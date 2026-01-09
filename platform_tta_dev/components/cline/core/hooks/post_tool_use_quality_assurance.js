// Logseq: [[TTA.dev/Platform_tta_dev/Components/Cline/Core/Hooks/Post_tool_use_quality_assurance]]
#!/usr/bin/env node
/**
 * TTA.dev Post-Tool Quality Assurance Hook
 * Provides warnings and auto-fixes for quality improvements
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const WORKSPACE_DIR = process.cwd();
const QUALITY_FIXES_LOG = path.join(WORKSPACE_DIR, '.tta', 'quality-fixes.log');

/**
 * Ensure log file exists
 */
function ensureLogFile() {
    const logDir = path.dirname(QUALITY_FIXES_LOG);
    if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
    }

    if (!fs.existsSync(QUALITY_FIXES_LOG)) {
        const header = `# TTA.dev Quality Assurance Log\n# Automatic fixes and improvements applied\n\n`;
        fs.writeFileSync(QUALITY_FIXES_LOG, header);
    }
}

/**
 * Log quality fixes
 */
function logQualityFix(fixType, description, fileAffected = '') {
    ensureLogFile();

    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${fixType}: ${description}`;
    const fullEntry = fileAffected ? `${logEntry} (${fileAffected})\n` : `${logEntry}\n`;

    fs.appendFileSync(QUALITY_FIXES_LOG, fullEntry);
}

/**
 * Check if UV environment is available for auto-fixes
 */
function canRunUVCommands() {
    try {
        execSync('which uv', { stdio: 'pipe' });
        execSync('uv --version', { stdio: 'pipe' });
        return true;
    } catch (error) {
        return false;
    }
}

/**
 * Auto-fix code formatting issues
 */
function autoFixFormatting(filePath) {
    if (!canRunUVCommands() || !fs.existsSync(path.join(WORKSPACE_DIR, '.venv'))) {
        return;
    }

    const fileExt = path.extname(filePath).toLowerCase();

    try {
        if (fileExt === '.py') {
            // Check if Black can be autofixed
            execSync(`cd "${WORKSPACE_DIR}" && uv run black --check --quiet "${filePath}"`, { stdio: 'pipe' });
        } else if (fileExt === '.ts' || fileExt === '.js') {
            // Check if there are linting issues (placeholder - would need specific tools)
            // Could integrate prettier, eslint, etc.
        }

        console.warn('⚠ TTA.dev Quality: Code formatting could be improved');
        console.warn('   Run: uv run black <file> or uv run isort <file> to auto-format');
    } catch (error) {
        // If formatting issues found, suggest auto-fix
        if (fileExt === '.py') {
            try {
                execSync(`cd "${WORKSPACE_DIR}" && uv run black "${filePath}"`, { stdio: 'pipe' });
                console.log('✓ Auto-fixed Python formatting with Black');
                logQualityFix('formatting', 'Auto-fixed Python code formatting', filePath);
            } catch (fixError) {
                console.warn('⚠ TTA.dev Quality: Could not auto-fix formatting, run manually: uv run black <file>');
            }
        }
    }
}

/**
 * Check for type hints in Python code
 */
function checkTypeHints(content) {
    if (!content.includes('def ') && !content.includes('class ')) {
        return; // Not a Python file with functions/classes
    }

    const lines = content.split('\n');
    const issues = [];

    // Check for modern type hints
    const permittedPatterns = [
        /\bdef\s+\w+.*->\s*[\w\[\]\|]/,  // Return type hints
        /\w+:\s*[\w\[\]\|\s"=]/,         // Parameter/attribute type hints
    ];

    // Check for legacy patterns that should be avoided
    const legacyPatterns = [
        /\bList\[/,
        /\bDict\[/,
        /\bSet\[/,
        /\bTuple\[/,
        /\bOptional\[/,
        /\bUnion\[/,
        /\bimport typing\b/,
        /\bfrom typing import\b/
    ];

    const hasLegacyImports = legacyPatterns.some(pattern => pattern.test(content));

    if (hasLegacyImports) {
        console.warn('⚠ TTA.dev Quality: Modern type hints required');
        console.warn('   Replace: List[T], Dict[K,V] → list[T], dict[K,V]');
        console.warn('   Replace: Optional[T] → T | None');
        console.warn('   Replace: Union[A,B] → A | B');
        console.warn('   Replace: import typing → use builtin types');

        // Try auto-fix common imports
        if (content.includes('import typing') && !content.includes('from typing import')) {
            const fixedContent = content
                .replace(/\bimport typing\b/g, '')
                .replace(/\btyping\.(\w+)\b/g, '$1');
            return fixedContent;
        }
    }

    return content;
}

/**
 * Auto-fix common code quality issues
 */
function autoFixCodeQuality(toolOutput, filePath) {
    if (!filePath || !fs.existsSync(filePath)) {
        return;
    }

    const originalContent = fs.readFileSync(filePath, 'utf8');
    let fixedContent = originalContent;

    const fileExt = path.extname(filePath).toLowerCase();

    if (fileExt === '.py') {
        // Check and fix type hints
        const checkedContent = checkTypeHints(fixedContent);
        if (checkedContent !== fixedContent) {
            fixedContent = checkedContent;
            console.log('✓ Auto-fixed type hint imports');
            logQualityFix('type-hints', 'Replaced legacy typing imports with modern syntax', filePath);
        }

        // Check for other common issues
        if (fixedContent.includes('print(') && !filePath.includes('test')) {
            console.warn('⚠ TTA.dev Quality: Print statements should use logging');
            console.warn('   Replace: print(...) → logger.info(...) or remove for production');
        }
    } else if (fileExt === '.ts' || fileExt === '.js') {
        // TypeScript/JavaScript specific checks
        if (fixedContent.includes('console.log') && !filePath.includes('test')) {
            console.warn('⚠ TTA.dev Quality: Console statements should use proper logging');
        }
    }

    // Apply fixes if content changed
    if (fixedContent !== originalContent) {
        try {
            fs.writeFileSync(filePath, fixedContent);
            console.log('✓ Auto-applied code quality improvements');
        } catch (error) {
            console.warn('⚠ TTA.dev Quality: Could not auto-apply fixes, manual intervention required');
        }
    }
}

/**
 * Check for security issues in dependencies
 */
function checkDependencySecurity() {
    if (!canRunUVCommands()) {
        return;
    }

    try {
        // Check for outdated dependencies
        const result = execSync('cd "' + WORKSPACE_DIR + '" && uv sync --dry-run --quiet', {
            encoding: 'utf8',
            stdio: 'pipe'
        });

        if (result.includes('Would upgrade') || result.includes('Would downgrade')) {
            console.warn('⚠ TTA.dev Quality: Dependencies may need updating');
            console.warn('   Run: uv sync to update dependencies');
        }
    } catch (error) {
        // Silent catch - not critical
    }
}

/**
 * Provide quality improvement suggestions
 */
function provideQualitySuggestions(toolResult) {
    const suggestions = [];

    // Check for common patterns that indicate quality concerns
    if (toolResult.includes('error') || toolResult.includes('Error')) {
        suggestions.push('Consider adding error handling and logging for better observability');
    }

    if (toolResult.includes('TODO') || toolResult.includes('FIXME')) {
        suggestions.push('TODO/FIXME comments found - consider addressing outstanding items');
    }

    if (toolResult.includes('print(') || toolResult.includes('console.log')) {
        suggestions.push('Replace debug prints with proper logging infrastructure');
    }

    if (toolResult.includes('hardcoded') || toolResult.includes('magic number')) {
        suggestions.push('Consider using named constants instead of magic numbers/strings');
    }

    // Output suggestions
    if (suggestions.length > 0) {
        console.log('\n🌟 TTA.dev Quality Suggestions:');
        suggestions.forEach(suggestion => {
            console.log(`   • ${suggestion}`);
        });
        console.log('');
    }
}

/**
 * Generate quality summary
 */
function generateQualitySummary() {
    const recentLogLines = [];

    if (fs.existsSync(QUALITY_FIXES_LOG)) {
        const logContent = fs.readFileSync(QUALITY_FIXES_LOG, 'utf8');
        const lines = logContent.split('\n').filter(line => line.trim());
        recentLogLines.push(...lines.slice(-5)); // Last 5 entries
    }

    if (recentLogLines.length > 0) {
        console.log('\n📊 Recent Quality Improvements:');
        recentLogLines.forEach(line => {
            if (line && !line.startsWith('#')) {
                console.log(`   ${line}`);
            }
        });
        console.log('');
    }
}

/**
 * Main hook logic
 */
function main() {
    const input = JSON.parse(process.argv[2] || '{}');

    // Get context from input
    const toolName = input.tool || '';
    const toolResult = input.result || '';
    const affectedFiles = input.files || [];

    console.log('\n--- TTA.dev Quality Assurance ---\n');

    // Run quality checks
    checkDependencySecurity();

    // Check and auto-fix files
    affectedFiles.forEach(filePath => {
        autoFixFormatting(filePath);
        autoFixCodeQuality(toolResult, filePath);
    });

    // Provide suggestions based on tool results
    provideQualitySuggestions(toolResult);

    // Show recent quality improvements
    generateQualitySummary();

    console.log('--- Quality Check Complete ---\n');

    process.exit(0);
}

if (require.main === module) {
    main();
}

module.exports = {
    main,
    autoFixFormatting,
    checkTypeHints,
    autoFixCodeQuality,
    provideQualitySuggestions
};
