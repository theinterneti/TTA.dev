# Shared Package

## Purpose
This package contains **truly universal** utilities shared across all TTA.dev packages.

## Current State
**Minimal by design** - only contains code that is genuinely needed by multiple packages.

## Philosophy
- Keep this package small and focused
- Don't add code here "just in case"
- Only promote utilities after they're used in 2+ packages
- Consider if code belongs in a specific package instead

## Contents
- Common types and interfaces
- Universal constants
- Cross-cutting utilities

## When to Add Here
✅ Used by 3+ packages
✅ No domain-specific logic
✅ Truly generic/reusable

❌ Used by only 1-2 packages
❌ Contains domain logic
❌ "Might be useful someday"
