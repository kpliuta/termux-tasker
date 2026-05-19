from __future__ import annotations

from tests.bdd.steps_common import *  # noqa: F403, F401


@given("the app is launched with a given app version")
@given("the app is launched for the first time")
@given("the app is launched")
def given_app_launched(pilot) -> None:
    ui(pilot).pause(0.1)


@given("the main menu screen is shown")
@given("the main menu screen is shown again")
def given_main_menu(pilot) -> None:
    ui(pilot).assert_screen(MainMenuScreen)


@given("any screen is shown")
def given_any_screen(pilot) -> None:
    ui(pilot).pause(0.1)


@given("the Runners screen is shown")
def given_runners_screen(pilot) -> None:
    ui(pilot).nav_to_runners()
    ui(pilot).assert_screen(RunnersScreen)
    ui(pilot).pause(0.3)


@given("the Runner Type screen is shown")
def given_runner_type_screen(pilot) -> None:
    ui(pilot).nav_to_runners()
    ui(pilot).click_id("#install_runner")
    ui(pilot).assert_screen(RunnerTypeScreen)


@given("the Runner Type / Task Type screen is shown")
def given_type_screen(pilot) -> None:
    ui(pilot).nav_to_runners()
    ui(pilot).click_id("#install_runner")
    ui(pilot).assert_screen(RunnerTypeScreen)


@given("the Install Runner screen is shown for a git-based runner")
def given_install_runner_git(pilot) -> None:
    from termux_tasker.ui.screens.install_runner import InstallRunnerScreen

    given_runner_type_screen(pilot)
    ui(pilot).click_label("GitHub URL")
    ui(pilot).pause()
    ui(pilot).set_value("#input_field", "https://github.com/test/test-runner.git")
    ui(pilot).pause(0.1)
    ui(pilot).click_id("#ok")
    ui(pilot).assert_screen(InstallRunnerScreen)


@given("the Install Runner screen is shown for a local runner")
def given_install_runner_local(pilot) -> None:
    from termux_tasker.ui.screens.install_runner import InstallRunnerScreen

    given_runner_type_screen(pilot)
    ui(pilot).click_label("Local Storage")
    from tests.bdd.when_steps import when_select_folder
    when_select_folder(pilot)
    ui(pilot).assert_screen(InstallRunnerScreen)


@given("the Tasks screen is shown")
def given_tasks_screen(pilot) -> None:
    ui(pilot).nav_to_tasks()
    ui(pilot).assert_screen(TasksMenuScreen)


@given("the Runner Menu screen is shown")
@given("the Runner Menu screen is shown for a runner")
def given_runner_menu(pilot) -> None:
    ui(pilot).nav_to_runner_menu()
    ui(pilot).assert_screen(RunnerMenuScreen)


@given("the Task Menu screen is shown")
@given("the Task Menu screen is shown for a task")
@given("the Task Menu screen is shown for an installed task")
def given_task_menu(pilot) -> None:
    ui(pilot).nav_to_task_menu()
    ui(pilot).assert_screen(TaskMenuScreen)


@given("the Task Type screen is shown")
def given_task_type_screen(pilot) -> None:
    ui(pilot).nav_to_tasks()
    ui(pilot).click_id("#install_task")
    ui(pilot).assert_screen(TaskTypeScreen)


@given("the Settings screen is shown")
def given_settings_screen(pilot) -> None:
    ui(pilot).nav_to_settings()
    ui(pilot).assert_screen(SettingsScreen)


@given('any screen with a "Back" button (or similar close action)')
def given_screen_with_back(pilot) -> None:
    ui(pilot).nav_to_runners()
    ui(pilot).assert_screen(RunnersScreen)


@given("a MenuScreen with multiple buttons")
def given_menu_with_buttons(pilot) -> None:
    ui(pilot).assert_screen(MainMenuScreen)


@given("no runners are running")
def given_no_runners(pilot) -> None:
    ui(pilot).pause(0.1)


