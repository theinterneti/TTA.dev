"""TTA.dev MCP server: orientation and primitive analysis tools."""

from typing import Any

from ._helpers import (
    _check_code_size,
    logger,
)


def register_primitives_tools(mcp: Any, analyzer: Any, _ro: Any) -> None:
    """Register primitive orientation and analysis tools with the MCP server."""

    @mcp.tool(annotations=_ro)
    async def tta_bootstrap(agent_id: str = "", task_hint: str = "") -> dict[str, Any]:
        """One-call orientation for coding agents. Returns primitives, tools, patterns, and provider status.

        Call this FIRST at the start of any TTA.dev agent session to get full context.

        Args:
            agent_id: Identifier for this agent session (used for logging, optional)
            task_hint: Brief description of what you're trying to build (used to rank primitives)

        Returns:
            Complete TTA.dev orientation package: primitives catalog, MCP tool index,
            quick-start patterns, and live provider status.
        """
        import re
        from importlib.metadata import version as _pkg_version
        from pathlib import Path

        logger.info("mcp_tool_called", tool="tta_bootstrap", agent_id=agent_id, task_hint=task_hint)

        # ── 1. Package version ────────────────────────────────────────────────
        try:
            pkg_version = _pkg_version("ttadev")
        except Exception:
            pkg_version = "0.1.0"

        # ── 2. Parse PRIMITIVES_CATALOG.md ────────────────────────────────────
        _max_primitives = 15  # keep response within token budget
        _desc_len = 70  # max chars for when_to_use description

        primitives: list[dict[str, str]] = []
        catalog_path = Path(__file__).parents[5] / "PRIMITIVES_CATALOG.md"
        if not catalog_path.exists():
            catalog_path = Path(__file__).parents[4] / "PRIMITIVES_CATALOG.md"

        _import_re = re.compile(r"from\s+(ttadev[\w.]*)\s+import\s+(\w+)")
        _section_re = re.compile(r"^## (.+)")
        _primitive_re = re.compile(r"^### ([\w\[\], ]+)")
        # Line prefixes to skip when collecting a human-readable description
        _skip_pfx = (
            "```",
            "#",
            "|",
            "- ",
            "* ",
            "> ",
            "!",
            "**Source",
            "**Import",
            "**Status",
            "**Test",
            "**Type",
            "**Key",
            "**Prop",
            "**Feature",
            "**Usage",
            "**State",
            "**Param",
        )

        _category_map: dict[str, str] = {
            "core workflow primitives": "core",
            "recovery primitives": "recovery",
            "performance primitives": "performance",
            "skill primitives": "skill",
            "llm routing primitives": "llm_routing",
            "orchestration primitives": "orchestration",
            "testing primitives": "testing",
            "observability primitives": "observability",
            "adaptive/self-improving primitives": "adaptive",
            "ace framework primitives": "ace",
            "coordination primitives": "coordination",
            "collaboration primitives": "collaboration",
        }
        # Allowlist: only emit these names to keep the payload focused
        _emit_names: set[str] = {
            "WorkflowPrimitive",
            "SequentialPrimitive",
            "ParallelPrimitive",
            "ConditionalPrimitive",
            "RouterPrimitive",
            "RetryPrimitive",
            "FallbackPrimitive",
            "TimeoutPrimitive",
            "CompensationPrimitive",
            "CircuitBreakerPrimitive",
            "CachePrimitive",
            "MemoryPrimitive",
            "ModelRouterPrimitive",
            "DelegationPrimitive",
            "TaskClassifierPrimitive",
            "MockPrimitive",
            "InstrumentedPrimitive",
            "AdaptivePrimitive",
            "AdaptiveRetryPrimitive",
            "SelfLearningCodePrimitive",
            "GitCollaborationPrimitive",
        }

        if catalog_path.exists():
            raw = catalog_path.read_text(encoding="utf-8")
            current_category = "core"
            current_name: str | None = None
            current_desc_lines: list[str] = []
            current_import: str = ""

            def _flush_primitive() -> None:
                if not current_name:
                    return
                clean = current_name.split("[")[0].strip()
                if clean not in _emit_names:
                    return
                desc = " ".join(current_desc_lines).strip()
                if not desc:
                    desc = f"A {current_category} primitive."
                imp = current_import or f"from ttadev.primitives import {clean}"
                primitives.append(
                    {
                        "name": clean,
                        "category": current_category,
                        "when_to_use": desc[:_desc_len],
                        "import": imp,
                    }
                )

            for line in raw.splitlines():
                sec = _section_re.match(line)
                if sec:
                    _flush_primitive()
                    current_name = None
                    current_desc_lines = []
                    current_import = ""
                    current_category = _category_map.get(
                        sec.group(1).strip().lower(), current_category
                    )
                    continue

                prim = _primitive_re.match(line)
                if prim:
                    _flush_primitive()
                    current_name = prim.group(1).strip()
                    current_desc_lines = []
                    current_import = ""
                    continue

                if current_name:
                    imp_match = _import_re.search(line)
                    if imp_match and not current_import:
                        current_import = f"from {imp_match.group(1)} import {imp_match.group(2)}"
                        continue
                    # Collect human-readable description lines only.
                    # Bold lines like "**Auto retry with exponential backoff.**" are good;
                    # code fence lines (```python) and bullet lists are not.
                    stripped = line.strip()
                    if (
                        stripped
                        and not stripped.startswith(_skip_pfx)
                        and stripped not in ("-", "---")
                        and "`" not in stripped  # skip inline code
                        and len(current_desc_lines) < 2
                    ):
                        # Strip markdown bold markers
                        cleaned = stripped.strip("*").strip()
                        if cleaned and len(cleaned) > 10:
                            current_desc_lines.append(cleaned)

            _flush_primitive()

        # Deduplicate, preserve catalog order, cap at _max_primitives
        seen: set[str] = set()
        deduped: list[dict[str, str]] = []
        for p in primitives:
            if p["name"] not in seen:
                seen.add(p["name"])
                deduped.append(p)
            if len(deduped) >= _max_primitives:
                break
        primitives = deduped

        # Fallback: use analyzer when catalog parse yielded nothing
        if not primitives:
            for p in analyzer.list_primitives()[:_max_primitives]:
                desc = p.get("description") or (p.get("use_cases") or [""])[0] or ""
                primitives.append(
                    {
                        "name": p.get("name", ""),
                        "category": p.get("category", "core"),
                        "when_to_use": desc[:_desc_len],
                        "import": p.get("import_path", ""),
                    }
                )

        # ── 3. MCP tool index grouped by domain ───────────────────────────────
        try:
            all_tools = await mcp.list_tools()
            all_tool_names = [t.name for t in all_tools]
        except Exception:
            all_tool_names = list(mcp._tool_manager._tools.keys())

        def _domain(name: str) -> str:
            if name == "tta_bootstrap":
                return "orientation"
            if "_" in name:
                prefix = name.split("_")[0]
                if prefix in {"control", "llm", "memory", "workflow"}:
                    return prefix
            return "analysis"

        mcp_tools: dict[str, list[str]] = {}
        for tool_name in all_tool_names:
            domain = _domain(tool_name)
            mcp_tools.setdefault(domain, []).append(tool_name)

        # ── 4. Provider status ────────────────────────────────────────────────
        try:
            from ttadev.primitives.mcp_server.tools.observability import _get_providers_status

            provider_status = _get_providers_status()
        except Exception as exc:
            provider_status = {"error": str(exc), "providers": []}

        # ── 5. Quick-start guide (≈150 words, stays in token budget) ─────────
        quick_start = (
            "TTA.dev: composable workflow primitives for reliable AI apps.\n\n"
            "GETTING STARTED:\n"
            "1. Import: `from ttadev.primitives import RetryPrimitive, WorkflowContext`\n"
            "2. Compose with >> (sequential) or | (parallel):\n"
            "   `workflow = fetch >> parse >> store`\n"
            "   `parallel = step_a | step_b | step_c`\n"
            "3. Execute: `await workflow.execute(data, WorkflowContext(workflow_id='...'))`\n\n"
            "PRIMITIVE GROUPS:\n"
            "- Recovery: Retry, Fallback, Timeout, CircuitBreaker\n"
            "- Performance: Cache, Memory\n"
            "- Core: Sequential, Parallel, Conditional\n"
            "- Orchestration: Delegation, MultiModel\n\n"
            "KEY MCP TOOLS:\n"
            "- tta_bootstrap: this tool — call first\n"
            "- list_primitives / get_primitive_info\n"
            "- llm_list_providers / llm_recommend_model\n"
            "- analyze_code: scan code for opportunities\n\n"
            "RULES: Never write manual retry loops (RetryPrimitive). "
            "Never use time.sleep for timeouts (TimeoutPrimitive)."
        )

        # ── 6. Key patterns (concise) ─────────────────────────────────────────
        patterns = (
            "Sequential: a >> b >> c\n"
            "Parallel:   a | b | c\n"
            "Retry:      RetryPrimitive(primitive=p, max_retries=3)\n"
            "Cache:      CachePrimitive(primitive=p, ttl_seconds=300)\n"
            "Timeout:    TimeoutPrimitive(primitive=p, timeout_seconds=30.0)\n"
            "Fallback:   FallbackPrimitive(primary=p1, fallbacks=[p2, p3])\n"
            "Circuit:    CircuitBreakerPrimitive(primitive=p, config=CircuitBreakerConfig(...))\n"
            "Context:    WorkflowContext(workflow_id='my-wf')\n"
        )

        # ── 7. Task-hint relevance ranking ────────────────────────────────────
        # Common words that appear in almost every primitive description — skip them
        _stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "to",
            "of",
            "in",
            "for",
            "with",
            "build",
            "create",
            "use",
            "using",
            "that",
            "this",
            "is",
            "it",
            "my",
        }
        top_for_task: list[dict[str, str]] = []
        if task_hint and primitives:
            hint_words = {w for w in task_hint.lower().split() if w not in _stop_words}

            def _score(p: dict[str, str]) -> tuple[int, int]:
                name_lower = p["name"].lower()
                text = (name_lower + " " + p["category"] + " " + p["when_to_use"]).lower()
                base = sum(1 for w in hint_words if w in text)
                # Bonus: name *starts with* a hint word (e.g. "retry" → RetryPrimitive wins
                # over AdaptiveRetryPrimitive for the "retry" hint)
                prefix_bonus = sum(1 for w in hint_words if name_lower.startswith(w))
                # Tie-break: prefer shorter (more specific) names
                return (base + prefix_bonus, -len(p["name"]))

            scored = sorted(primitives, key=_score, reverse=True)
            top_for_task = [p for p in scored if _score(p)[0] > 0][:3]
            if not top_for_task:
                top_for_task = scored[:3]

        return {
            "version": pkg_version,
            "agent_id": agent_id,
            "primitives": primitives,
            "mcp_tools": mcp_tools,
            "quick_start": quick_start,
            "patterns": patterns,
            "provider_status": provider_status,
            "top_primitives_for_task": top_for_task,
        }

    @mcp.tool(annotations=_ro)
    async def analyze_code(
        code: str,
        file_path: str = "",
        project_type: str = "general",
        min_confidence: float = 0.3,
    ) -> dict[str, Any]:
        """Analyze code and recommend TTA.dev primitives.

        Analyzes source code for patterns and suggests appropriate
        TTA.dev primitives with confidence scores, reasoning, and
        ready-to-use code templates.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context
            project_type: Type of project (general, web, api, data_processing, ml)
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            dict: Analysis report with the following structure:
                {
                    "detected_patterns": List[str],
                    "recommendations": List[{
                        "primitive_name": str,
                        "confidence_score": float,
                        "reasoning": str,
                        "code_template": str,
                        "import_path": str
                    }],
                    "detected_issues": List[str],
                    "optimization_opportunities": List[str],
                    "complexity_level": str
                }
        """
        if err := _check_code_size(code):
            return err
        logger.info(
            "mcp_tool_called",
            tool="analyze_code",
            file_path=file_path,
            code_length=len(code),
        )
        report = analyzer.analyze(
            code,
            file_path=file_path,
            project_type=project_type,
            min_confidence=min_confidence,
        )
        return report.to_dict()

    @mcp.tool(annotations=_ro)
    async def get_primitive_info(primitive_name: str) -> dict[str, Any]:
        """Get detailed information about a TTA.dev primitive.

        Returns comprehensive documentation including description,
        use cases, code templates, and related primitives.

        Args:
            primitive_name: Name of the primitive (e.g., "RetryPrimitive")

        Returns:
            dict: Primitive documentation with the following structure:
                {
                    "name": str,
                    "description": str,
                    "import_path": str,
                    "use_cases": List[str],
                    "templates": List[str],
                    "related_primitives": List[str],
                    "category": str
                }
        """
        return analyzer.get_primitive_info(primitive_name)

    @mcp.tool(annotations=_ro)
    async def list_primitives() -> list[dict[str, Any]]:
        """List all available TTA.dev primitives.

        Returns a list of all primitives with their descriptions
        and primary use cases.

        Returns:
            list[dict]: List of primitives, each with the following structure:
                [{
                    "name": str,
                    "description": str,
                    "import_path": str,
                    "use_cases": List[str],
                    "category": str
                }]
        """
        return analyzer.list_primitives()

    @mcp.tool(annotations=_ro)
    async def search_templates(query: str) -> list[dict[str, Any]]:
        """Search for primitive templates by keyword.

        Searches through all templates and examples to find
        relevant code patterns.

        Args:
            query: Search query (e.g., "retry", "cache", "parallel")

        Returns:
            list[dict]: List of matching templates with structure:
                [{
                    "primitive_name": str,
                    "match_type": str,  # "template" or "example"
                    "match_text": str,
                    "relevance_score": float
                }]
        """
        return analyzer.search_templates(query)
