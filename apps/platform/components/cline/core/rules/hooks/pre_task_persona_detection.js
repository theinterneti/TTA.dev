// Logseq: [[TTA.dev/Platform_tta_dev/Components/Cline/Core/Rules/Hooks/Pre_task_persona_detection]]
#!/usr/bin/env node
/**
 * TTA.dev Persona Detection Hook
 * Automatically detects and activates appropriate persona based on task context
 */

const fs = require('fs');
const path = require('path');

const WORKSPACE_DIR = process.cwd();
const PERSONA_OVERRIDES_FILE = path.join(WORKSPACE_DIR, '.tta', 'persona-overrides.json');

/**
 * Persona definitions with keywords and capabilities
 */
const PERSONAS = {
    DevOpsGuardian: {
        name: 'DevOpsGuardian',
        description: 'Handles CI/CD, deployment, infrastructure, and operational tasks',
        keywords: [
            'deploy', 'ci/cd', 'pipeline', 'docker', 'kubernetes', 'aws', 'gcp', 'azure',
            'jenkins', 'github actions', 'gitlab ci', 'bitbucket', 'circleci', 'travis',
            'terraform', 'ansible', 'puppet', 'chef', 'prometheus', 'grafana',
            'monitoring', 'logging', 'nginx', 'apache', 'security groups', 'firewall',
            'scaling', 'load balancer', 'cdn', 'ssl', 'certificate', 'domain',
            'server', 'infrastructure', 'cloud', 'hosting', 'git', 'github', 'gitlab',
            'bitbucket', 'repository', 'branch', 'merge', 'pr', 'pull request',
            'code review', 'release', 'tag', 'versioning', 'changelog'
        ],
        mcpServers: ['github', 'docker', 'kubernetes'],
        promptPrefix: 'You are DevOpsGuardian - the expert in all things infrastructure, deployment, and DevOps. You ensure reliable, scalable, and secure systems.',
        successRate: 0.85,
        averageResponseTime: 120
    },

    QualityGuardian: {
        name: 'QualityGuardian',
        description: 'Handles testing, code quality, security scanning, and validation',
        keywords: [
            'test', 'testing', 'pytest', 'jest', 'jasmine', 'mocha', 'vitest',
            'cypress', 'playwright', 'selenium', 'unit test', 'integration test',
            'e2e', 'end-to-end', 'tdd', 'bdd', 'qa', 'quality assurance',
            'lint', 'linter', 'ruff', 'eslint', 'black', 'isort', 'mypy',
            'bandit', 'security', 'vulnerability', 'scan', 'audit', 'coverage',
            'benchmark', 'performance', 'mutation testing', 'cosmic-ray',
            'semgrep', 'eslint', 'pre-commit', 'husky', 'validate', 'verify',
            'check', 'report', 'analysis', 'metric', 'dashboard'
        ],
        mcpServers: ['jest', 'playwright', 'bandit', 'semgrep', 'mutate'],
        promptPrefix: 'You are QualityGuardian - the champion of code quality, testing excellence, and security. You ensure bulletproof, efficient, and reliable code.',
        successRate: 0.92,
        averageResponseTime: 95
    },

    PrimitiveArchitect: {
        name: 'PrimitiveArchitect',
        description: 'Handles primitive functions, architecture design, and component construction',
        keywords: [
            'primitive', 'function', 'component', 'architecture', 'design pattern',
            'async', 'await', 'coroutine', 'context manager', '__init__', 'property',
            'decorator', 'descriptor', 'metaclass', 'generator', 'iterator',
            'protocol', 'abstract base class', 'trait', 'mixin', 'composition',
            'inheritance', 'polymorphism', 'encapsulation', 'abstraction',
            'solid', 'dry', 'kiss', 'yagni', 'refactor', 'optimize', 'performance',
            'caching', 'memory', 'cpu', 'latency', 'throughput', 'scaling',
            'database', 'neo4j', 'mongodb', 'postgresql', 'redis', 'narrative',
            'storytelling', 'player', 'character', 'world', 'therapeutic'
        ],
        mcpServers: ['neo4j', 'mongodb', 'redis', 'narrative-engine'],
        promptPrefix: 'You are PrimitiveArchitect - the master builder of clean, efficient primitives and architectural foundations. You create robust, extensible systems.',
        successRate: 0.88,
        averageResponseTime: 85
    }
};

/**
 * Check for manual persona override
 */
