#!/usr/bin/env python3
"""
Workflow Monitoring Script for Phase 3 Migration

Compares v1 and v2 workflow performance and results during parallel execution.
Generates daily reports and alerts on anomalies.

Usage:
    python scripts/workflow/workflow-monitor.py --days 1 --output report.md
"""

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

try:
    from github import Github
except ImportError:
    print(
        "Error: PyGithub not installed. Run: pip install PyGithub",
        file=sys.stderr,
    )
    sys.exit(1)


@dataclass
class WorkflowMetrics:
    """Metrics for a single workflow run"""

    workflow_name: str
    run_id: int
    conclusion: str
    duration_seconds: int
    pr_number: int | None
    branch: str
    created_at: datetime
    url: str


@dataclass
class ComparisonReport:
    """Comparison report between v1 and v2 workflows"""

    date: str
    v1_runs: list[WorkflowMetrics]
    v2_runs: list[WorkflowMetrics]
    avg_duration_v1: float
    avg_duration_v2: float
    performance_delta: float  # percentage
    v1_success_rate: float
    v2_success_rate: float
    unique_v2_failures: list[WorkflowMetrics]
    alerts: list[str]


class WorkflowMonitor:
    """Monitor and compare GitHub Actions workflows"""

    def __init__(self, github_token: str, repo_name: str):
        self.gh = Github(github_token)
        self.repo = self.gh.get_repo(repo_name)

    def fetch_workflow_runs(
        self, workflow_name: str, since: datetime, branch: str | None = None
    ) -> list[WorkflowMetrics]:
        """Fetch workflow runs for a given workflow"""
        workflow = self.repo.get_workflow(workflow_name)

        runs = workflow.get_runs(created=f">={since.isoformat()}", branch=branch)

        metrics = []
        for run in runs:
            # Calculate duration
            if run.updated_at and run.created_at:
                duration = (run.updated_at - run.created_at).total_seconds()
            else:
                duration = 0

            # Extract PR number from workflow run
            pr_number = None
            if run.event == "pull_request" and run.pull_requests:
                pr_number = run.pull_requests[0].number

            metrics.append(
                WorkflowMetrics(
                    workflow_name=workflow_name,
                    run_id=run.id,
                    conclusion=run.conclusion or "pending",
                    duration_seconds=int(duration),
                    pr_number=pr_number,
                    branch=run.head_branch,
                    created_at=run.created_at,
                    url=run.html_url,
                )
            )

        return metrics

    def calculate_success_rate(self, runs: list[WorkflowMetrics]) -> float:
        """Calculate percentage of successful runs"""
        if not runs:
            return 0.0

        successful = sum(1 for r in runs if r.conclusion == "success")
        return (successful / len(runs)) * 100

    def calculate_avg_duration(self, runs: list[WorkflowMetrics]) -> float:
        """Calculate average duration in seconds"""
        if not runs:
            return 0.0

        # Filter out pending/in-progress runs
        completed = [r for r in runs if r.conclusion in ["success", "failure"]]
        if not completed:
            return 0.0

        total_duration = sum(r.duration_seconds for r in completed)
        return total_duration / len(completed)

    def find_unique_failures(
        self, v1_runs: list[WorkflowMetrics], v2_runs: list[WorkflowMetrics]
    ) -> list[WorkflowMetrics]:
        """Find failures in v2 that don't occur in v1 (for same PR)"""
        unique_failures = []

        # Group v1 runs by PR number
        v1_by_pr = {}
        for run in v1_runs:
            if run.pr_number:
                v1_by_pr[run.pr_number] = run

        # Check v2 failures
        for v2_run in v2_runs:
            if v2_run.conclusion == "failure" and v2_run.pr_number:
                # Check if v1 succeeded for same PR
                v1_run = v1_by_pr.get(v2_run.pr_number)
                if v1_run and v1_run.conclusion == "success":
                    unique_failures.append(v2_run)

        return unique_failures

    def generate_alerts(
        self,
        performance_delta: float,
        unique_failures: list[WorkflowMetrics],
        threshold: float = 0.10,
    ) -> list[str]:
        """Generate alerts based on comparison"""
        alerts = []

        # Performance degradation alert
        if performance_delta > threshold * 100:
            alerts.append(
                f"⚠️  Performance degradation: v2 is {performance_delta:.1f}% slower than v1"
            )

        # Unique failures alert
        if unique_failures:
            alerts.append(
                f"🚨 Unique v2 failures: {len(unique_failures)} PR(s) failed in v2 but passed in v1"
            )

        return alerts

    def compare_workflows(
        self, v1_workflow: str, v2_workflow: str, days: int, alert_threshold: float = 0.10
    ) -> ComparisonReport:
        """Compare v1 and v2 workflows over specified time period"""
        since = datetime.now() - timedelta(days=days)

        print(f"Fetching {v1_workflow} runs since {since.isoformat()}...")
        v1_runs = self.fetch_workflow_runs(v1_workflow, since)

        print(f"Fetching {v2_workflow} runs since {since.isoformat()}...")
        v2_runs = self.fetch_workflow_runs(v2_workflow, since)

        # Calculate metrics
        avg_v1 = self.calculate_avg_duration(v1_runs)
        avg_v2 = self.calculate_avg_duration(v2_runs)

        # Performance delta (percentage difference)
        if avg_v1 > 0:
            performance_delta = ((avg_v2 - avg_v1) / avg_v1) * 100
        else:
            performance_delta = 0.0

        # Success rates
        v1_success = self.calculate_success_rate(v1_runs)
        v2_success = self.calculate_success_rate(v2_runs)

        # Unique failures
        unique_failures = self.find_unique_failures(v1_runs, v2_runs)

        # Generate alerts
        alerts = self.generate_alerts(performance_delta, unique_failures, alert_threshold)

        return ComparisonReport(
            date=datetime.now().strftime("%Y-%m-%d"),
            v1_runs=v1_runs,
            v2_runs=v2_runs,
            avg_duration_v1=avg_v1,
            avg_duration_v2=avg_v2,
            performance_delta=performance_delta,
            v1_success_rate=v1_success,
            v2_success_rate=v2_success,
            unique_v2_failures=unique_failures,
            alerts=alerts,
        )

    def format_report_markdown(self, report: ComparisonReport) -> str:
        """Format comparison report as Markdown"""
        md = []

        md.append(f"# Workflow Comparison Report - {report.date}\n")

        # Alert section
        if report.alerts:
            md.append("## 🚨 Alerts\n")
            for alert in report.alerts:
                md.append(f"- {alert}")
            md.append("")
        else:
            md.append("## ✅ No Alerts\n")
            md.append("All metrics within acceptable thresholds.\n")

        # Summary table
        md.append("## 📊 Summary\n")
        md.append("| Metric | v1 | v2 | Delta |")
        md.append("|--------|----|----|-------|")
        md.append(f"| Runs | {len(report.v1_runs)} | {len(report.v2_runs)} | - |")
        success_delta = report.v2_success_rate - report.v1_success_rate
        md.append(
            f"| Success Rate | {report.v1_success_rate:.1f}% | "
            f"{report.v2_success_rate:.1f}% | {success_delta:+.1f}% |"
        )
        md.append(
            f"| Avg Duration | {report.avg_duration_v1:.0f}s | "
            f"{report.avg_duration_v2:.0f}s | {report.performance_delta:+.1f}% |"
        )
        md.append("")

        # Unique failures
        if report.unique_v2_failures:
            md.append("## 🚨 Unique v2 Failures\n")
            md.append("PRs that failed in v2 but passed in v1:\n")
            for failure in report.unique_v2_failures:
                md.append(f"- PR #{failure.pr_number}: [{failure.run_id}]({failure.url})")
            md.append("")

        # Recent runs
        md.append("## 📝 Recent Runs\n")
        md.append("### v1 Workflow\n")
        for run in report.v1_runs[:5]:
            status_emoji = "✅" if run.conclusion == "success" else "❌"
            pr_info = f"PR #{run.pr_number}" if run.pr_number else run.branch
            md.append(f"- {status_emoji} [{pr_info}]({run.url}) - {run.duration_seconds}s")
        md.append("")

        md.append("### v2 Workflow\n")
        for run in report.v2_runs[:5]:
            status_emoji = "✅" if run.conclusion == "success" else "❌"
            pr_info = f"PR #{run.pr_number}" if run.pr_number else run.branch
            md.append(f"- {status_emoji} [{pr_info}]({run.url}) - {run.duration_seconds}s")
        md.append("")

        # Recommendations
        md.append("## 💡 Recommendations\n")
        if not report.alerts:
            md.append("- ✅ Continue parallel execution")
            md.append("- ✅ Monitor for 7 days minimum before proceeding to Phase 3.2")
        else:
            md.append("- ⚠️  Investigate alerts before proceeding")
            md.append("- ⚠️  Consider extending parallel execution period")
            if report.unique_v2_failures:
                md.append("- 🚨 **Do not** proceed to Phase 3.2 until unique failures are resolved")
        md.append("")

        md.append("---\n")
        md.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Monitor and compare GitHub Actions workflows")
    parser.add_argument(
        "--days", type=int, default=1, help="Number of days to analyze (default: 1)"
    )
    parser.add_argument(
        "--output", type=str, help="Output file for markdown report (default: stdout)"
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=0.10,
        help="Performance degradation threshold as decimal (default: 0.10 = 10%%)",
    )
    parser.add_argument(
        "--v1-workflow",
        type=str,
        default="pr-validation.yml",
        help="V1 workflow filename (default: pr-validation.yml)",
    )
    parser.add_argument(
        "--v2-workflow",
        type=str,
        default="pr-validation-v2.yml",
        help="V2 workflow filename (default: pr-validation-v2.yml)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=os.getenv("GITHUB_REPOSITORY", "theinterneti/TTA.dev"),
        help="GitHub repository (default: from GITHUB_REPOSITORY env)",
    )

    args = parser.parse_args()

    # Get GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Create monitor
    monitor = WorkflowMonitor(github_token, args.repo)

    # Generate comparison report
    print(f"Comparing {args.v1_workflow} vs {args.v2_workflow} over last {args.days} day(s)...")
    report = monitor.compare_workflows(
        args.v1_workflow, args.v2_workflow, args.days, args.alert_threshold
    )

    # Format report
    markdown = monitor.format_report_markdown(report)

    # Output report
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown)
        print(f"Report written to {args.output}")
    else:
        print(markdown)

    # Exit with error code if there are alerts
    if report.alerts:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
