- TODO Triage Session #ops-todo
  type:: workflow
  priority:: medium
  status:: DOING
  created:: [[YYYY-MM-DD]]
  last-reviewed:: [[YYYY-MM-DD]]
  estimated-effort:: 30 minutes
  notes:: Review codebase scan results and categorize TODOs.

  ### 🎯 Goal
  Systematically review `TODO` comments from the codebase scan and determine if they are actionable Logseq tasks or non-actionable contextual notes.

  ### 📋 Workflow Steps

  1.  **Run Codebase Scan**:
      ```bash
      uv run python scripts/scan-codebase-todos.py --output triage_todos.csv
      ```
      *Purpose*: Generate a fresh list of `TODO` comments from the codebase.

  2.  **Review `triage_todos.csv`**:
      *Open the `triage_todos.csv` file in your editor.*
      For each `TODO` entry:
      *   **Is it an actionable task?** (e.g., "Implement feature X", "Fix bug Y", "Write tests for Z")
          *   **YES**: Create a new Logseq TODO entry in today's journal (`logseq/journals/YYYY_MM_DD.md`) with appropriate tags (`#dev-todo` or `#user-todo`) and properties (`type::`, `priority::`, `package::`, `related::`, `estimated-effort::`).
          *   **NO**: It's a contextual note (e.g., "This could be optimized", "Assumes input is validated").
              *   **Action**: Add `#non-actionable` to the original code comment.
                  *Example*: `# TODO: This could be optimized #non-actionable`
                  *Purpose*: Prevent it from appearing in future actionable scans.

  3.  **Update Codebase (if necessary)**:
      If you added `#non-actionable` tags to code comments, commit those changes.
      ```bash
      git add .
      git commit -m "chore: Tag non-actionable TODOs"
      ```

  4.  **Re-run Scan (Optional)**:
      To verify your changes, run the scan again and check if the number of `TODOs` has decreased.
      ```bash
      uv run python scripts/scan-codebase-todos.py
      ```

  ### ✅ Completion Criteria
  - [ ] All `TODO` entries in `triage_todos.csv` have been reviewed.
  - [ ] Actionable `TODOs` have been migrated to Logseq journals.
  - [ ] Non-actionable `TODOs` in code have been tagged with `#non-actionable`.
  - [ ] Codebase changes (adding `#non-actionable` tags) have been committed.

  ### 🔗 Related Pages
  - [[TODO Management System]]
  - [[TODO Guidelines for TTA.dev]]
  - [[scripts/scan-codebase-todos.py]]
