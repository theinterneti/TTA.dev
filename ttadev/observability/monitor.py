"""Simple monitoring wrapper for TTA.dev workflows."""
from typing import Any
import time
from ttadev.primitives.core.base import WorkflowPrimitive, WorkflowContext
from ttadev.observability.markdown_logger import get_logger

class MonitoredWorkflow:
    """Wrapper that adds markdown logging to any workflow."""
    
    def __init__(self, workflow: WorkflowPrimitive, name: str = "workflow"):
        self.workflow = workflow
        self.name = name
        self.logger = get_logger()
    
    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with logging."""
        start_time = time.time()
        
        # Log workflow start
        self.logger.log_workflow_execution(self.name, "started", 0)
        self.logger.log_daily_activity(
            f"Workflow Started: {self.name}",
            {"workflow_id": context.workflow_id or "N/A"}
        )
        
        try:
            result = await self.workflow.execute(input_data, context)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log success
            self.logger.log_workflow_execution(self.name, "success", duration_ms)
            self.logger.log_daily_activity(
                f"Workflow Completed: {self.name}",
                {
                    "status": "success",
                    "duration_ms": f"{duration_ms:.2f}",
                    "workflow_id": context.workflow_id or "N/A"
                }
            )
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log failure
            self.logger.log_workflow_execution(self.name, f"error: {str(e)}", duration_ms)
            self.logger.log_daily_activity(
                f"Workflow Failed: {self.name}",
                {
                    "status": "error",
                    "error": str(e),
                    "duration_ms": f"{duration_ms:.2f}",
                    "workflow_id": context.workflow_id or "N/A"
                }
            )
            raise

def monitor(workflow: WorkflowPrimitive, name: str = "workflow") -> MonitoredWorkflow:
    """Wrap a workflow with markdown logging."""
    return MonitoredWorkflow(workflow, name)