@given("at least one runner is running")
@given("the runner is enabled and running")
def given_runners_running(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().enable_runner(runner_dir)
    proc = RunnerProcess(
        runner_dir,
        ui(pilot).app.state.session_id,
        ui(pilot).app.state.tmp_dir,
    )
    ui(pilot).app.state.runners["sh_runner"] = proc


@given("there is at least one installed runner")
@given("a runner is already installed")
def given_installed_runner(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    assert runner_dir.exists()


@given("the runner is disabled")
def given_runner_disabled(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().disable_runner(runner_dir)


@given("a runner uninstall confirmation dialog is shown")
def given_uninstall_confirmation(pilot) -> None:
    ui(pilot).nav_to_runner_menu()
    ui(pilot).click_id("#uninstall")


@given('the runner state is "off"')
def given_runner_state_off(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    s = settings().load_runner_settings(runner_dir)
    assert s.session.state == "off"


@given('the runner state is not "off"')
def given_runner_state_not_off(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().set_runner_state(runner_dir, "initialization")


@given("a runner is enabled")
def given_runner_enabled_for_lifecycle(pilot) -> None:
    ui(pilot).nav_to_runner_menu()
    ui(pilot).click_id("#toggle")
    ui(pilot).pause()


@given("a runner was disabled before the app exited")
def given_runner_was_disabled(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().disable_runner(runner_dir)


@given("a runner is starting up")
def given_runner_starting(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().set_runner_state(runner_dir, "initialization")


@given("the runner metadata defines a property")
def given_runner_has_properties(pilot) -> None:
    meta = settings().load_runner_metadata(
        ui(pilot).app.state.runners_dir / "sh_runner"
    )
    assert len(meta.properties) > 0


@given("defined properties exist on the runner")
def given_runner_properties(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    for key, value in TEST_PROPERTIES.items():
        settings().set_runner_property(runner_dir, key, value)


@given('a runner is in "task-exec" state running a long task')
def given_runner_task_exec(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().enable_runner(runner_dir)
    settings().set_runner_state(runner_dir, "task-exec")


@given("a runner has running subprocesses")
def given_runner_with_procs(pilot) -> RunnerProcess:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    proc = RunnerProcess(
        runner_dir,
        "test-session",
        ui(pilot).app.state.tmp_dir,
    )
    proc.shutting_down = False
    proc._processes = [asyncio.create_subprocess_exec("true")]
    return proc


@given("the runner `sh_runner_malformed_no_exec` which has no `[exec]` section")
def given_malformed_runner_no_exec(pilot, app_state_fixture) -> Path:
    from tests.bdd.conftest import sh_runner_malformed_no_exec_dir as _fixture

    return _fixture


@given("there is at least one task installed")
@given("there is at least one installed task")
def given_installed_task(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    assert task_dir.exists()


@given("a task uninstall confirmation dialog is shown")
def given_task_uninstall_confirmation(pilot) -> None:
    ui(pilot).nav_to_task_menu()
    ui(pilot).click_id("#uninstall")


@given('the task state is "stopped"')
def given_task_stopped(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    s = settings().load_task_settings(task_dir)
    assert s.session.state == "stopped"


@given('the task state is not "stopped"')
def given_task_not_stopped(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    settings().set_task_state(task_dir, "running")
    settings().enable_task(task_dir)


@given("a runner is executing a command")
def given_runner_executing(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().enable_runner(runner_dir)
    settings().set_runner_state(runner_dir, "task-exec")


@given("a task is successfully installed")
def given_task_installed(pilot) -> None:
    from termux_tasker.ui.screens.task_menu import TaskMenuScreen

    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )

    def _push():
        ui(pilot).app.push_screen(TaskMenuScreen(task_dir))

    ui(pilot).app.call_from_thread(_push)
    ui(pilot).pause(0.3)


@given('a task is configured with `settings.general.timeout = "30s"`')
def given_timeout_30s(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    settings().set_task_timeout(task_dir, "30s")


@given("a runner has both enabled and disabled tasks")
def given_mixed_tasks(pilot) -> None:
    tasks_dir = ui(pilot).app.state.runners_dir / "sh_runner" / "tasks"

    enabled_dir = tasks_dir / "enabled_task"
    fs().ensure_directory(enabled_dir)
    fs().write_text(
        enabled_dir / "metadata.toml",
        "[general]\n"
        'id = "enabled_task"\n'
        'name = "Enabled Task"\n'
        'version = "1.0"\n'
        'runner_id = "sh_runner"\n'
        'runner_min_version = ">=1.1.0"\n'
        'default_timeout = "1m"\n',
    )
    settings().enable_task(enabled_dir)

    disabled_dir = tasks_dir / "disabled_task"
    fs().ensure_directory(disabled_dir)
    fs().write_text(
        disabled_dir / "metadata.toml",
        "[general]\n"
        'id = "disabled_task"\n'
        'name = "Disabled Task"\n'
        'version = "1.0"\n'
        'runner_id = "sh_runner"\n'
        'runner_min_version = ">=1.1.0"\n'
        'default_timeout = "1m"\n',
    )
    settings().disable_task(disabled_dir)


@given('a task specifies `runner_min_version = ">=10.1.0"`')
def given_incompatible_version(pilot) -> None:
    ui(pilot).pause(0.1)


@given('a task specifies `runner_min_version = ">=1.1.0,<2.0.0"`')
def given_compatible_version(pilot) -> None:
    ui(pilot).pause(0.1)


@given('the installed runner has version "1.1.0"')
@given("I selected a runner version to install")
@given("I selected a git tag to install")
@given("the Install Runner Version screen is shown")
def given_version_selected(pilot) -> None:
    ui(pilot).pause(0.1)


@given(
    "the task `sh_runner_task_malformed_wrong_runner_version` "
    'with `runner_min_version = ">=10.1.0"`'
)
def given_task_wrong_version(pilot, app_state_fixture) -> Path:
    from tests.bdd.conftest import sh_runner_task_wrong_version_dir as _fixture

    return _fixture


@given(
    "the task `sh_runner_task_malformed_no_required_file` "
    "which has no `required_file`"
)
def given_task_no_required_file(pilot, app_state_fixture) -> Path:
    from tests.bdd.conftest import sh_runner_task_no_required_file_dir as _fixture

    return _fixture


@given("I am installing a runner where all properties have defaults or are optional")
@given("the property is non-optional")
def given_property_meta(pilot) -> None:
    ui(pilot).pause(0.1)


@given("I am installing a runner with non-optional properties without defaults")
def given_runner_non_optional(pilot, tmp_dir: Path) -> None:
    """Jump to property prompt state for a runner install with 2 required properties."""
    from tests.bdd.conftest import RUNNER_REQUIRED_META, _write_runner
    from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen
    from termux_tasker.ui.base.screen import InputScreen
    import uuid

    folder = _write_runner(tmp_dir / f"_test_{uuid.uuid4().hex}", RUNNER_REQUIRED_META)
    screen = InstallRunnerVersionScreen(folder)
    ui(pilot).push_screen(screen)
    ui(pilot).pause(0.3)

    ui(pilot).pilot_driver._submit(
        lambda p: screen._finalize_install("test_runner", "1.0.0", "install")
    )
    ui(pilot).wait_until_screen(InputScreen, timeout=5)


@given("I am installing a task with non-optional properties without defaults")
def given_task_non_optional(pilot, tmp_dir: Path) -> None:
    """Jump to property prompt state for a task install with 2 required properties."""
    from tests.bdd.conftest import TASK_REQUIRED_META, _write_task
    from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen
    from termux_tasker.ui.base.screen import InputScreen
    import uuid

    folder = _write_task(tmp_dir / f"_test_{uuid.uuid4().hex}", TASK_REQUIRED_META)
    runner_dir = pilot.app.state.runners_dir / "sh_runner"
    screen = InstallTaskVersionScreen(runner_dir, folder)
    ui(pilot).push_screen(screen)
    ui(pilot).pause(0.3)

    ui(pilot).pilot_driver._submit(
        lambda p: screen._finalize_install("test_task", "1.0.0", "install")
    )
    ui(pilot).wait_until_screen(InputScreen, timeout=5)


@given("a LogScreen is opened with a file path")
def given_log_screen_file(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "test.log"
    fs().write_text(log_file, "line 1\nline 2\nline 3\n")
    ui(pilot).push_log_screen(log_file, follow=False)
    ui(pilot).assert_screen(LogScreen)


@given("a LogScreen is opened with follow mode enabled")
def given_log_screen_follow(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    fs().write_text(log_file, "existing content\n")
    ui(pilot).push_log_screen(log_file, follow=True)
    ui(pilot).assert_screen(LogScreen)


@given("there is existing content in the file")
def given_existing_content(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    if not log_file.exists():
        fs().write_text(log_file, "existing content\n")


@given("content is displayed")
def given_content_displayed(pilot) -> None:
    ui(pilot).assert_screen(LogScreen)


@given("a LogScreen is shown")
def given_log_screen_shown(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "simple.log"
    fs().write_text(log_file, "content\n")
    ui(pilot).push_log_screen(log_file, follow=False)
    ui(pilot).assert_screen(LogScreen)


@given("a LogScreen is opened with a TOML file containing `[section]` headers")
def given_toml_log(pilot) -> None:
    toml_file = ui(pilot).app.state.work_dir / "test.toml"
    fs().write_text(toml_file, '[general]\nname = "test"\nversion = "1.0"\n')
    ui(pilot).push_log_screen(toml_file, follow=True)
    ui(pilot).assert_screen(LogScreen)


@given("a confirmation dialog is shown for exiting with running runners")
def given_exit_confirmation(pilot) -> None:
    given_runners_running(pilot)
    ui(pilot).click_id("#exit")
