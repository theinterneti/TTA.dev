# tta-observability-integration Package

type:: Package
status:: Active
owner:: @observability-team
package-path:: platform/observability
last-updated:: [[2025-10-31]]

---

## Purpose

Observability primitives and integrations (OpenTelemetry, Prometheus exporters, metrics and tracing helpers).

## Current Status

- ✅ Production-ready
- ✅ Prometheus metrics export configured (port 9464)
- ✅ Instrumentation wrappers for primitives

## Links

- Source: `platform/observability/`
- Docs: `docs/observability/`, [[TTA.dev/Guides/Observability]]

## Next Actions (Architecture)

- TODO Create package architecture page and whiteboard
  type:: documentation
  priority:: medium
  related:: [[TTA.dev/Architecture]]

- TODO Add example showing metrics collection for CachePrimitive
  type:: examples
  priority:: medium

## Owner Notes
- Ensure safe failure when OTLP is unavailable
- Export Prometheus metrics under `/metrics` endpoint
