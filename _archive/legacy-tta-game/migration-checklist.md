# Migration Checklist
- origin /TTA/TTA
- destination /app
## Priority Components
1. Source Code
- [ ] Review and migrate `src/agents/`
- [ ] Review and migrate `src/core/`
- [ ] Review and migrate `src/knowledge/`
- [ ] Review and migrate `src/models/`
- [ ] Review and migrate `src/tools/`

2. Essential Configuration
- [ ] `.env.example`
- [ ] `docker-compose.yml`
- [ ] `Dockerfile`
- [ ] `.gitignore`

3. Documentation
- [ ] `README.md`
- [ ] `PLANNING.md`
- [ ] Architecture docs
- [ ] Development guides

4. Tests
- [ ] Unit tests
- [ ] Integration tests
- [ ] Test fixtures

## Migration Process
1. For each file/directory:
   - Review content
   - Check for duplicates
   - Select most recent/relevant version
   - Verify dependencies
   - Test functionality
   - Document migration in MIGRATION.md

## Exclude
- Archived versions
- Duplicate configurations
- Obsolete documentation
- Temporary files
- Build artifacts

---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/Migration-checklist]]
