// Logseq: [[TTA.dev/Platform_tta_dev/Components/Cline/Core/Rules/Hooks/Pre_tool_use_enforce_tta_standards]]
#!/usr/bin/env node
/**
 * TTA.dev Standards Enforcement Hook
 * Blocks tools if UV environment or TTA standards are not met
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const WORKSPACE_DIR = process.cwd();
const BLOCK_EXIT_CODE = 1;
const ALLOW_EXIT_CODE = 0;

/**
 * Check if UV is properly configured and installed
 */
function checkUVConfiguration() {
    const errors = [];

    try {
        // Check if UV is installed
        execSync('which uv', { stdio: 'pipe' });
    } catch (error) {
        errors.push('UV package manager not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh');
        return errors;
    }

    try {
        // Check UV config files
        const uvTomlPath = path.join(WORKSPACE_DIR, 'uv.toml');
        if (!fs.existsSync(uvTomlPath)) {
            errors.push('uv.toml not found in project root');
        }

        // Check for UV managed mode in pyproject.toml
        const pyprojectPath = path.join(WORKSPACE_DIR, 'pyproject.toml');
        if (fs.existsSync(pyprojectPath)) {
            const content = fs.readFileSync(pyprojectPath, 'utf8');
            if (!content.includes('[tool.uv]')) {
                errors.push('pyproject.toml missing [tool.uv] section');
            }
            if (!content.includes('managed = true')) {
                errors.push('UV managed mode not enabled (missing "managed = true" in [tool.uv])');
            }
        } else {
            errors.push('pyproject.toml not found');
        }

        // Check .venv directory
        const venvPath = path.join(WORKSPACE_DIR, '.venv');
        if (!fs.existsSync(venvPath)) {
            errors.push('.venv directory not found. Run: uv venv');
        } else {
            const pythonPath = path.join(venvPath, 'bin', 'python');
            if (!fs.existsSync(pythonPath)) {
                errors.push('Python interpreter not found in .venv');
            }
        }

        // Check uv.lock
        const lockPath = path.join(WORKSPACE_DIR, 'uv.lock');
        if (!fs.existsSync(lockPath)) {
            errors.push('uv.lock not found. Run: uv lock');
        }

    } catch (error) {
        errors.push(`UV configuration check failed: ${error.message}`);
    }

    return errors;
}

/**
 * Check for forbidden 'list' directory
 */
function checkListDirectory() {
    const listPath = path.join(WORKSPACE_DIR, 'list');
    if (fs.existsSync(listPath)) {
        return ['Forbidden "list" directory exists - should not exist. Run: rm -rf list'];
    }
    return [];
}

/**
 * Check for modern Python features usage
 */
function checkPrimitivesUsage(toolInput) {
    const errors = [];

    // Check for forbidden patterns in tool arguments
    const forbidden = [
        'import typing', // Should use modern typing syntax
        'from typing import', // Should use modern typing syntax
        'List[', // Should use list[...]
        'Dict[', // Should use dict[...]
        'Set[', // Should use set[...]
        'Tuple[', // Should use tuple[...]
        'Optional[', // Should use | None
        'Union[', // Should use |
    ];

    const inputStr = JSON.stringify(toolInput);
    forbidden.forEach(pattern => {
        if (inputStr.includes(pattern)) {
            errors.push(`TTA.dev standard violation: Use modern type hints. Replace "${pattern}" with modern syntax (list[...], dict[...], | None, etc.)`);
        }
    });

    return errors;
}

/**
 * Main hook logic
 */
function main() {
    const input = JSON.parse(process.argv[2] || '{}');
    const allErrors = [];

    // Run all checks
    allErrors.push(...checkUVConfiguration());
    allErrors.push(...checkListDirectory());
    allErrors.push(...checkPrimitivesUsage(input));

    if (allErrors.length > 0) {
        console.error('=== TTA.dev Standards Enforcement Blocked ===');

        // Only show first few errors to avoid wall of text
        const maxErrors = 5;
        allErrors.slice(0, maxErrors).forEach(error => {
            console.error(`✗ ${error}`);
        });

        if (allErrors.length > maxErrors) {
            console.error(`... and ${allErrors.length - maxErrors} more errors`);
        }

        console.error('\nFix these issues before continuing. Run verify-uv-configuration.sh for detailed UV setup.');
        process.exit(BLOCK_EXIT_CODE);
    }

    // All checks passed
    console.log('✓ TTA.dev standards compliance check passed');
    process.exit(ALLOW_EXIT_CODE);
}

if (require.main === module) {
    main();
}

module.exports = { main, checkUVConfiguration, checkListDirectory, checkPrimitivesUsage };
