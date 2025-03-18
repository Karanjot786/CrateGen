"""Tests for WES models"""
import io
import sys

import pytest

from crategen.models.wes_models import (
    WESData,
    WESLog,
    WESOutputs,
    WESRunRequest,
    WESState,
    WESTaskLog,
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

test_url = "https://raw.githubusercontent.com/elixir-cloud-aai/CrateGen/refs/heads/main/README.md"

MAX_SYSTEM_LOGS = 2

# Test data samples
test_workflow_params = {
    "reads": f"{test_url}/reads.fastq",
    "reference": f"{test_url}/reference.fa",
    "output_dir": f"{test_url}/results/"
}

test_workflow_engine_params = {
    "memory": "16GB",
    "cpu": "4",
    "disk_size": "100GB"
}

test_tags = {
    "project": "genomics-pipeline",
    "sample": "TCGA-AB-2823",
    "analysis": "variant-calling"
}


class TestWESState:
    """Test suite for WESState enum"""

    def test_state_enum_values(self):
        """Test that WESState enum has correct values"""
        assert WESState.UNKNOWN == "UNKNOWN"
        assert WESState.QUEUED == "QUEUED"
        assert WESState.INITIALIZING == "INITIALIZING"
        assert WESState.RUNNING == "RUNNING"
        assert WESState.PAUSED == "PAUSED"
        assert WESState.COMPLETE == "COMPLETE"
        assert WESState.EXECUTOR_ERROR == "EXECUTOR_ERROR"
        assert WESState.SYSTEM_ERROR == "SYSTEM_ERROR"
        assert WESState.CANCELLED == "CANCELLED"
        assert WESState.CANCELING == "CANCELING"
        assert WESState.PREEMPTED == "PREEMPTED"


class TestWESOutputs:
    """Test suite for WESOutputs model"""

    def test_wes_outputs_creation(self):
        """Test creating WESOutputs objects"""
        # Test with real URLs
        outputs = WESOutputs(
            location="https://storage.googleapis.com/workflow-outputs/run123/result.bam",
            name="alignment.bam"
        )
        assert outputs.location.startswith("https://")
        assert outputs.name == "alignment.bam"
        
        # Test with different output types
        outputs = WESOutputs(
            location="https://storage.googleapis.com/workflow-outputs/run123/variants.vcf",
            name="variants.vcf"
        )
        assert "variants.vcf" in outputs.location
        assert outputs.name.endswith(".vcf")


class TestWESLog:
    """Test suite for WESLog model"""

    def test_log_creation_with_minimal_fields(self):
        """Test creating WESLog with minimal fields"""
        log = WESLog()
        assert log.name is None
        assert log.cmd is None
        assert log.start_time is None
        assert log.end_time is None
        assert log.stdout is None
        assert log.stderr is None
        assert log.exit_code is None
        assert log.system_logs is None

    @pytest.mark.parametrize("valid_datetime", valid_datetime_strings)
    def test_log_creation_with_all_fields(self, valid_datetime):
        """Test creating WESLog with all fields"""
        log = WESLog(
            name="workflow_123",
            cmd=["cwltool", "--non-strict", test_url, test_url],
            start_time=valid_datetime,
            end_time=valid_datetime,
            stdout="https://storage.googleapis.com/workflow-logs/run123/stdout.log",
            stderr="https://storage.googleapis.com/workflow-logs/run123/stderr.log",
            exit_code=0,
            system_logs=[
                "Workflow engine initialized",
                "Downloading CWL workflow from GitHub",
                "Execution completed successfully"
            ]
        )
        assert log.name == "workflow_123"
        assert test_url in log.cmd
        assert log.stdout.startswith("https://")
        assert log.stderr.startswith("https://")
        assert log.exit_code == 0
        assert len(log.system_logs) == MAX_SYSTEM_LOGS

    @pytest.mark.parametrize("invalid_datetime", invalid_datetime_strings)
    def test_log_datetime_validation(self, invalid_datetime):
        """Test datetime validation in WESLog"""
        with pytest.raises(ValueError) as exc_info:
            WESLog(
                name="workflow_123",
                start_time=invalid_datetime
            )
        assert "format" in str(exc_info.value)


class TestWESTaskLog:
    """Test suite for WESTaskLog model"""

    def test_task_log_creation(self):
        """Test creating WESTaskLog objects"""
        # Test with required fields and real URLs
        task_log = WESTaskLog(
            id="task-bwa-mem-123",
            name="bwa_mem_alignment",
            cmd=["bwa", "mem", "-t", "4", "reference.fa", "reads.fastq"],
            stdout="https://storage.googleapis.com/workflow-logs/task123/stdout.log",
            stderr="https://storage.googleapis.com/workflow-logs/task123/stderr.log",
            exit_code=0,
            tes_uri=test_url
        )
        assert task_log.id.startswith("task-")
        assert task_log.name == "bwa_mem_alignment"
        assert task_log.stdout.startswith("https://")
        assert task_log.stderr.startswith("https://")
        assert task_log.tes_uri == test_url

    def test_task_log_name_required(self):
        """Test that name is required for WESTaskLog"""
        with pytest.raises(ValueError):
            WESTaskLog(id="task-123")


class TestWESRunRequest:
    """Test suite for WESRunRequest model"""

    def test_run_request_minimal(self):
        """Test creating WESRunRequest with minimal fields"""
        request = WESRunRequest(
            workflow_params={
                "input_reads": "https://storage.googleapis.com/sample-data/reads.fastq",
                "output_path": "s3://my-bucket/results/"
            },
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url=test_url
        )
        assert request.workflow_type == "CWL"
        assert request.workflow_url == test_url
        assert request.workflow_params["input_reads"].startswith("https://")
        assert request.workflow_params["output_path"].startswith("s3://")

    def test_run_request_all_fields(self):
        """Test creating WESRunRequest with all fields"""
        request = WESRunRequest(
            workflow_params={
                "reads": "https://storage.googleapis.com/sample-data/tumor.bam",
                "reference": "https://storage.googleapis.com/references/hg38.fa",
                "output_dir": "s3://my-bucket/variant-calls/"
            },
            workflow_type="WDL",
            workflow_type_version="1.0",
            workflow_url="https://raw.githubusercontent.com/broadinstitute/gatk-workflows/master/mutect2.wdl",
            tags={
                "project": "cancer-genomics",
                "sample": "TCGA-AB-2823",
                "analysis": "somatic-variant-calling"
            },
            workflow_engine_parameters={
                "memory": "16GB",
                "cpu": "4",
                "disk_size": "100GB"
            },
            workflow_engine="cromwell",
            workflow_engine_version="52.0.1"
        )
        assert request.workflow_type == "WDL"
        assert request.workflow_url.endswith(".wdl")
        assert request.tags["project"] == "cancer-genomics"
        assert request.workflow_engine == "cromwell"

    def test_workflow_engine_validation(self):
        """Test workflow engine validation rules"""
        # Valid: No version specified
        request = WESRunRequest(
            workflow_params={},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url=test_url
        )
        assert request.workflow_engine is None
        assert request.workflow_engine_version is None

        # Valid: Both engine and version specified
        request = WESRunRequest(
            workflow_params={},
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url=test_url,
            workflow_engine="cwltool",
            workflow_engine_version="3.1.20220502201013"
        )
        assert request.workflow_engine == "cwltool"
        assert request.workflow_engine_version.startswith("3.1")

        # Invalid: Version without engine
        with pytest.raises(ValueError) as exc_info:
            WESRunRequest(
                workflow_params={},
                workflow_type="CWL",
                workflow_type_version="v1.0",
                workflow_url=test_url,
                workflow_engine_version="3.1.20220502201013"
            )
        assert "workflow_engine" in str(exc_info.value)

class TestWESData:
    """Test suite for WESData model"""

    def test_wes_data_minimal(self):
        """Test creating WESData with minimal fields"""
        wes_data = WESData(run_id="wes-run-123")
        assert wes_data.run_id.startswith("wes-")
        assert wes_data.request is None
        assert wes_data.state is None
        assert wes_data.run_log is None
        assert wes_data.task_logs_url is None
        assert wes_data.task_logs is None
        assert wes_data.outputs == {}

    def test_wes_data_complete(self):
        """Test creating WESData with all fields"""
        request = WESRunRequest(
            workflow_params={
                "reads": "https://storage.googleapis.com/sample-data/sample.fastq",
                "output_dir": "s3://my-bucket/results/"
            },
            workflow_type="CWL",
            workflow_type_version="v1.0",
            workflow_url=test_url
        )
        
        run_log = WESLog(
            name="variant_calling_workflow",
            cmd=["cwltool", "--non-strict", test_url, test_url],
            stdout="https://storage.googleapis.com/workflow-logs/run123/stdout.log",
            stderr="https://storage.googleapis.com/workflow-logs/run123/stderr.log",
            exit_code=0,
            system_logs=["Workflow started", "Workflow completed"]
        )
        
        task_log = WESTaskLog(
            id="task-123",
            name="variant_calling",
            cmd=["gatk", "HaplotypeCaller", "-R", "reference.fa", "-I", "input.bam"],
            stdout="https://storage.googleapis.com/workflow-logs/task123/stdout.log",
            stderr="https://storage.googleapis.com/workflow-logs/task123/stderr.log",
            exit_code=0,
            tes_uri=test_url
        )
        
        wes_data = WESData(
            run_id="wes-run-123",
            request=request,
            state=WESState.COMPLETE,
            run_log=run_log,
            task_logs_url="https://storage.googleapis.com/workflow-logs/run123/tasks/",
            task_logs=[task_log],
            outputs={
                "aligned_bam": "https://storage.googleapis.com/workflow-outputs/run123/aligned.bam",
                "variants_vcf": "https://storage.googleapis.com/workflow-outputs/run123/variants.vcf"
            }
        )
        
        assert wes_data.run_id == "wes-run-123"
        assert wes_data.request == request
        assert wes_data.state == WESState.COMPLETE
        assert wes_data.run_log == run_log
        assert wes_data.task_logs_url.startswith("https://")
        assert wes_data.task_logs == [task_log]
        assert all(url.startswith("https://") for url in wes_data.outputs.values())

    def test_task_logs_deprecation_warning(self):
        """Test deprecation warning when task_logs is used"""
        task_log = WESTaskLog(
            id="task-123",
            name="alignment",
            cmd=["bwa", "mem", "ref.fa", "reads.fastq"],
            stdout="https://storage.googleapis.com/logs/task123/stdout.log",
            stderr="https://storage.googleapis.com/logs/task123/stderr.log",
            exit_code=0
        )
        
        # Capture stdout to test the deprecation warning
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        WESData(
            run_id="wes-run-123",
            task_logs=[task_log]
        )
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        assert "DeprecationWarning" in output
        assert "task_logs" in output
        assert "task_logs_url" in output
