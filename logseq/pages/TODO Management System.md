alias:: TODO Dashboard, Task Dashboard
type:: [[Dashboard]]
description:: Central hub for all project TODOs and task management

# TODO Management System

Main dashboard for tracking all development, learning, and operations tasks.

## Active Tasks

{{query (and (task NOW DOING) (not (page "templates")))}}

## Upcoming Tasks

{{query (and (task TODO LATER) (not (page "templates")))}}

## Recently Completed

{{query (and (task DONE) (between -7d today))}}

## By Priority

### High Priority
{{query (and (task TODO NOW DOING) (priority A))}}

### Medium Priority
{{query (and (task TODO NOW DOING) (priority B))}}

## By Tag

### Development
{{query (and (task TODO NOW DOING) [[dev-todo]])}}

### Learning
{{query (and (task TODO NOW DOING) [[learning-todo]])}}

### Operations
{{query (and (task TODO NOW DOING) [[ops-todo]])}}

## Quick Add

Use these tags when creating TODOs:
- `#dev-todo` - Development work (building TTA.dev itself)
- `#learning-todo` - Learning and documentation
- `#ops-todo` - Operations and infrastructure
- `#template-todo` - Reusable patterns

Priority markers: `[#A]` high · `[#B]` medium · `[#C]` low

## Related Pages
- [[TTA.dev/TODOs]] - Legacy TODO dashboard
- [[TTA.dev/TODO Architecture]] - System design
- [[TODO Templates]] - Copy-paste patterns
