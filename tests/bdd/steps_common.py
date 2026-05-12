from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pytest_bdd import given, then, when

from termux_tasker.runner_process import RunnerProcess, _parse_timeout
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

from tests.bdd.helpers import FileSystemHelper, SettingsHelper, UIHelper, ValidationHelper

TEST_PROPERTIES = {"property-1": "value1", "property-2": "value2"}


def ui(pilot) -> UIHelper:
    return UIHelper(pilot)


def settings() -> SettingsHelper:
    return SettingsHelper()


def fs() -> FileSystemHelper:
    return FileSystemHelper()


def val() -> ValidationHelper:
    return ValidationHelper()
