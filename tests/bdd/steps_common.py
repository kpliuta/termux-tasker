from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pytest_bdd import given, then, when

from termux_tasker.runner_process import RunnerProcess, _parse_timeout  # noqa
from termux_tasker.runner_validator import RunnerValidator
from termux_tasker.task_validator import TaskValidator, TaskValidatorException

from termux_tasker.ui.base.screen import (
    ConfirmationScreen,
    FileBrowserScreen,
    InfoScreen,
    InputScreen,
    LoadingScreen,
    LogScreen,
)
from termux_tasker.ui.screens.main_menu import MainMenuScreen
from termux_tasker.ui.screens.runner_menu import RunnerMenuScreen
from termux_tasker.ui.screens.runners_screen import RunnersScreen
from termux_tasker.ui.screens.runner_type import RunnerTypeScreen
from termux_tasker.ui.screens.settings_screen import SettingsScreen
from termux_tasker.ui.screens.task_menu import TaskMenuScreen
from termux_tasker.ui.screens.task_type import TaskTypeScreen
from termux_tasker.ui.screens.tasks_menu import TasksMenuScreen

from tests.bdd.helpers import UIHelper
from tests.bdd.helpers import file_helper as _fs
from tests.bdd.helpers import settings_helper as _settings
from tests.bdd.helpers import validation_helper as _val

__all__ = [
    "UIHelper", "given", "then", "when",
    "Path", "pytest", "asyncio", "AsyncMock", "patch",
    "RunnerProcess", "_parse_timeout", "RunnerValidator",
    "TaskValidator", "TaskValidatorException",
    "ConfirmationScreen", "FileBrowserScreen", "InfoScreen",
    "InputScreen", "LoadingScreen", "LogScreen",
    "MainMenuScreen", "RunnerMenuScreen", "RunnersScreen",
    "RunnerTypeScreen", "SettingsScreen", "TaskMenuScreen",
    "TaskTypeScreen", "TasksMenuScreen",
    "ui", "settings", "fs", "val", "TEST_PROPERTIES",
]


from typing import Any


TEST_PROPERTIES = {"property-1": "value1", "property-2": "value2"}


def ui(pilot) -> UIHelper:
    return UIHelper(pilot)


def settings() -> Any:
    return _settings


def fs() -> Any:
    return _fs


def val() -> Any:
    return _val
