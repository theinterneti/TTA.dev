# ACE + E2B Integration Plan
**Revolutionary Self-Learning Code Execution**

## Executive Summary

Combine Agentic Context Engine (ACE) with E2B sandboxes to create primitives that learn from actual code execution, not just LLM reasoning. This enables "learning by doing" - agents that improve their code generation and debugging through real-world execution feedback.

## The Power of This Combination

### ACE Alone
- Learns from LLM reasoning about success/failure
- Builds "playbooks" of strategies
- Self-reflection without ground truth

### E2B Alone
- Secure code execution in 150ms
- Isolated environments with full observability
- Multiple language support

### ACE + E2B Together 🚀
- **Learn from actual execution results**
- **Self-improving code generation**
- **Environment-specific strategy learning**
- **Real debugging pattern recognition**

## Implementation Strategy

### Phase 1: Basic ACE-Enabled Code Primitive

Create `SelfLearningCodeExecutionPrimitive` that:

```python
class SelfLearningCodeExecutionPrimitive(InstrumentedPrimitive):
    """Code execution primitive that learns from execution results."""

    def __init__(self):
        self.ace_generator = Generator(llm_client)
        self.ace_reflector = Reflector(llm_client)
        self.ace_curator = Curator(llm_client)
        self.playbook = Playbook()
        self.e2b_executor = CodeExecutionPrimitive()

    async def execute(self, input_data, context):
        # 1. Generate code using current playbook strategies
        code_output = await self.ace_generator.generate(
            question=input_data["task"],
            context=input_data.get("context", ""),
            playbook=self.playbook
        )

        # 2. Execute code in E2B sandbox
        execution_result = await self.e2b_executor.execute({
            "code": code_output.final_answer,
            "language": input_data.get("language", "python")
        }, context)

        # 3. Reflect on execution results
        reflection = await self.ace_reflector.reflect(
            question=input_data["task"],
            generator_output=code_output,
            playbook=self.playbook,
            ground_truth=input_data.get("expected_output"),
            feedback=self._format_execution_feedback(execution_result)
        )

        # 4. Update playbook with learned strategies
        curator_output = await self.ace_curator.curate(
            reflection=reflection,
            playbook=self.playbook,
            question_context="code generation"
        )

        # 5. Apply playbook updates
        self.playbook.apply_delta(curator_output.delta)

        return {
            "code": code_output.final_answer,
            "execution_result": execution_result,
            "learned_strategies": len(curator_output.delta.operations),
            "playbook_size": len(self.playbook.bullets())
        }
```

### Phase 2: Advanced Learning Patterns

#### 2.1 Iterative Code Refinement with Learning

```python
class IterativeLearningCodePrimitive(SelfLearningCodeExecutionPrimitive):
    """Iteratively refines code while learning debugging strategies."""

    async def execute(self, input_data, context):
        max_iterations = input_data.get("max_iterations", 3)

        for iteration in range(max_iterations):
            # Generate code using learned strategies
            result = await super().execute(input_data, context)

            # If successful, we're done
            if result["execution_result"]["success"]:
                return result

            # Learn from failure and try again
            input_data["context"] += f"\n\nPrevious attempt failed: {result['execution_result']['error']}"

        return result  # Return final attempt
```

#### 2.2 Environment-Specific Learning

```python
class EnvironmentSpecificLearningPrimitive(SelfLearningCodeExecutionPrimitive):
    """Maintains separate playbooks for different environments."""

    def __init__(self):
        super().__init__()
        self.playbooks = {
            "python": Playbook(),
            "javascript": Playbook(),
            "ml": Playbook(),
            "data_analysis": Playbook()
        }

    def get_playbook(self, context):
        """Select appropriate playbook based on context."""
        if "ml" in context or "machine learning" in context:
            return self.playbooks["ml"]
        elif "data" in context or "pandas" in context:
            return self.playbooks["data_analysis"]
        # ... etc
```

### Phase 3: Advanced ACE + E2B Patterns

#### 3.1 Multi-Agent Code Review with Learning

```python
class LearningCodeReviewWorkflow:
    """Multi-agent workflow where agents learn from each other."""

    def __init__(self):
        self.code_generator = SelfLearningCodeExecutionPrimitive()
        self.code_reviewer = SelfLearningCodeReviewPrimitive()
        self.code_optimizer = SelfLearningOptimizationPrimitive()

    async def execute(self, task):
        # 1. Generate initial code (learns generation patterns)
        code_result = await self.code_generator.execute(task)

        # 2. Review code (learns review patterns)
        review_result = await self.code_reviewer.execute({
            "code": code_result["code"],
            "task": task["description"]
        })

        # 3. Optimize based on review (learns optimization patterns)
        if review_result["needs_optimization"]:
            optimized_result = await self.code_optimizer.execute({
                "code": code_result["code"],
                "review_feedback": review_result["feedback"]
            })
            return optimized_result

        return code_result
```

#### 3.2 Benchmark-Driven Learning

```python
class BenchmarkLearningPrimitive(SelfLearningCodeExecutionPrimitive):
    """Learns by running against known benchmarks."""

    async def learn_from_benchmarks(self, benchmark_suite):
        """Train on benchmark problems to build initial strategies."""

        for benchmark in benchmark_suite:
            result = await self.execute({
                "task": benchmark["problem"],
                "expected_output": benchmark["expected_output"],
                "test_cases": benchmark["test_cases"]
            })

            # Each benchmark adds to learned strategies
            print(f"Learned {result['learned_strategies']} strategies from {benchmark['name']}")

        print(f"Total playbook size: {len(self.playbook.bullets())} strategies")
```

## Real-World Use Cases

### 1. Self-Improving API Client Generation
Learn patterns for:
- Error handling strategies
- Rate limiting approaches
- Authentication patterns
- Data transformation techniques

### 2. Adaptive Data Processing
Learn patterns for:
- Data cleaning strategies
- Format conversion techniques
- Performance optimization approaches
- Error recovery methods

### 3. Intelligent Code Debugging
Learn patterns for:
- Common error resolution
- Test case generation
- Code refactoring strategies
- Performance bottleneck identification

## Implementation Roadmap

### Week 1: Foundation
- [ ] Merge ACE experiments from `experiment/ace-integration` branch
- [ ] Create basic `SelfLearningCodeExecutionPrimitive`
- [ ] Test with simple code generation tasks
- [ ] Verify playbook learning works

### Week 2: Enhancement
- [ ] Add iterative refinement capabilities
- [ ] Implement environment-specific learning
- [ ] Create comprehensive test suite
- [ ] Document learning patterns

### Week 3: Advanced Patterns
- [ ] Multi-agent learning workflows
- [ ] Benchmark-driven learning
- [ ] Performance optimization learning
- [ ] Real-world use case validation

### Week 4: Production Ready
- [ ] Error handling and edge cases
- [ ] Observability and monitoring
- [ ] Documentation and examples
- [ ] Integration with existing primitives

## Success Metrics

1. **Learning Effectiveness**: Measurable improvement in success rates over iterations
2. **Strategy Quality**: Human-readable, useful strategies in playbooks
3. **Generalization**: Learned strategies work on similar but different problems
4. **Performance**: Learning overhead acceptable for production use
5. **Observability**: Clear visibility into what was learned and why

## Next Steps

1. **Immediate**: Review ACE experiment results from previous branch
2. **Short-term**: Implement basic self-learning code primitive
3. **Medium-term**: Build advanced learning patterns
4. **Long-term**: Create production-ready learning ecosystem

This combination of ACE + E2B could be groundbreaking - agents that genuinely learn and improve from real execution experience, not just theoretical reasoning.
