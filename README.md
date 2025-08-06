# TTA Development

This directory contains the **development environment** and **work-in-progress** components for the Therapeutic Text Adventure (TTA) project. This is where active development happens before code moves to production.

## 🛠️ Purpose

- **Development Environment**: Tools and configurations for development
- **Work in Progress**: Features being actively developed
- **Testing Infrastructure**: Comprehensive test suites
- **Documentation**: Development guides and API documentation
- **Scripts**: Automation and utility scripts

## 📁 Directory Structure

### Core Development Components

- **`core/`**: Game engine and main application logic
- **`docs/`**: Comprehensive project documentation
- **`tests/`**: Test suites for all components
- **`scripts/`**: Development and deployment scripts

### Documentation

The `docs/` directory contains extensive documentation:

- **`architecture/`**: System architecture and design documents
- **`development/`**: Development guides and coding standards
- **`guides/`**: User guides and tutorials
- **`integration/`**: Integration guides for external systems
- **`models/`**: Model selection and evaluation documentation

## 🚀 Getting Started

### Development Setup

1. **Clone and Setup**:
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Setup pre-commit hooks
   pre-commit install
   ```

2. **Environment Configuration**:
   ```bash
   # Copy from production template
   cp ../tta.prod/.env.example .env
   
   # Add development-specific settings
   echo "DEBUG_MODE=true" >> .env
   echo "LOG_LEVEL=DEBUG" >> .env
   ```

3. **Database Setup**:
   ```bash
   # Start Neo4j (if using Docker)
   docker-compose up -d neo4j
   
   # Run database migrations
   python scripts/setup_database.py
   ```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_agents.py -v
pytest tests/test_knowledge_graph.py -v
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=src tests/
```

## 🔧 Development Tools

### Core Game Engine

The `core/` directory contains the main game engine:

- **`main.py`**: Main application entry point
- **`dynamic_game.py`**: Dynamic game world generation
- **`langgraph_engine.py`**: LangGraph-based agent orchestration

### Testing Infrastructure

Comprehensive test coverage for all components:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component testing
- **End-to-End Tests**: Full system testing
- **Performance Tests**: Load and performance testing

### Development Scripts

The `scripts/` directory contains automation tools:

- **Database Management**: Setup, migration, backup scripts
- **Model Testing**: Automated model evaluation
- **Deployment**: Production deployment automation
- **Utilities**: Various development utilities

## 📚 Documentation

### Architecture Documentation

- **`docs/architecture/Overview.md`**: System overview
- **`docs/architecture/Agentic_RAG.md`**: Agent-based RAG implementation
- **`docs/architecture/Neo4j_Schema.md`**: Knowledge graph schema

### Development Guides

- **`docs/development/Development_Guide.md`**: Comprehensive development guide
- **`docs/development/CodingStandards.md`**: Coding standards and best practices
- **`docs/development/TestingStrategy.md`**: Testing approach and guidelines

### Integration Documentation

- **`docs/integration/AI_Libraries_Integration_Plan.md`**: AI library integration
- **`docs/models/Model_Selection_Strategy.md`**: Model selection guidelines

## 🔄 Development Workflow

### Feature Development

1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Develop**: Write code following coding standards
3. **Test**: Add tests and ensure all tests pass
4. **Document**: Update relevant documentation
5. **Review**: Submit pull request for review
6. **Deploy**: Merge to main after approval

### Code Quality

- **Linting**: Use `black`, `isort`, and `ruff` for code formatting
- **Type Checking**: Use `mypy` for type checking
- **Testing**: Maintain high test coverage
- **Documentation**: Keep documentation up to date

### Continuous Integration

The project uses CI/CD for:

- **Automated Testing**: Run tests on all commits
- **Code Quality Checks**: Linting and type checking
- **Security Scanning**: Dependency vulnerability scanning
- **Documentation Building**: Automatic documentation generation

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **System Tests**: Test complete workflows
4. **Performance Tests**: Test system performance
5. **Security Tests**: Test security measures

### Test Data

- **Fixtures**: Reusable test data and mocks
- **Factories**: Dynamic test data generation
- **Snapshots**: Expected output snapshots for regression testing

## 📊 Monitoring and Debugging

### Logging

- **Structured Logging**: JSON-formatted logs for analysis
- **Log Levels**: Appropriate log levels for different environments
- **Performance Logging**: Track performance metrics

### Debugging Tools

- **Debug Mode**: Enhanced debugging in development
- **Profiling**: Performance profiling tools
- **Tracing**: Request tracing for complex workflows

## 🚀 Deployment

### Development Deployment

- **Local Development**: Run locally with hot reload
- **Development Server**: Shared development environment
- **Staging**: Production-like environment for testing

### Production Deployment

- **Containerization**: Docker-based deployment
- **Orchestration**: Kubernetes or Docker Compose
- **Monitoring**: Production monitoring and alerting

## 🤝 Contributing

### Development Guidelines

1. **Follow Standards**: Adhere to coding standards
2. **Write Tests**: Include tests for all new features
3. **Document Changes**: Update documentation
4. **Review Process**: Participate in code reviews

### Getting Help

- **Documentation**: Check the docs first
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Team Chat**: Internal team communication channels

## 🔗 Related Resources

- **Production Code**: `../tta.prod/` - Stable, production-ready code
- **Prototypes**: `../tta.prototype/` - Experimental features
- **Main Documentation**: `../Documentation/` - Project-wide documentation
