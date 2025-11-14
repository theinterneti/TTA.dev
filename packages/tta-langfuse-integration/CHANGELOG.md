# Changelog

All notable changes to the tta-langfuse-integration package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-11-14

### Added
- Initial package structure for Langfuse integration
- `initialize_langfuse()` - Global client setup and configuration
- `is_langfuse_enabled()` - Check if Langfuse is active
- `shutdown_langfuse()` - Graceful shutdown with event flushing
- `LangfusePrimitive` - Wrapper primitive for automatic LLM tracing
- `LangfuseObservablePrimitive` - Decorator-based alternative
- Support for environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`)
- Automatic token usage tracking
- Cost calculation support
- Session and user tracking
- Metadata and tags support
- Integration with `WorkflowContext` for correlation
- Graceful degradation when Langfuse not configured
- Comprehensive documentation:
  - README.md - Quick start guide
  - ARCHITECTURE.md - Technical architecture
  - INTEGRATION_GUIDE.md - Complete integration patterns
  - QUICK_REFERENCE.md - API reference
  - IMPLEMENTATION_SUMMARY.md - Project summary
- Basic unit tests for initialization and primitives
- Added to workspace in root `pyproject.toml`
- Updated `AGENTIC_PRIMITIVES_ROADMAP.md` with Langfuse entry

### Dependencies
- `langfuse>=2.0.0` - Langfuse Python SDK
- `tta-dev-primitives` - Core primitives integration
- `opentelemetry-api>=1.38.0` - OpenTelemetry compatibility
- `opentelemetry-sdk>=1.38.0` - OpenTelemetry SDK
- `pydantic>=2.6.0` - Data validation

### Documentation
- Complete architecture documentation
- Integration patterns and examples
- Cost tracking guide
- Troubleshooting guide
- Best practices

## [Unreleased]

### Planned Features
- Prompt management and versioning
- Automated evaluation support
- Dataset management for testing
- A/B testing capabilities
- Cost budgeting and alerts
- Fine-tuning data collection
- Enhanced error tracking with stack traces
- Custom evaluation criteria
- Integration examples with popular LLM providers
- Performance benchmarks

---

## Version History

- **0.1.0** (2024-11-14) - Initial release with core functionality