function checkPersonaOverride(taskContext = '') {
    try {
        if (fs.existsSync(PERSONA_OVERRIDES_FILE)) {
            const overrides = JSON.parse(fs.readFileSync(PERSONA_OVERRIDES_FILE, 'utf8'));

            // Check for exact task match
            if (overrides.tasks && taskContext) {
                for (const [taskPattern, persona] of Object.entries(overrides.tasks)) {
                    if (taskContext.toLowerCase().includes(taskPattern.toLowerCase())) {
                        return persona;
                    }
                }
            }

            // Check for global override
            if (overrides.global) {
                return overrides.global;
            }
        }
    } catch (error) {
        // If override file is malformed, continue with detection
        console.warn('Warning: Malformed persona override file, ignoring:', error.message);
    }

    return null;
}

/**
 * Analyze task context to detect appropriate persona
 */
function detectPersona(taskContext = '') {
    if (!taskContext) {
        // Default to QualityGuardian for general tasks
        return PERSONAS.QualityGuardian;
    }

    const context = taskContext.toLowerCase();
    const scores = {};

    // Calculate relevance scores for each persona
    Object.values(PERSONAS).forEach(persona => {
        let score = 0;

        persona.keywords.forEach(keyword => {
            const count = (context.match(new RegExp(keyword, 'gi')) || []).length;
            score += count;
        });

        // Apply weights for different contexts
        if (context.includes('deploy') || context.includes('production') || context.includes('infrastructure')) {
            if (persona.name === 'DevOpsGuardian') score *= 2;
        }

        if (context.includes('test') || context.includes('quality') || context.includes('security')) {
            if (persona.name === 'QualityGuardian') score *= 2;
        }

        if (context.includes('primitive') || context.includes('architecture') || context.includes('component')) {
            if (persona.name === 'PrimitiveArchitect') score *= 2;
        }

        scores[persona.name] = score;
    });

    // Find persona with highest score
    const bestMatch = Object.entries(scores).reduce((a, b) =>
        scores[a[0]] > scores[b[0]] ? a : b
    )[0];

    const bestScore = scores[bestMatch];

    // If no keywords matched, default to QualityGuardian
    if (bestScore === 0) {
        return PERSONAS.QualityGuardian;
    }

    return PERSONAS[bestMatch];
}

/**
 * Log persona activation with metrics
 */
function logPersonaActivation(persona, source, taskContext = '') {
    const logEntry = {
        timestamp: new Date().toISOString(),
        persona: persona.name,
        source: source, // 'override', 'detected', 'default'
        confidence: persona.successRate,
        taskPreview: taskContext.substring(0, 100) + (taskContext.length > 100 ? '...' : ''),
        metrics: {
            expectedSuccessRate: persona.successRate,
            averageResponseTimeSeconds: persona.averageResponseTime
        }
    };

    console.log('=== TTA.dev Persona Activated ===');
    console.log(`⊹ ${persona.name} - ${persona.description}`);
    console.log(`Source: ${source}`);
    console.log(`Success Rate: ${(persona.successRate * 100).toFixed(1)}%`);
    console.log(`Avg Response: ${persona.averageResponseTime}s`);
    console.log(`MCP Servers: ${persona.mcpServers.join(', ')}`);
    console.log('');

    // TODO: Log to observability system
    // This could integrate with Prometheus, Grafana, or a custom metrics system
}

/**
 * Main hook logic
 */
function main() {
    const input = JSON.parse(process.argv[2] || '{}');

    // Extract task context from input
    const taskContext = [
        input.task || '',
        input.description || '',
        input.prompt || '',
        input.message || ''
    ].join(' ').trim();

    // Check for manual override first
    let overridePersona = checkPersonaOverride(taskContext);

    let persona;
    let source;

    if (overridePersona && PERSONAS[overridePersona]) {
        // Valid override found
        persona = PERSONAS[overridePersona];
        source = 'override';
    } else {
        // Auto-detect if no valid override
        persona = detectPersona(taskContext);
        source = overridePersona ? 'detected (override invalid)' : 'detected';

        if (overridePersona && !PERSONAS[overridePersona]) {
            console.warn(`Warning: Unknown persona "${overridePersona}" in override file, using auto-detection`);
        }
    }

    // Log activation
    logPersonaActivation(persona, source, taskContext);

    // Set environment variables for persona context
    process.env.TTA_DEV_ACTIVE_PERSONA = persona.name;
    process.env.TTA_DEV_PERSONA_SUCCESS_RATE = persona.successRate.toString();
    process.env.TTA_DEV_PERSONA_RESPONSE_TIME = persona.averageResponseTime.toString();
    process.env.TTA_DEV_PERSONA_MCP_SERVERS = persona.mcpServers.join(',');

    // Set persona-specific prompt
    process.env.TTA_DEV_PERSONA_PROMPT_PREFIX = persona.promptPrefix;

    // Exit successfully to allow task to continue
    process.exit(0);
}

if (require.main === module) {
    main();
}

module.exports = { main, detectPersona, checkPersonaOverride, PERSONAS };
