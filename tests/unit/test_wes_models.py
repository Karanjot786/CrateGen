"""Tests for WES models"""

import datetime
import io
import sys
import pytest
from unittest.mock import patch

from crategen.models.wes_models import (
    State,
    WESOutputs,
    Log,
    TaskLog,
    RunRequest,
    WESData
)

# Test data constants
valid_datetime_strings = [
    "2020-10-02T16:00:00.000Z",
    "2024-10-15T18:14:34+00:00",
    "2024-10-15T18:14:34.948996+00:00",
    "2024-10-15T19:01:06.872464+00:00",
]

invalid_datetime_strings = [
    "2020-10-02 16:00:00",  # Missing 'T' separator
    "2020-10-02T16:00:00",  # Missing timezone
    "20201002T160000Z",  # Missing separators
    "2020-10-02T16:00:00.000+0200",  # Invalid timezone format
    "2020-10-02T16:00:00.000 GMT",  # Invalid timezone format
    "02-10-2020T16:00:00.000Z",  # Incorrect date order
]

test_workflow_url = "https://raw.githubusercontent.com/example/workflow.cwl"

class TestState:
    """Test suite for State enum"""

    def test_state_enum_values(self):
        """Test that State enum has correct values"""
        assert State.UNKNOWN == "UNKNOWN"
        assert State.QUEUED == "QUEUED"
        assert State.INITIALIZING == "INITIALIZING"
        assert State.RUNNING == "RUNNING"
        assert State.PAUSED == "PAUSED"
        assert State.COMPLETE == "COMPLETE"
        assert State.EXECUTOR_ERROR == "EXECUTOR_ERROR"
        assert State.SYSTEM_ERROR == "SYSTEM_ERROR"
        assert State.CANCELLED == "CANCELLED"
        assert State.CANCELING == "CANCELING"
        assert State.PREEMPTED == "PREEMPTED"

class TestWESOutputs:
    """Test suite for WESOutputs model"""

    def test_wes_outputs_creation(self):
        """Test creating WESOutputs objects"""
        # Test with minimal required fields
        outputs = WESOutputs(location="/path/to/output", name="output_file")
        assert outputs.location == "/path/to/output"
        assert outputs.name == "output_file"
        
        # Test with edge case values
        outputs = WESOutputs(location="s3://bucket/key", name="")
        assert outputs.location == "s3://bucket/key"
        assert outputs.name == ""

class TestLog:
    """Test suite for Log model"""

    def test_log_creation_with_minimal_fields(self):
        """Test creating Log with minimal fields"""
        log = Log()
        assert log.name is None
        assert log.cmd is None
        assert log.start_time is None
        assert log.end_time is None
        assert log.stdout is None
        assert log.stderr is None
        assert log.exit_code is None
        assert log.system_logs is None

    def test_log_creation_with_all_fields(self):
        """Test creating Log with all fields"""
        log = Log(
            name="workflow_run",
            cmd=["cwltool", "workflow.cwl", "inputs.json"],
            start_time=datetime.datetime(2023, 1, 1, 12, 0, 0),
            end_time=datetime.datetime(2023, 1, 1, 12, 30, 0),
            stdout="https://example.com/stdout.log",
            stderr="https://example.com/stderr.log",
            exit_code=0,
            system_logs=["Starting job", "Job completed"]
        )
        assert log.name == "workflow_run"
        assert log.cmd == ["cwltool", "workflow.cwl", "inputs.json"]
        assert log.stdout == "https://example.com/stdout.log"
        assert log.stderr == "https://example.com/stderr.log"
        assert log.exit_code == 0
        assert log.system_logs == ["Starting job", "Job completed"]
        # Datetime fields are validated and converted to RFC3339

class TestTaskLog:
    """Test suite for TaskLog model"""

    def test_task_log_creation(self):
        """Test creating TaskLog objects"""
        # Test with required fields
        task_log = TaskLog(
            id="task-001",
            name="alignment_task",
        )
        assert task_log.id == "task-001"
        assert task_log.name == "alignment_task"
        assert task_log.tes_uri is None
        
        # Test with all fields
        task_log = TaskLog(
            id="task-002",
            name="variant_calling",
            tes_uri="https://tes-service.org/tasks/task-002",
            cmd=["samtools", "mpileup", "-f", "ref.fa", "input.bam"],
            exit_code=0
        )
        assert task_log.id == "task-002"
        assert task_log.name == "variant_calling"
        assert task_log.tes_uri == "https://tes-service.org/tasks/task-002"
        assert task_log.cmd == ["samtools", "mpileup", "-f", "ref.fa", "input.bam"]
        assert task_log.exit_code == 0

    def test_task_log_name_required(self):
        """Test that name is required for TaskLog"""
        with pytest.raises(ValueError):
            TaskLog(id="task-001")

