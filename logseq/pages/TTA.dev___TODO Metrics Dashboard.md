type:: [[Dashboard]]
description:: Metrics and analytics for the TTA.dev knowledge base

# TODO Metrics Dashboard

Analytics dashboard for tracking TODO completion rates and KB health.

## Active TODOs by Tag

{{query (and (task TODO NOW DOING) [[dev-todo]])}}

{{query (and (task TODO NOW DOING) [[learning-todo]])}}

{{query (and (task TODO NOW DOING) [[ops-todo]])}}

## Completion Trends

{{query (and (task DONE) (between -30d today))}}

## Summary Stats

Use Logseq queries to generate metrics on TODO volume, completion rate, and tag distribution.

## Related Pages
- [[TODO Management System]] - Main task dashboard
- [[TTA.dev/TODO Architecture]] - System design
