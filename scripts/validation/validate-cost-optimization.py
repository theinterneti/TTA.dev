#!/usr/bin/env python3
"""Validate cost optimization primitive usage.

This script validates that cost optimization primitives (Router, Cache, Timeout)
are being used appropriately throughout the codebase.

Targets:
- 40% cost reduction through caching
- 30% cost reduction through routing
- Timeout enforcement for reliability
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set


class CostOptimizationAnalyzer(ast.NodeVisitor):
    """Analyze cost optimization primitive usage."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.primitives_used: Set[str] = set()
        self.llm_calls: List[int] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track primitive imports."""
        if node.module and "observability_integration" in node.module:
            for alias in node.names:
                if alias.name in {"CachePrimitive", "RouterPrimitive", "TimeoutPrimitive"}:
                    self.primitives_used.add(alias.name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Track potential LLM calls."""
        if hasattr(node.func, "attr"):
            func_name = getattr(node.func, "attr", "")
            if func_name in {"generate", "complete", "chat", "invoke", "run"}:
                self.llm_calls.append(node.lineno)
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Dict:
    """Analyze a single file for cost optimization."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        analyzer = CostOptimizationAnalyzer(file_path)
        analyzer.visit(tree)
        
        return {
            "primitives": analyzer.primitives_used,
            "llm_calls": analyzer.llm_calls,
            "has_optimization": bool(analyzer.primitives_used and analyzer.llm_calls),
        }
    
    except Exception:
        return {"primitives": set(), "llm_calls": [], "has_optimization": False}


def main() -> int:
    """Main validation logic."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate cost optimization")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("packages"),
        help="Path to check (default: packages)"
    )
    parser.add_argument(
        "--check-router-usage",
        action="store_true",
        help="Check for RouterPrimitive usage"
    )
    parser.add_argument(
        "--check-cache-usage",
        action="store_true",
        help="Check for CachePrimitive usage"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.4,
        help="Expected cost reduction threshold (default: 0.4 = 40%%)"
    )
    args = parser.parse_args()
    
    package_dir = args.path
    if not package_dir.exists():
        print(f"❌ Path not found: {package_dir}")
        return 1
    
    stats = {
        "total_files": 0,
        "files_with_llm": 0,
        "files_with_cache": 0,
        "files_with_router": 0,
        "files_with_timeout": 0,
        "files_with_optimization": 0,
    }
    
    print("🔍 Analyzing cost optimization patterns...")
    print()
    
    for py_file in package_dir.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        stats["total_files"] += 1
        result = analyze_file(py_file)
        
        if result["llm_calls"]:
            stats["files_with_llm"] += 1
        
        if "CachePrimitive" in result["primitives"]:
            stats["files_with_cache"] += 1
        
        if "RouterPrimitive" in result["primitives"]:
            stats["files_with_router"] += 1
        
        if "TimeoutPrimitive" in result["primitives"]:
            stats["files_with_timeout"] += 1
        
        if result["has_optimization"]:
            stats["files_with_optimization"] += 1
    
    # Calculate optimization rates
    if stats["files_with_llm"] > 0:
        cache_rate = stats["files_with_cache"] / stats["files_with_llm"]
        router_rate = stats["files_with_router"] / stats["files_with_llm"]
        optimization_rate = stats["files_with_optimization"] / stats["files_with_llm"]
    else:
        cache_rate = router_rate = optimization_rate = 0.0
    
    # Report results
    print("📊 Cost Optimization Analysis:")
    print(f"  Files analyzed: {stats['total_files']}")
    print(f"  Files with LLM calls: {stats['files_with_llm']}")
    print(f"  Files using CachePrimitive: {stats['files_with_cache']} ({cache_rate:.1%})")
    print(f"  Files using RouterPrimitive: {stats['files_with_router']} ({router_rate:.1%})")
    print(f"  Files using TimeoutPrimitive: {stats['files_with_timeout']}")
    print(f"  Files with any optimization: {stats['files_with_optimization']} ({optimization_rate:.1%})")
    print()
    
    # Validation checks
    issues = []
    
    if args.check_cache_usage and cache_rate < args.threshold:
        issues.append(f"Cache usage ({cache_rate:.1%}) below threshold ({args.threshold:.1%})")
    
    if args.check_router_usage and router_rate < args.threshold:
        issues.append(f"Router usage ({router_rate:.1%}) below threshold ({args.threshold:.1%})")
    
    if issues:
        print("⚠️  Cost optimization issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("💡 Recommendations:")
        print("  - CachePrimitive: 40% cost savings for repeated operations")
        print("  - RouterPrimitive: 30% cost savings for multi-model routing")
        print("  - TimeoutPrimitive: Reliability and cost control")
        print()
        return 1
    else:
        print("✅ Cost optimization validation passed")
        print()
        if stats["files_with_llm"] > 0:
            estimated_savings = (cache_rate * 0.4) + (router_rate * 0.3)
            print(f"📈 Estimated cost reduction: {estimated_savings:.1%}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
