# Copilot Auto-Reviewer Flow Diagram

## Overview

This document visualizes how the automatic Copilot reviewer assignment works in the TTA.dev repository.

## Dual Approach Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Creates Pull Request                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   GitHub PR Creation Event    │
              └───────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────────┐   ┌──────────────────────────┐
    │  CODEOWNERS Method    │   │  GitHub Actions Method   │
    │     (Primary)         │   │      (Fallback)          │
    └───────────────────────┘   └──────────────────────────┘
                │                           │
                ▼                           ▼
    ┌───────────────────────┐   ┌──────────────────────────┐
    │ GitHub reads          │   │ Workflow triggers on     │
    │ .github/CODEOWNERS    │   │ pull_request.opened      │
    └───────────────────────┘   └──────────────────────────┘
                │                           │
                ▼                           ▼
    ┌───────────────────────┐   ┌──────────────────────────┐
    │ Finds: * @Copilot     │   │ Uses github-script@v7    │
    └───────────────────────┘   └──────────────────────────┘
                │                           │
                ▼                           ▼
    ┌───────────────────────┐   ┌──────────────────────────┐
    │ Auto-requests review  │   │ Checks if already        │
    │ from @Copilot         │   │ assigned                 │
    └───────────────────────┘   └──────────────────────────┘
                │                           │
                │                           ▼
                │               ┌──────────────────────────┐
                │               │ If not assigned:         │
                │               │ Request review via API   │
                │               └──────────────────────────┘
                │                           │
                └─────────────┬─────────────┘
                              ▼
              ┌───────────────────────────────┐
              │  Copilot Added as Reviewer    │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Copilot Reviews Pull Request │
              └───────────────────────────────┘
```

## Detailed Workflow Steps

### CODEOWNERS Method (Primary)

```
Step 1: Developer creates PR
   ↓
Step 2: GitHub detects new PR
   ↓
Step 3: GitHub reads .github/CODEOWNERS
   ↓
Step 4: GitHub finds: * @Copilot
   ↓
Step 5: GitHub automatically requests review from @Copilot
   ↓
Step 6: Copilot appears in "Reviewers" section
   ↓
Step 7: Copilot reviews the PR
```

**Timeline:** Immediate (< 5 seconds)

### GitHub Actions Method (Fallback)

```
Step 1: Developer creates PR
   ↓
Step 2: GitHub triggers pull_request.opened event
   ↓
Step 3: Workflow "Auto-assign Copilot Reviewer" starts
   ↓
Step 4: Workflow extracts PR number, owner, repo
   ↓
Step 5: Workflow calls GitHub API to list current reviewers
   ↓
Step 6: Workflow checks if Copilot is already assigned
   ↓
Step 7a: If already assigned → Log and exit
   ↓
Step 7b: If not assigned → Request Copilot as reviewer via API
   ↓
Step 8: Copilot appears in "Reviewers" section
   ↓
Step 9: Copilot reviews the PR
```

**Timeline:** 10-30 seconds (workflow execution time)

## Error Handling Flow

```
┌─────────────────────────────────────────┐
│  Workflow Attempts to Assign Copilot    │
└─────────────────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │  API Call Made  │
        └─────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   ┌─────────┐         ┌─────────┐
   │ Success │         │  Error  │
   └─────────┘         └─────────┘
        │                   │
        ▼                   ▼
   ┌─────────┐         ┌─────────────────────┐
   │   Log   │         │ Log error message   │
   │ Success │         │ (non-blocking)      │
   └─────────┘         └─────────────────────┘
        │                   │
        │                   ▼
        │         ┌─────────────────────────┐
        │         │ Check error type:       │
        │         │ - Not a collaborator?   │
        │         │ - Permission denied?    │
        │         │ - Other?                │
        │         └─────────────────────────┘
        │                   │
        │                   ▼
        │         ┌─────────────────────────┐
        │         │ Provide helpful hint    │
        │         │ in logs                 │
        │         └─────────────────────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
        ┌─────────────────┐
        │ Workflow Exits  │
        │ (Always Success)│
        └─────────────────┘
```

**Key Point:** Workflow never fails - errors are logged but don't block PR creation

## Integration Points

### With Existing Workflows

```
┌──────────────────────────────────────────────────────────┐
│                    Pull Request Created                   │
└──────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ CODEOWNERS   │  │ Auto-assign  │  │ Existing     │
│ Assignment   │  │ Copilot      │  │ Workflows    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        │                 │         ┌───────┴───────┐
        │                 │         │               │
        │                 │         ▼               ▼
        │                 │  ┌──────────┐   ┌──────────┐
        │                 │  │   CI     │   │ Quality  │
        │                 │  │  Tests   │   │  Checks  │
        │                 │  └──────────┘   └──────────┘
        │                 │         │               │
        └─────────────────┴─────────┴───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  All Workflows Run    │
              │  Independently        │
              └───────────────────────┘
```

**No Conflicts:** Each workflow runs independently with its own triggers and permissions

## Permissions Model

```
┌─────────────────────────────────────────────────────────┐
│              Auto-assign Copilot Workflow                │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ pull-requests:   │              │ contents: read   │
│ write            │              │                  │
└──────────────────┘              └──────────────────┘
        │                                   │
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ Can assign       │              │ Can read repo    │
│ reviewers        │              │ content          │
└──────────────────┘              └──────────────────┘
```

**Minimal Permissions:** Only what's needed for reviewer assignment

## Success Indicators

```
┌─────────────────────────────────────────────────────────┐
│                  Check PR Page                           │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Reviewers    │  │ Actions Tab  │  │ Workflow     │
│ Section      │  │              │  │ Logs         │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Shows        │  │ Green ✓      │  │ "Successfully│
│ @Copilot     │  │ Checkmark    │  │  assigned"   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Troubleshooting Decision Tree

```
                    Is Copilot assigned?
                           │
                ┌──────────┴──────────┐
                │                     │
               Yes                   No
                │                     │
                ▼                     ▼
         ┌──────────┐        Check CODEOWNERS
         │ Success! │        file location
         └──────────┘                │
                              ┌──────┴──────┐
                              │             │
                          Correct       Incorrect
                              │             │
                              ▼             ▼
                      Check workflow   Move to
                      logs             .github/
                              │             │
                      ┌───────┴───────┐     │
                      │               │     │
                  Success         Error     │
                      │               │     │
                      ▼               ▼     ▼
                  All good!    Check error  Retry
                               message
                                   │
                        ┌──────────┴──────────┐
                        │                     │
                "Not collaborator"      Other error
                        │                     │
                        ▼                     ▼
                Add Copilot as          Check GitHub
                collaborator            status/docs
```

---

**Visual Guide Complete!** 

Use this diagram to understand how the automatic Copilot reviewer assignment works and troubleshoot any issues.