class TestRunRequest:
    """Test suite for RunRequest model"""

    def test_run_request_minimal(self):
        """Test creating RunRequest with minimal fields"""
        request = RunRequest(
            workflow_params={"input": "input.txt", "output": "output.txt"},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url="https://example.com/workflow.cwl"
        )
        assert request.workflow_params == {"input": "input.txt", "output": "output.txt"}
        assert request.workflow_type == "CWL"
        assert request.workflow_type_version == "v1.0"
        assert request.workflow_url == "https://example.com/workflow.cwl"
        assert request.tags == {}
        assert request.workflow_engine_parameters is None
        assert request.workflow_engine is None
        assert request.workflow_engine_version is None

    def test_run_request_all_fields(self):
        """Test creating RunRequest with all fields"""
        request = RunRequest(
            workflow_params={"input": "input.txt", "output": "output.txt"},
            workflow_type="WDL",
            workflow_type_version="1.0",
            workflow_url="https://example.com/workflow.wdl",
            tags={"project": "genomics", "priority": "high"},
            workflow_engine_parameters={"memory": "16G"},
            workflow_engine="cromwell",
            workflow_engine_version="52.0.1"
        )
        assert request.workflow_params == {"input": "input.txt", "output": "output.txt"}
        assert request.workflow_type == "WDL"
        assert request.workflow_type_version == "1.0"
        assert request.workflow_url == "https://example.com/workflow.wdl"
        assert request.tags == {"project": "genomics", "priority": "high"}
        assert request.workflow_engine_parameters == {"memory": "16G"}
        assert request.workflow_engine == "cromwell"
        assert request.workflow_engine_version == "52.0.1"

    def test_workflow_engine_validation(self):
        """Test that workflow_engine is required when workflow_engine_version is set"""
        # Valid: No version specified
        request = RunRequest(
            workflow_params={},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url="https://example.com/workflow.cwl"
        )
        assert request.workflow_engine is None
        assert request.workflow_engine_version is None

        # Valid: Both engine and version specified
        request = RunRequest(
            workflow_params={},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url="https://example.com/workflow.cwl",
            workflow_engine="cwltool",
            workflow_engine_version="3.1.20220502201013"
        )
        assert request.workflow_engine == "cwltool"
        assert request.workflow_engine_version == "3.1.20220502201013"

        # Invalid: Version without engine
        with pytest.raises(ValueError) as exc_info:
            RunRequest(
                workflow_params={},
                workflow_type="CWL",
                workflow_type_version="v1.0",
                workflow_url="https://example.com/workflow.cwl",
                workflow_engine_version="3.1.20220502201013"
            )
        assert "workflow_engine" in str(exc_info.value)

class TestWESData:
    """Test suite for WESData model"""

    def test_wes_data_minimal(self):
        """Test creating WESData with minimal fields"""
        wes_data = WESData(run_id="run-001")
        assert wes_data.run_id == "run-001"
        assert wes_data.request is None
        assert wes_data.state is None
        assert wes_data.run_log is None
        assert wes_data.task_logs_url is None
        assert wes_data.task_logs is None
        assert wes_data.outputs == {}

    def test_wes_data_complete(self):
        """Test creating WESData with all fields"""
        request = RunRequest(
            workflow_params={"input": "input.txt"},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url="https://example.com/workflow.cwl"
        )
        run_log = Log(
            name="workflow_run",
            cmd=["cwltool", "workflow.cwl", "inputs.json"],
            exit_code=0
        )
        task_log = TaskLog(
            id="task-001",
            name="data_processing"
        )
        
        wes_data = WESData(
            run_id="run-001",
            request=request,
            state=State.COMPLETE,
            run_log=run_log,
            task_logs_url="https://example.com/tasks",
            task_logs=[task_log],
            outputs={"result": "https://example.com/results/run-001.txt"}
        )
        
        assert wes_data.run_id == "run-001"
        assert wes_data.request == request
        assert wes_data.state == State.COMPLETE
        assert wes_data.run_log == run_log
        assert wes_data.task_logs_url == "https://example.com/tasks"
        assert wes_data.task_logs == [task_log]
        assert wes_data.outputs == {"result": "https://example.com/results/run-001.txt"}

    def test_task_logs_deprecation_warning(self):
        """Test deprecation warning when task_logs is used"""
        task_log = TaskLog(id="task-001", name="test")
        
        # Capture stdout to test the deprecation warning
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        WESData(
            run_id="run-001",
            task_logs=[task_log]
        )
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        assert "DeprecationWarning" in output
        assert "task_logs" in output
        assert "task_logs_url" in output  # Fixed: was 'tes_logs_url', should be 'task_logs_url'