# TTA Migration Quick Start

**Ready to begin? Here's what to do next.**

---

## Step 1: Run Setup Script (5 minutes)

```bash
cd ~/repos/TTA.dev
./scripts/setup-tta-audit-sandbox.sh
```

**What this does:**
- Creates `~/sandbox/tta-audit/` directory
- Clones TTA repository
- Installs dependencies
- Runs initial analysis
- Creates analysis scripts

**Expected output:** "Setup Complete" message

---

## Step 2: Review Initial Analysis (10 minutes)

```bash
cd ~/sandbox/tta-audit

# View package statistics
cat analysis/package-statistics.md

# See all classes
head -50 analysis/class-list.txt

# Check directory structure
cat analysis/directory-structure.txt
```

---

## Step 3: Analyze Packages (30 minutes)

```bash
cd TTA

# Analyze each package
python ../scripts/analyze_package.py tta-narrative-engine
python ../scripts/analyze_package.py tta-ai-framework
python ../scripts/analyze_package.py universal-agent-context
python ../scripts/analyze_package.py ai-dev-toolkit
```

**Output:** JSON structure files in `../analysis/`

---

## Step 4: Generate Audit Report (5 minutes)

```bash
cd ../scripts
./generate_report.sh > ../analysis/audit-report.md

# View report
cat ../analysis/audit-report.md
```

---

## Step 5: Transfer to TTA.dev (5 minutes)

```bash
# Create analysis directory in TTA.dev
mkdir -p ~/repos/TTA.dev/docs/planning/tta-analysis

# Copy all analysis files
cp ~/sandbox/tta-audit/analysis/* \
   ~/repos/TTA.dev/docs/planning/tta-analysis/

# Update Logseq
cd ~/repos/TTA.dev
# Edit logseq/journals/2025_11_08.md
# Mark sandbox setup as DONE
# Add new TODOs for findings
```

---

## Step 6: Create Primitive Mapping (2-3 hours)

**In TTA.dev:**

```bash
cd ~/repos/TTA.dev
vim docs/planning/tta-analysis/primitive-mapping.json
```

**Format:**
```json
{
  "TTA Classes": [
    {
      "name": "NarrativeCoherence",
      "file": "coherence/validator.py",
      "lines": 250,
      "maps_to": "CoherenceValidatorPrimitive",
      "complexity": "medium",
      "dependencies": ["neo4j", "pydantic"],
      "notes": "Needs OpenTelemetry integration"
    }
  ]
}
```

---

## Troubleshooting

### "Command not found: uv"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Permission denied: setup script"

```bash
chmod +x ~/repos/TTA.dev/scripts/setup-tta-audit-sandbox.sh
```

### "Git clone failed"

Check internet connection and GitHub access:
```bash
ssh -T git@github.com
```

---

## Key Files

### Created by Setup
- `~/sandbox/tta-audit/README.md` - Sandbox guide
- `~/sandbox/tta-audit/analysis/package-statistics.md` - Stats
- `~/sandbox/tta-audit/scripts/analyze_package.py` - Analyzer

### You Will Create
- `~/repos/TTA.dev/docs/planning/tta-analysis/primitive-mapping.json`
- `~/repos/TTA.dev/packages/tta-narrative-primitives/DESIGN_SPEC.md`

---

## Documentation

- **Workflow Guide:** `docs/planning/TTA_SANDBOX_WORKFLOW.md`
- **Full Plan:** `docs/planning/TTA_REMEDIATION_PLAN.md`
- **Checklist:** `docs/planning/TTA_AUDIT_CHECKLIST.md`

---

## Time Estimates

| Task | Time |
|------|------|
| Setup script | 5 min |
| Initial review | 10 min |
| Package analysis | 30 min |
| Report generation | 5 min |
| Transfer to TTA.dev | 5 min |
| **Day 1 Total** | **~60 min** |
| Primitive mapping | 2-3 hours |
| Design spec | 3-4 hours |
| **Week 1 Total** | **~10 hours** |

---

## Success Checklist

### After Setup Script

- [ ] Sandbox created at `~/sandbox/tta-audit/`
- [ ] TTA repository cloned
- [ ] Dependencies installed
- [ ] Initial analysis complete
- [ ] Scripts created

### After Analysis

- [ ] 4 packages analyzed
- [ ] JSON structure files generated
- [ ] Audit report created
- [ ] Files transferred to TTA.dev

### After Mapping

- [ ] primitive-mapping.json created
- [ ] All TTA classes mapped
- [ ] Dependencies documented
- [ ] Complexity assessed

---

## Next Steps After Day 1

1. Review primitive-mapping.json
2. Create DESIGN_SPEC.md
3. Set up package structure in TTA.dev
4. Begin implementing first primitive

---

**Ready?** Run the setup script!

```bash
cd ~/repos/TTA.dev
./scripts/setup-tta-audit-sandbox.sh
```


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Quick_start]]
