"""
Each model in this module conforms to the corresponding WES model names as specified by the GA4GH schema (https://ga4gh.github.io/workflow-execution-service-schemas/docs/).

This module provides Pydantic models for the Workflow Execution Service (WES) schema,
supporting validation, serialization, and deserialization of WES data structures.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator

from crategen.converters.utils import convert_to_iso8601


class State(str, Enum):
    """Enumeration of workflow states in the Workflow Execution Service (WES).
    
    These states represent the different stages a workflow can be in during its lifecycle.
    
    **Attributes:**
    
    - **UNKNOWN**: The state of the workflow is unknown.
    - **QUEUED**: The workflow is queued.
    - **INITIALIZING**: The workflow is initializing.
    - **RUNNING**: The workflow is running.
    - **PAUSED**: The workflow is paused.
    - **COMPLETE**: The workflow has completed successfully.
    - **EXECUTOR_ERROR**: The workflow encountered an executor error.
    - **SYSTEM_ERROR**: The workflow encountered a system error.
    - **CANCELLED**: The workflow was cancelled by the user.
    - **CANCELING**: The workflow is in the process of being cancelled.
    - **PREEMPTED**: The workflow was preempted by the system.
    
    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/state_enum
    """
    UNKNOWN = "UNKNOWN"
    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    EXECUTOR_ERROR = "EXECUTOR_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CANCELLED = "CANCELLED"
    CANCELING = "CANCELING"
    PREEMPTED = "PREEMPTED"


class WESOutputs(BaseModel):
    """Represents an output file or directory from a workflow run.
    
    **Attributes:**
    
    - **location** (`str`): The location (URL or path) where the output is stored.
    - **name** (`str`): The name of the output file or directory.
    
    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/outputs_model
    """
    location: str
    name: str


class Log(BaseModel):
    """
    Represents a run log in the Workflow Execution Service (WES).

    **Attributes:**

    - **name** (`Optional[str]`): The task or workflow name.
    - **cmd** (`Optional[list[str]]`): The command line that was executed.
    - **start_time** (`Optional[str]`): When the command started executing, in ISO 8601 format.
    - **end_time** (`Optional[str]`): When the command stopped executing, in ISO 8601 format.
    - **stdout** (`Optional[str]`): A URL to retrieve standard output logs of the workflow run or task.
    - **stderr** (`Optional[str]`): A URL to retrieve standard error logs of the workflow run or task.
    - **exit_code** (`Optional[int]`): The exit code of the program.
    - **system_logs** (`optional[list[str]]`):  Any logs the system decides are relevant, which are not tied directly to a workflow.

    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/runlog_model
    """

    name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cmd: Optional[List[str]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    system_logs: Optional[List[str]] = None

    @validator("start_time", "end_time")
    def validate_datetime(cls, value):
        """Validate and convert datetime values to RFC3339/ISO8601 format.
        
        This validator handles both datetime objects and string representations,
        converting them to a consistent ISO8601 format with UTC timezone (Z suffix).
        
        Args:
            value (Union[datetime, str, None]): The datetime value to validate and convert
            
        Returns:
            Optional[str]: The formatted datetime string, or None if input was None
        """
        # Handle both string and datetime objects
        if value is None:
            return None
        # If it's already a datetime object, convert it to ISO format
        if isinstance(value, datetime):
            return value.isoformat() + "Z"
        # Otherwise, use the utility function for string conversion
        return convert_to_iso8601(value)


class TaskLog(Log):
    """
    Represents a task log in the Workflow Execution Service (WES).

    **Attributes:**

    - **name** (`str`): The task or workflow name.
    - **cmd** (`Optional[list[str]]`): The command line that was executed.
    - **start_time** (`Optional[str]`): When the command started executing, in ISO 8601 format.
    - **end_time** (`Optional[str]`): When the command stopped executing, in ISO 8601 format.
    - **stdout** (`Optional[str]`): A URL to retrieve standard output logs of the workflow run or task.
    - **stderr** (`Optional[str]`): A URL to retrieve standard error logs of the workflow run or task.
    - **exit_code** (`Optional[int]`): The exit code of the program.
    - **system_logs** (`Optional[list[str]]`):  Any logs the system decides are relevant, which are not tied directly to a workflow.
    - **id** (`str`): A unique identifier which maybe used to reference the task.
    - **tes_uri** (`Optional[str]`): An optional URL pointing to an extended task definition defined by a TES api.

    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/runlog_model
    """

    id: str
    tes_uri: Optional[str] = None
    name: str = Field(...)


class RunRequest(BaseModel):
    """
    Represents a workflow request in WES.

    **Attributes:**

    - **workflow_params** (`Optional[dict[str, str]]`): The workflow run parameterizations (JSON encoded),
      including input and output file locations.
    - **workflow_type** (`str`): The workflow descriptor type.
    - **workflow_type_version** (`str`): The workflow descriptor type version.
    - **tags** (`Optional[dict[str, str]]`): Additional tags associated with the workflow.
    - **workflow_engine_parameters** (Optional[dict[str, str]]): Input values specific to the workflow engine.
    - **workflow_engine** (`Optional[str]`): The workflow engine.
    - **workflow_engine_version** (`Optional[str]`): The workflow engine version.
    - **workflow_url** (`str`): The workflow url.

    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/runrequest_model
    """

    workflow_params: dict[str, str]
    workflow_type: str
    workflow_type_version: str
    tags: Optional[dict[str, str]] = {}
    workflow_engine_parameters: Optional[dict[str, str]] = None
    workflow_engine: Optional[str] = None
    workflow_engine_version: Optional[str] = None
    workflow_url: str

    @root_validator()
    def validate_workflow_engine(cls, values):
        """Validate workflow engine dependencies.
        
        If workflow_engine_version is set, then workflow_engine must also be set.
        
        Args:
            values (dict): The model field values
            
        Returns:
            dict: The validated field values
            
        Raises:
            ValueError: If workflow_engine_version is set but workflow_engine is not
        """
        engine_version = values.get("workflow_engine_version")
        engine = values.get("workflow_engine")
        if engine_version is not None and engine is None:
            raise ValueError(
                "The 'workflow_engine' attribute is required when the 'workflow_engine_version' attribute is set"
            )
        return values


class WESData(BaseModel):
    """
    Represents a WES run.

    **Attributes:**

    - **run_id** (`str`): The unique identifier for the WES run.
    - **request** (`Optional[RunRequest]`): The request associated with the WES run.
    - **state** (`Optional[State]`): The state of the WES run.
    - **run_log** (`Optional[Log]`): The log of the WES run.
    - **task_logs_url** (`Optional[str]`): A reference to the complete url which may be used 
      to obtain a paginated list of task logs for this workflow.
    - **task_logs** (`Optional[list[Log | TaskLog] | None]`): The logs of individual tasks within the run.
      This attribute is deprecated.
    - **outputs** (`dict[str, str]`): The outputs of the WES run.

    **Reference:** https://ga4gh.github.io/workflow-execution-service-schemas/docs/#tag/run_model
    """

    run_id: str
    request: Optional[RunRequest] = None
    state: Optional[State] = None
    run_log: Optional[Log] = None
    task_logs_url: Optional[str] = None
    task_logs: Optional[List[Union[Log, TaskLog]]] = None
    outputs: dict[str, str] = {}

    @root_validator
    def check_deprecated_fields(cls, values):
        """Check for usage of deprecated fields and issue warnings.
        
        Currently warns about task_logs field which is deprecated in favor of task_logs_url.
        
        Args:
            values (dict): The model field values
            
        Returns:
            dict: The field values unchanged
        """
        if values.get("task_logs") is not None:
            print(
                "DeprecationWarning: The 'task_logs' field is deprecated and will be removed in future versions. Use 'task_logs_url' instead."
            )
        return values
