# Cline Memory Bank Setup Workflow

This workflow will guide you through the process of setting up a Cline Memory Bank for your project. It will read your existing `.clinerules` and `AGENTS.md` files to create a rich, project-specific knowledge base for Cline.

## Step 1: Create the Memory Bank Directory

I will start by creating a `memory-bank` directory in your project root. This is where all the Memory Bank files will be stored.

<execute_command>
<command>mkdir memory-bank</command>
<requires_approval>true</requires_approval>
</execute_command>

## Step 2: Create the Project Brief

I will now create the `projectbrief.md` file. This is the foundational document for your Memory Bank. I will populate it with a summary of your project based on the information in your `.clinerules` and `AGENTS.md` files.

<write_to_file>
<path>memory-bank/projectbrief.md</path>
<content>
# Project Brief: TTA.dev

This project, TTA.dev, is a production-ready AI development toolkit. It provides agentic primitives for building reliable AI workflows, composable patterns with type-safe operators, and built-in observability with OpenTelemetry integration. It is a multi-package monorepo with a focus on focused, reusable components.
