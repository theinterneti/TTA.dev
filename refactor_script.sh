#!/bin/bash

# This script refactors the Serena documentation to improve its structure and clarity.

# Create the necessary directories
mkdir -p framework/docs/mcp-references/integrations
mkdir -p serena/docs/getting-started
mkdir -p serena/docs/core-concepts
mkdir -p serena/docs/integrations
mkdir -p serena/docs/advanced-topics

# Move the existing documentation to the new structure
mv framework/docs/mcp-references/serena.md serena/docs/getting-started/installation.md
mv framework/docs/mcp-references/integrations/serena-integration.md serena/docs/integrations/mcp-clients.md

# Create new files with the refactored content
cat > serena/docs/getting-started/quickstart.md << EOL
# Quickstart

This guide will walk you through the process of setting up your first project with Serena.
EOL

cat > serena/docs/core-concepts/projects.md << EOL
# Projects

Serena uses a project-based workflow to help you stay organized and efficient.
EOL

cat > serena/docs/core-concepts/tools.md << EOL
# Tools

Serena provides a powerful set of tools for symbolic operations, code analysis, and more.
EOL

cat > serena/docs/core-concepts/configuration.md << EOL
# Configuration

Learn how to customize Serena to fit your specific needs.
EOL

cat > serena/docs/integrations/custom-agents.md << EOL
# Custom Agents

Learn how to integrate Serena with your own custom agent frameworks.
EOL

cat > serena/docs/advanced-topics/security.md << EOL
# Security

Important security recommendations for using Serena safely and responsibly.
EOL

cat > serena/docs/advanced-topics/prompting-strategies.md << EOL
# Prompting Strategies

Tips and best practices for getting the most out of Serena.
EOL

cat > serena/docs/contributing.md << EOL
# Contributing

We welcome contributions from the community.
EOL

echo "Documentation refactoring complete."
