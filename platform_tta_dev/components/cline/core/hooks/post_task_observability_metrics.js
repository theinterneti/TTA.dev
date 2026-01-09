// Logseq: [[TTA.dev/Platform_tta_dev/Components/Cline/Core/Hooks/Post_task_observability_metrics]]
#!/usr/bin/env node
/**
 * TTA.dev Post-Task Observability Hook
 * Collects metrics about persona performance and task outcomes
 */

const fs = require('fs');
const path = require('path');

const WORKSPACE_DIR = process.cwd();
const METRICS_DIR = path.join(WORKSPACE_DIR, '.tta', 'metrics');
const METRICS_FILE = path.join(METRICS_DIR, 'persona-metrics.json');

/**
 * Ensure metrics directory and file exist
 */
function ensureMetricsFile() {
    if (!fs.existsSync(METRICS_DIR)) {
        fs.mkdirSync(METRICS_DIR, { recursive: true });
    }

    if (!fs.existsSync(METRICS_FILE)) {
        const initialMetrics = {
            _description: "TTA.dev Persona Performance Metrics",
            _version: "1.0.0",
            _created: new Date().toISOString(),
            personas: {
                DevOpsGuardian: {
                    totalTasks: 0,
                    successfulTasks: 0,
                    failedTasks: 0,
                    averageResponseTime: 0,
                    totalResponseTime: 0,
                    completedTasks: 0,
                    tasksByCategory: {},
                    performanceRating: 0,
                    qualityMetrics: {
                        securityIncidents: 0,
                        deploymentSuccess: 0,
                        rollbackCount: 0
                    }
                },
                QualityGuardian: {
                    totalTasks: 0,
                    successfulTasks: 0,
                    failedTasks: 0,
                    averageResponseTime: 0,
                    totalResponseTime: 0,
                    completedTasks: 0,
                    tasksByCategory: {},
                    performanceRating: 0,
                    qualityMetrics: {
                        testCoverage: [],
                        securityFindings: 0,
                        lintErrorsPrevented: 0
                    }
                },
                PrimitiveArchitect: {
                    totalTasks: 0,
                    successfulTasks: 0,
                    failedTasks: 0,
                    averageResponseTime: 0,
                    totalResponseTime: 0,
                    completedTasks: 0,
                    tasksByCategory: {},
                    performanceRating: 0,
                    qualityMetrics: {
                        architecturalImprovements: 0,
                        primitiveImplementations: 0,
                        performanceOptimizations: 0
                    }
                }
            },
            summary: {
                totalTasks: 0,
                averageSuccessRate: 0,
                overallPerformanceRating: 0,
                mostEffectivePersona: null,
                tasksByHour: {},
                tasksByDay: {},
                errorPatterns: {}
            }
        };
        fs.writeFileSync(METRICS_FILE, JSON.stringify(initialMetrics, null, 2));
    }
}

/**
 * Load current metrics
 */
function loadMetrics() {
    try {
        ensureMetricsFile();
        return JSON.parse(fs.readFileSync(METRICS_FILE, 'utf8'));
    } catch (error) {
        console.warn('Warning: Could not load metrics file:', error.message);
        return null;
    }
}

/**
 * Save metrics to file
 */
function saveMetrics(metrics) {
    try {
        fs.writeFileSync(METRICS_FILE, JSON.stringify(metrics, null, 2));
    } catch (error) {
        console.error('Error: Could not save metrics file:', error.message);
    }
}

/**
 * Detect task category from task context
 */
function detectTaskCategory(taskContext = '') {
    const context = taskContext.toLowerCase();

    if (context.includes('deploy') || context.includes('infrastructure') || context.includes('docker')) {
        return 'deployment';
    }
    if (context.includes('test') || context.includes('quality') || context.includes('security')) {
        return 'testing';
    }
    if (context.includes('component') || context.includes('architecture') || context.includes('database')) {
        return 'architecture';
    }
    if (context.includes('bug') || context.includes('fix') || context.includes('error')) {
        return 'bug-fix';
    }
    if (context.includes('feature') || context.includes('implement')) {
        return 'feature-development';
    }
    if (context.includes('performance') || context.includes('optimize')) {
        return 'performance';
    }
    if (context.includes('documentation') || context.includes('readme') || context.includes('doc')) {
        return 'documentation';
    }
    if (context.includes('config') || context.includes('setup') || context.includes('install')) {
        return 'configuration';
    }

    return 'general';
}

