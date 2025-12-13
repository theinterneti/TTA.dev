# TODO System Quickstart Guide

**Get started with TTA.dev's TODO architecture in 5 minutes**

**Last Updated:** November 2, 2025

---

## 🚀 For Developers

### Adding a Development TODO

1. **Open today's journal:**
   ```
   logseq/journals/2025_11_02.md
   ```

2. **Copy this template:**
   ```markdown
   - TODO [Your task description] #dev-todo
     type:: [implementation|testing|documentation|examples]
     priority:: [high|medium|low]
     package:: [tta-dev-primitives|tta-observability-integration|etc.]
     status:: not-started
     created:: [[2025-11-02]]
   ```

3. **Fill in the details**

4. **Link to context:**
   ```markdown
   related:: [[TTA.dev/Component/Name]]
   ```

**Full templates:** [[TODO Templates]]

---

## 🎓 For Learners

### Starting a Learning Path

1. **Check available paths:**
   - [[TTA.dev/Learning Paths]]

2. **Add first TODO:**
   ```markdown
   - TODO Complete Getting Started tutorial #learning-todo
     type:: tutorial
     audience:: new-users
     difficulty:: beginner
     learning-path:: [[Getting Started]]
     created:: [[2025-11-02]]
   ```

3. **Work through sequence**

4. **Mark milestones when complete**

---

## 🤖 For Agents

### Understanding the System

1. **Read the architecture:**
   - [[TTA.dev/TODO Architecture]]

2. **Know your categories:**
   - `#dev-todo` - Building TTA.dev
   - `#learning-todo` - User education
   - `#template-todo` - Reusable patterns
   - `#ops-todo` - Infrastructure

3. **Use templates:**
   - [[TODO Templates]]

4. **Check metrics:**
   - [[TTA.dev/TODO Metrics Dashboard]]

---

## 📊 Daily Workflow

### Morning (2 minutes)

1. Check in-progress TODOs:
   ```
   {{query (task DOING)}}
   ```

2. Review high priority:
   ```
   {{query (and (task TODO) (property priority high))}}
   ```

3. Update your status

### During Work

1. Mark TODO as DOING when starting:
   ```markdown
   - DOING [Task] #dev-todo
     status:: in-progress
     started:: [[2025-11-02]]
   ```

2. Update if blocked:
   ```markdown
   blocked:: true
   blocker:: [reason]
   ```

### Evening (3 minutes)

1. Mark completed TODOs as DONE:
   ```markdown
   - DONE [Task] #dev-todo
     completed:: [[2025-11-02]]
   ```

2. Review tomorrow's priorities

---

## 📦 Package-Specific Work

### Check Your Package

1. **tta-dev-primitives:**
   - [[TTA.dev/Packages/tta-dev-primitives/TODOs]]

2. **Filter by component:**
   ```
   {{query (and (task TODO) (property component "RouterPrimitive"))}}
   ```

3. **Check dependencies:**
   ```
   {{query (and (task TODO) (property blocks))}}
   ```

---

## 🔍 Quick Queries

### Find TODOs

**By package:**
```
{{query (and (task TODO) (property package "tta-dev-primitives"))}}
```

**By priority:**
```
{{query (and (task TODO) (property priority high))}}
```

**By type:**
```
{{query (and (task TODO) (property type "testing"))}}
```

**Blocked tasks:**
```
{{query (and (task TODO) (property blocked true))}}
```

---

## 📚 Reference Pages

### Start Here
- [[TTA.dev/TODO Architecture]] - System design
- [[TODO Templates]] - Copy-paste templates

### Daily Use
- [[TODO Management System]] - Main dashboard
- Your package TODO page

### Analytics
- [[TTA.dev/TODO Metrics Dashboard]] - Metrics

### Learning
- [[TTA.dev/Learning Paths]] - Learning sequences

### Visualization
- [[Whiteboard - TODO Dependency Network]] - Visual map

---

## 💡 Pro Tips

1. **Always add context:** Use `related::` to link pages
2. **Track dependencies:** Use `depends-on::` and `blocks::`
3. **Be specific:** "Add tests for CachePrimitive TTL" not "Add tests"
4. **Update daily:** Keep status current
5. **Use templates:** Don't reinvent the wheel

---

## 🆘 Common Issues

### "Don't know which category to use"

- Building code? → `#dev-todo`
- Creating tutorial? → `#learning-todo`
- Making template? → `#template-todo`
- Deploying? → `#ops-todo`

### "Don't know required properties"

Check [[TTA.dev/TODO Architecture]] → "TODO Properties Reference"

### "Can't find my TODOs"

Check [[TODO Management System]] → Your category section

### "Need a template"

[[TODO Templates]] → Find your scenario

---

## ✅ Checklist

Before committing work:

- [ ] TODO marked as DONE
- [ ] Completion date added
- [ ] Related TODOs updated
- [ ] Dependencies resolved
- [ ] New TODOs created for follow-up

---

**Quick Start Time:** 5 minutes
**Full Mastery:** Read [[TTA.dev/TODO Architecture]]
**Questions:** See [[TODO Management System]]


---
**Logseq:** [[TTA.dev/Logseq/Pages/Todo system quickstart]]
