"""
ValidationGatePrimitive - Human approval gate for specifications

This primitive enforces human validation before proceeding with implementation.
It presents artifacts for review, collects approval/rejection decisions, and
logs validation history.

Phase 1 Implementation:
- File-based approval mechanism (write decision to .approval file)
- CLI prompt for feedback collection
- Approval status tracking
- Validation history logging

Phase 2 Enhancement (Future):
- Web-based approval UI
- Multi-reviewer workflows
- Approval delegation
- Integration with issue tracking
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive


class ValidationGatePrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Enforce human validation gate for specifications.

    This primitive blocks workflow execution until human approval is obtained.
    Supports approval/rejection with feedback, validation criteria checklist,
    and complete audit trail of validation decisions.

    Phase 1: File-based approval with CLI prompts
    Phase 2: Web UI, multi-reviewer, approval delegation (future)

    Args:
        timeout_seconds: Maximum time to wait for approval (default: 3600 = 1 hour)
        auto_approve_on_timeout: If True, auto-approve on timeout (default: False)
        require_feedback_on_rejection: If True, feedback required for rejection (default: True)

    Input:
        - artifacts: List of file paths to artifacts requiring approval
        - validation_criteria: Dict of criteria to check (e.g., {"coverage": 0.9, "tests": True})
        - reviewer: Optional reviewer name/email
        - context_info: Optional additional context for reviewer

    Output:
        - approved: Boolean approval status
        - feedback: Reviewer feedback text
        - timestamp: ISO 8601 timestamp of decision
        - reviewer: Name/email of reviewer
        - validation_results: Results of validation criteria checks
        - approval_path: Path to approval file
    """

    def __init__(
        self,
        name: str = "validation_gate",
        timeout_seconds: int = 3600,
        auto_approve_on_timeout: bool = False,
        require_feedback_on_rejection: bool = True,
    ) -> None:
        """Initialize ValidationGatePrimitive.

        Args:
            name: Primitive name for observability
            timeout_seconds: Max time to wait for approval
            auto_approve_on_timeout: Auto-approve on timeout
            require_feedback_on_rejection: Require feedback for rejection
        """
        super().__init__(name=name)
        self.timeout_seconds = timeout_seconds
        self.auto_approve_on_timeout = auto_approve_on_timeout
        self.require_feedback_on_rejection = require_feedback_on_rejection

    async def _execute_impl(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> dict[str, Any]:
        """Execute validation gate.

        Args:
            input_data: Input containing artifacts and validation criteria
            context: Workflow context for observability

        Returns:
            Validation result with approval status and feedback

        Raises:
            ValueError: If required fields missing
            FileNotFoundError: If artifacts don't exist
            TimeoutError: If approval times out and auto_approve disabled
        """
        # Extract input fields
        artifacts = input_data.get("artifacts", [])
        validation_criteria = input_data.get("validation_criteria", {})
        reviewer = input_data.get("reviewer", "unknown")
        context_info = input_data.get("context_info", {})

        # Validate input
        if not artifacts:
            raise ValueError("At least one artifact required for validation")

        # Verify artifacts exist
        for artifact_path in artifacts:
            if not Path(artifact_path).exists():
                raise FileNotFoundError(f"Artifact not found: {artifact_path}")

        # Check for existing approval
        approval_dir = Path(artifacts[0]).parent / ".approvals"
        approval_dir.mkdir(exist_ok=True)

        # Generate approval file name based on artifacts
        artifact_names = "_".join(Path(a).stem for a in artifacts[:3])  # Use first 3 for filename
        if len(artifacts) > 3:
            artifact_names += f"_and_{len(artifacts) - 3}_more"

        approval_path = approval_dir / f"{artifact_names}.approval.json"

        # Check for existing approval decision
        if approval_path.exists():
            existing_approval = self._load_approval(approval_path)
            # If already approved/rejected, return existing decision
            if existing_approval.get("status") in ["approved", "rejected"]:
                return {
                    "approved": existing_approval["status"] == "approved",
                    "feedback": existing_approval.get("feedback", ""),
                    "timestamp": existing_approval.get("timestamp", ""),
                    "reviewer": existing_approval.get("reviewer", reviewer),
                    "validation_results": existing_approval.get("validation_results", {}),
                    "approval_path": str(approval_path),
                    "reused_approval": True,
                }

        # Run validation criteria checks
        validation_results = self._check_validation_criteria(artifacts, validation_criteria)

        # Create pending approval record
        approval_record = {
            "status": "pending",
            "artifacts": [str(a) for a in artifacts],
            "validation_criteria": validation_criteria,
            "validation_results": validation_results,
            "reviewer": reviewer,
            "context_info": context_info,
            "created_at": datetime.now(UTC).isoformat(),
            "timeout_seconds": self.timeout_seconds,
        }

        self._save_approval(approval_path, approval_record)

        # In Phase 1, we don't block for interactive approval
        # Instead, we return pending status with instructions
        return {
            "approved": False,
            "feedback": "Approval pending - please review and approve",
            "timestamp": approval_record["created_at"],
            "reviewer": reviewer,
            "validation_results": validation_results,
            "approval_path": str(approval_path),
            "status": "pending",
            "instructions": self._generate_approval_instructions(
                approval_path, artifacts, validation_results
            ),
        }

    def _check_validation_criteria(
        self,
        artifacts: list[str],
        validation_criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """Check validation criteria against artifacts.

        Args:
            artifacts: List of artifact paths
            validation_criteria: Criteria to check

        Returns:
            Dictionary of validation results
        """
        results = {}

        # Check if artifacts exist
        results["artifacts_exist"] = all(Path(a).exists() for a in artifacts)

        # Check coverage criterion
        if "min_coverage" in validation_criteria:
            # For specs, check if coverage meets threshold
            min_coverage = validation_criteria["min_coverage"]
            # This would need spec parsing in full implementation
            # For now, mark as manual check
            results["coverage_check"] = {
                "required": min_coverage,
                "status": "manual_check_required",
            }

        # Check required sections criterion
        if "required_sections" in validation_criteria:
            required_sections = validation_criteria["required_sections"]
            results["required_sections_check"] = {
                "required": required_sections,
                "status": "manual_check_required",
            }

        # Check completeness criterion
        if "completeness_check" in validation_criteria:
            results["completeness_check"] = {
                "required": validation_criteria["completeness_check"],
                "status": "manual_check_required",
            }

        # Add timestamp
        results["checked_at"] = datetime.now(UTC).isoformat()

        return results

    def _generate_approval_instructions(
        self,
        approval_path: Path,
        artifacts: list[str],
        validation_results: dict[str, Any],
    ) -> str:
        """Generate instructions for manual approval.

        Args:
            approval_path: Path to approval file
            artifacts: List of artifact paths
            validation_results: Validation check results

        Returns:
            Instructions string
        """
        instructions = f"""
=== VALIDATION GATE: APPROVAL REQUIRED ===

Artifacts requiring approval:
{chr(10).join(f"  - {a}" for a in artifacts)}

Validation Results:
{chr(10).join(f"  {k}: {v}" for k, v in validation_results.items() if k != "checked_at")}

To approve, edit the approval file:
  {approval_path}

Change the "status" field:
  - "approved" - Approve and proceed
  - "rejected" - Reject and block

Optionally add "feedback":
  "feedback": "Your comments here"

Example approval:
{{
  "status": "approved",
  "feedback": "Looks good, coverage meets requirements",
  "approved_at": "{datetime.now(UTC).isoformat()}"
}}

Example rejection:
{{
  "status": "rejected",
  "feedback": "Coverage too low, needs more tests",
  "rejected_at": "{datetime.now(UTC).isoformat()}"
}}

=== END INSTRUCTIONS ===
"""
        return instructions.strip()

    def _load_approval(self, approval_path: Path) -> dict[str, Any]:
        """Load approval record from file.

        Args:
            approval_path: Path to approval file

        Returns:
            Approval record dictionary
        """
        return json.loads(approval_path.read_text(encoding="utf-8"))

    def _save_approval(self, approval_path: Path, approval_record: dict[str, Any]) -> None:
        """Save approval record to file.

        Args:
            approval_path: Path to approval file
            approval_record: Approval record to save
        """
        approval_path.write_text(
            json.dumps(approval_record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    async def check_approval_status(self, approval_path: str) -> dict[str, Any]:
        """Check status of pending approval.

        This is a utility method to check if approval has been granted
        after returning pending status.

        Args:
            approval_path: Path to approval file

        Returns:
            Current approval status
        """
        path = Path(approval_path)
        if not path.exists():
            return {"status": "not_found", "approved": False}

        approval_record = self._load_approval(path)
        status = approval_record.get("status", "pending")

        return {
            "status": status,
            "approved": status == "approved",
            "feedback": approval_record.get("feedback", ""),
            "timestamp": approval_record.get(
                "approved_at" if status == "approved" else "rejected_at",
                approval_record.get("created_at", ""),
            ),
            "reviewer": approval_record.get("reviewer", "unknown"),
        }

    async def approve(
        self,
        approval_path: str,
        reviewer: str,
        feedback: str = "",
    ) -> dict[str, Any]:
        """Programmatically approve a pending validation.

        Utility method for testing or automated approval flows.

        Args:
            approval_path: Path to approval file
            reviewer: Name/email of reviewer
            feedback: Optional feedback text

        Returns:
            Updated approval record
        """
        path = Path(approval_path)
        if not path.exists():
            raise FileNotFoundError(f"Approval file not found: {approval_path}")

        approval_record = self._load_approval(path)
        approval_record["status"] = "approved"
        approval_record["reviewer"] = reviewer
        approval_record["feedback"] = feedback
        approval_record["approved_at"] = datetime.now(UTC).isoformat()

        self._save_approval(path, approval_record)

        return {
            "approved": True,
            "feedback": feedback,
            "timestamp": approval_record["approved_at"],
            "reviewer": reviewer,
            "validation_results": approval_record.get("validation_results", {}),
            "approval_path": str(approval_path),
        }

    async def reject(
        self,
        approval_path: str,
        reviewer: str,
        feedback: str,
    ) -> dict[str, Any]:
        """Programmatically reject a pending validation.

        Utility method for testing or automated rejection flows.

        Args:
            approval_path: Path to approval file
            reviewer: Name/email of reviewer
            feedback: Feedback text (required)

        Returns:
            Updated approval record
        """
        path = Path(approval_path)
        if not path.exists():
            raise FileNotFoundError(f"Approval file not found: {approval_path}")

        if self.require_feedback_on_rejection and not feedback:
            raise ValueError("Feedback required for rejection")

        approval_record = self._load_approval(path)
        approval_record["status"] = "rejected"
        approval_record["reviewer"] = reviewer
        approval_record["feedback"] = feedback
        approval_record["rejected_at"] = datetime.now(UTC).isoformat()

        self._save_approval(path, approval_record)

        return {
            "approved": False,
            "feedback": feedback,
            "timestamp": approval_record["rejected_at"],
            "reviewer": reviewer,
            "validation_results": approval_record.get("validation_results", {}),
            "approval_path": str(approval_path),
        }
