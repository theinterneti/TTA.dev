# GitHub Copilot Auto-Reviewer Setup

This document explains how GitHub Copilot is automatically assigned as a reviewer for all pull requests in the TTA.dev repository.

## Implementation

We use a **dual approach** to ensure Copilot is assigned as a reviewer:

### 1. CODEOWNERS File (Primary Method)

**File:** `.github/CODEOWNERS`

The CODEOWNERS file designates `@Copilot` as the owner of all files (`*`). When a pull request is created, GitHub automatically requests a review from code owners.

**Advantages:**
- Native GitHub feature
- No additional workflow execution needed
- Works immediately on PR creation

**Limitations:**
- Requires Copilot to be a repository collaborator
- May not work if Copilot bot doesn't have proper permissions

### 2. GitHub Actions Workflow (Fallback Method)

**File:** `.github/workflows/auto-assign-copilot.yml`

This workflow triggers on `pull_request` events (types: `opened`, `reopened`) and uses the GitHub API to assign Copilot as a reviewer.

**Advantages:**
- Programmatic control over reviewer assignment
- Handles edge cases (checks if already assigned)
- Provides detailed logging
- Graceful error handling

**Triggers:**
- When a new PR is opened
- When a closed PR is reopened

**Permissions Required:**
- `pull-requests: write` - To assign reviewers
- `contents: read` - To read repository content

## How It Works

### CODEOWNERS Flow

```
1. Developer creates PR
2. GitHub reads .github/CODEOWNERS
3. GitHub automatically requests review from @Copilot
4. Copilot appears in "Reviewers" section
```

### GitHub Actions Flow

```
1. Developer creates PR
2. Workflow triggers on pull_request.opened event
3. Workflow checks if Copilot is already assigned
4. If not assigned, workflow requests Copilot as reviewer via API
5. Copilot appears in "Reviewers" section
```

## Verification

To verify the setup is working:

1. **Create a test PR:**
   ```bash
   git checkout -b test/copilot-reviewer
   echo "test" > test.txt
   git add test.txt
   git commit -m "test: verify Copilot auto-assignment"
   git push origin test/copilot-reviewer
   gh pr create --title "Test: Copilot Auto-Reviewer" --body "Testing automatic Copilot reviewer assignment"
   ```

2. **Check the PR:**
   - Go to the PR page on GitHub
   - Look for Copilot in the "Reviewers" section
   - Check the Actions tab to see if the workflow ran successfully

3. **View workflow logs:**
   ```bash
   gh run list --workflow=auto-assign-copilot.yml
   gh run view <run-id> --log
   ```

## Troubleshooting

### Copilot Not Appearing as Reviewer

**Possible causes:**

1. **Copilot not a collaborator:**
   - Solution: Add Copilot as a repository collaborator in Settings → Collaborators

2. **CODEOWNERS file not in correct location:**
   - Must be in `.github/CODEOWNERS` (not `CODEOWNERS` at root)
   - Verify: `ls -la .github/CODEOWNERS`

3. **Workflow permissions insufficient:**
   - Check workflow run logs for permission errors
   - Verify repository Actions settings allow workflows to create PRs

4. **Branch protection rules:**
   - Ensure branch protection doesn't prevent automated reviewer assignment

### Workflow Fails

**Check the logs:**
```bash
gh run list --workflow=auto-assign-copilot.yml --limit 5
gh run view <run-id> --log
```

**Common errors:**

- `"not a collaborator"` - Add Copilot to repository collaborators
- `"Resource not accessible"` - Check workflow permissions
- `"Bad credentials"` - Verify GITHUB_TOKEN has correct scopes

## Configuration

### Modify CODEOWNERS

To add additional code owners for specific paths:

```
# Global owner
* @Copilot

# Package-specific owners
/packages/tta-dev-primitives/ @theinterneti @Copilot
/packages/tta-observability-integration/ @theinterneti @Copilot

# Documentation
/docs/ @theinterneti @Copilot
```

### Modify Workflow

To change when the workflow triggers:

```yaml
on:
  pull_request:
    types: [opened, reopened, ready_for_review]  # Add more trigger types
```

To assign additional reviewers:

```javascript
reviewers: ['Copilot', 'another-reviewer'],
```

## Maintenance

### Regular Checks

- **Monthly:** Verify Copilot is still assigned on new PRs
- **After GitHub updates:** Test if CODEOWNERS/workflow still works
- **When adding collaborators:** Update CODEOWNERS if needed

### Updating the Workflow

When updating the workflow:

1. Test changes in a fork or feature branch first
2. Verify workflow syntax: `gh workflow view auto-assign-copilot.yml`
3. Monitor first few PRs after deployment

## References

- [GitHub CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Actions - Pull Request Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request)
- [GitHub REST API - Request Reviewers](https://docs.github.com/en/rest/pulls/review-requests)
- [GitHub Actions - github-script](https://github.com/actions/github-script)

## Support

If you encounter issues:

1. Check this documentation first
2. Review workflow logs: `gh run list --workflow=auto-assign-copilot.yml`
3. Verify CODEOWNERS syntax: `cat .github/CODEOWNERS`
4. Create an issue in the repository with:
   - PR number where it failed
   - Workflow run logs
   - Expected vs actual behavior

---

**Last Updated:** 2025-10-29
**Maintained by:** @theinterneti



---
**Logseq:** [[TTA.dev/.github/Copilot_reviewer_setup]]