/**
 * Calculate performance rating based on various factors
 */
function calculatePerformanceRating(personaMetrics, taskOutcome, responseTime) {
    let rating = 0;

    // Base success rate (40% weight)
    const successRate = personaMetrics.completedTasks > 0
        ? personaMetrics.successfulTasks / personaMetrics.completedTasks
        : 0;
    rating += successRate * 40;

    // Response time efficiency (30% weight)
    // Faster is better, but expect some variance
    const avgResponseTime = personaMetrics.averageResponseTime;
    let timeEfficiency = 1.0;
    if (responseTime > avgResponseTime * 1.5) {
        timeEfficiency = 0.7; // Penalty for much slower than average
    } else if (responseTime < avgResponseTime * 0.8) {
        timeEfficiency = 1.2; // Bonus for faster than average
    }
    rating += timeEfficiency * 30;

    // Task diversity and coverage (20% weight)
    const categoryCount = Object.keys(personaMetrics.tasksByCategory).length;
    let diversityBonus = Math.min(categoryCount / 5, 1.0); // Max bonus at 5+ categories
    rating += diversityBonus * 20;

    // Quality-specific metrics (10% weight)
    let qualityBonus = 0;
    const quality = personaMetrics.qualityMetrics;

    if (personaMetrics.persona === 'DevOpsGuardian') {
        qualityBonus = (quality.deploymentSuccess || 0) > 0 ? 1.0 : 0.5;
    } else if (personaMetrics.persona === 'QualityGuardian') {
        const avgCoverage = quality.testCoverage && quality.testCoverage.length > 0
            ? quality.testCoverage.reduce((a, b) => a + b, 0) / quality.testCoverage.length
            : 0;
        qualityBonus = Math.min(avgCoverage / 100, 1.0);
    } else if (personaMetrics.persona === 'PrimitiveArchitect') {
        qualityBonus = (quality.architecturalImprovements || 0) > 0 ? 1.0 : 0.8;
    }

    rating += qualityBonus * 10;

    return Math.min(100, Math.max(0, rating));
}

/**
 * Log metrics to external monitoring system
 */
function logToMonitoringSystem(metrics, taskLog) {
    // TODO: Integrate with Prometheus, Grafana, or other monitoring systems
    // For now, just log to console for demonstration

    const timestamp = new Date().toISOString();
    console.log('=== TTA.dev Metrics Update ===');
    console.log(`${timestamp} - Persona: ${taskLog.persona}`);
    console.log(`Task: ${taskLog.category} - ${taskLog.outcome}`);
    console.log(`Response Time: ${taskLog.responseTime}s`);
    console.log(`Performance Rating: ${taskLog.performanceRating}/100`);
    console.log('');

    // Could send to external systems here:
    // - Prometheus metrics endpoint
    // - Grafana annotations
    // - Elasticsearch for analysis
    // - Custom dashboard APIs
}

/**
 * Main hook logic
 */
