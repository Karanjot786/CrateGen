"""Models package for TES, WES, and WRROC.

This package contains Pydantic models that conform to the GA4GH schemas for Task Execution Services (TES),
Workflow Execution Services (WES), and WRROC. These models are used for data validation and type safety
throughout the CrateGen project.
"""

from .tes_models import (
    TESData,
    TESExecutor,
    TESExecutorLog,
    TESFileType,
    TESInput,
    TESOutput,
    TESOutputFileLog,
    TESResources,
    TESState,
    TESTaskLog,
)
from .wes_models import (
<<<<<<< HEAD
    State,
    WESOutputs,
    Log,
    TaskLog,
    RunRequest,
    WESData,
=======
    WESData,
    WESLog,
    WESOutputs,
    WESRunRequest,
    WESState,
    WESTaskLog,
>>>>>>> e2e7014 (feat: add WES models with unit tests)
)

__all__ = [
    # TES Models
    "TESData",
    "TESInput",
    "TESOutput",
    "TESExecutor",
    "TESTaskLog",
    "TESResources",
    "TESExecutorLog",
    "TESOutputFileLog",
    "TESFileType",
    "TESState",
    
    # WES Models
<<<<<<< HEAD
    "State",
    "WESOutputs",
    "Log",
    "TaskLog", 
    "RunRequest",
=======
    "WESState",
    "WESOutputs",
    "WESLog",
    "WESTaskLog", 
    "WESRunRequest",
>>>>>>> e2e7014 (feat: add WES models with unit tests)
    "WESData",
]