function main() {
    const input = JSON.parse(process.argv[2] || '{}');

    // Get task context from environment variables set by pre-task hook
    const activePersona = process.env.TTA_DEV_ACTIVE_PERSONA;
    const expectedResponseTime = parseInt(process.env.TTA_DEV_PERSONA_RESPONSE_TIME || '0');

    if (!activePersona) {
        console.log('Warning: No active persona detected, skipping metrics collection');
        process.exit(0);
    }

    // Extract task information
    const taskContext = [
        input.task || '',
        input.description || '',
        input.prompt || '',
        input.message || ''
    ].join(' ').trim();

    const taskCategory = detectTaskCategory(taskContext);
    const taskOutcome = input.success ? 'success' : (input.error ? 'error' : 'completed');
    const responseTime = input.duration || expectedResponseTime;

    // Load current metrics
    const metrics = loadMetrics();
    if (!metrics) {
        console.error('Error: Could not load metrics, skipping collection');
        process.exit(1);
    }

    // Update persona-specific metrics
    const personaMetrics = metrics.personas[activePersona];
    if (personaMetrics) {
        personaMetrics.totalTasks += 1;

        if (taskOutcome === 'success') {
            personaMetrics.successfulTasks += 1;
        } else if (taskOutcome === 'error') {
            personaMetrics.failedTasks += 1;
        } else {
            personaMetrics.completedTasks += 1;
        }

        // Update response time
        personaMetrics.totalResponseTime += responseTime;
        personaMetrics.averageResponseTime = personaMetrics.totalResponseTime / personaMetrics.totalTasks;

        // Update task categories
        const categoryCounts = personaMetrics.tasksByCategory[taskCategory] || 0;
        personaMetrics.tasksByCategory[taskCategory] = categoryCounts + 1;

        // Update performance rating
        personaMetrics.performanceRating = calculatePerformanceRating(personaMetrics, taskOutcome, responseTime);

        // Update quality-specific metrics
        if (activePersona === 'DevOpsGuardian' && taskOutcome === 'success') {
            if (taskCategory === 'deployment') {
                personaMetrics.qualityMetrics.deploymentSuccess += 1;
            }
        } else if (activePersona === 'QualityGuardian') {
            if (taskCategory === 'testing' && taskOutcome === 'success') {
                // Could parse coverage from output
                personaMetrics.qualityMetrics.testCoverage.push(85); // Placeholder
                personaMetrics.qualityMetrics.lintErrorsPrevented += Math.floor(Math.random() * 3); // Placeholder
            }
        } else if (activePersona === 'PrimitiveArchitect' && taskOutcome === 'success') {
            if (taskCategory === 'architecture' || taskCategory === 'performance') {
                personaMetrics.qualityMetrics.architecturalImprovements += 1;
                personaMetrics.qualityMetrics.primitiveImplementations += 1;
            }
        }
    }

    // Update summary metrics
    metrics.summary.totalTasks += 1;
    const totalTasks = Object.values(metrics.personas).reduce((acc, p) => acc + p.totalTasks, 0);
    const totalSuccessful = Object.values(metrics.personas).reduce((acc, p) => acc + p.successfulTasks, 0);
    metrics.summary.averageSuccessRate = totalSuccessful / totalTasks;

    // Determine most effective persona
    const personaRatings = Object.entries(metrics.personas).map(([name, p]) => ({
        name,
        rating: p.performanceRating
    }));
    metrics.summary.overallPerformanceRating = personaRatings.reduce((acc, p) => acc + p.rating, 0) / personaRatings.length;
    metrics.summary.mostEffectivePersona = personaRatings.reduce((a, b) =>
        a.rating > b.rating ? a : b
    ).name;

    // Update time-based metrics
    const now = new Date();
    const hour = now.getHours().toString().padStart(2, '0');
    const day = now.toISOString().split('T')[0];

    metrics.summary.tasksByHour[hour] = (metrics.summary.tasksByHour[hour] || 0) + 1;
    metrics.summary.tasksByDay[day] = (metrics.summary.tasksByDay[day] || 0) + 1;

    // Save updated metrics
    saveMetrics(metrics);

    // Log for monitoring
    const taskLog = {
        persona: activePersona,
        category: taskCategory,
        outcome: taskOutcome,
        responseTime: responseTime,
        performanceRating: personaMetrics?.performanceRating || 0,
        timestamp: new Date().toISOString(),
        taskPreview: taskContext.substring(0, 100)
    };

    logToMonitoringSystem(metrics, taskLog);

    process.exit(0);
}

if (require.main === module) {
    main();
}

module.exports = {
    main,
    detectTaskCategory,
    calculatePerformanceRating,
    loadMetrics,
    saveMetrics
};
