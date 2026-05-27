from __future__ import annotations

from tests.bdd.steps_common import *  # noqa


@given("the app is launched for the first time")
def given_app_launched(pilot) -> None:
    app = pilot.app
    assert app.state.work_dir.exists()
    assert app.state.runners_path.exists()
    assert app.state.tmp_dir.exists()
    assert app.state.app_config_file.exists()


@given("the main menu screen is shown")
@given("the main menu screen is shown again")
def given_main_menu(pilot) -> None:
    ui(pilot).assert_screen(MainMenuScreen)


@given("any screen is shown")
def given_any_screen(pilot) -> None:
    ui(pilot).assert_screen(MainMenuScreen)


@given("the Runners screen is shown")
def given_runners_screen(pilot) -> None:
    ui(pilot).nav_to_runners()
    ui(pilot).assert_screen(RunnersScreen)


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
    assert len(ui(pilot).app.state.runners) == 0


@given("at least one runner is running")
@given("the runner is enabled and running")
def given_runners_running(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().enable_runner(runner_path)
    proc = RunnerProcess(
        runner_path,
        ui(pilot).app.state.session_id,
        ui(pilot).app.state.tmp_dir,
    )
    ui(pilot).app.state.runners["sh_runner"] = proc


@given("there is at least one installed runner")
@given("a runner is already installed")
def given_installed_runner(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert runner_path.exists()


@given("the runner is disabled")
def given_runner_disabled(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().disable_runner(runner_path)


@given("a runner uninstall confirmation dialog is shown")
def given_uninstall_confirmation(pilot) -> None:
    ui(pilot).nav_to_runner_menu()
    ui(pilot).click_id("#uninstall")


@given('the runner state is "off"')
def given_runner_state_off(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "off"


@given('the runner state is not "off"')
def given_runner_state_not_off(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "initialization")


@given("a runner is enabled")
def given_runner_enabled_for_lifecycle(pilot) -> None:
    ui(pilot).nav_to_runner_menu()
    ui(pilot).click_id("#toggle")
    ui(pilot).pause()


@given("a runner was disabled before the app exited")
def given_runner_was_disabled(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().disable_runner(runner_path)


@given("the runner metadata defines a property")
def given_runner_has_properties(pilot) -> None:
    meta = settings().load_runner_metadata(
        ui(pilot).app.state.runners_path / "sh_runner"
    )
    assert len(meta.properties) > 0


@given("there is at least one task installed")
@given("there is at least one installed task")
def given_installed_task(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    assert task_path.exists()


@given("a task uninstall confirmation dialog is shown")
def given_task_uninstall_confirmation(pilot) -> None:
    ui(pilot).nav_to_task_menu()
    ui(pilot).click_id("#uninstall")


@given('the task state is "stopped"')
def given_task_stopped(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    s = settings().load_task_settings(task_path)
    assert s.session.state == "stopped"


@given('the task state is not "stopped"')
def given_task_not_stopped(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    settings().set_task_state(task_path, "running")
    settings().enable_task(task_path)


@given("a runner is executing a command")
def given_runner_executing(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().enable_runner(runner_path)
    settings().set_runner_state(runner_path, "task-exec")


@given("a task is successfully installed")
def given_task_installed(pilot) -> None:
    from termux_tasker.ui.screens.task_menu import TaskMenuScreen

    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )

    def _push():
        ui(pilot).app.push_screen(TaskMenuScreen(task_path))

    ui(pilot).app.call_from_thread(_push)
    ui(pilot).pause(0.1)


@given('a task is configured with `settings.general.timeout = "30s"`')
def given_timeout_30s(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    settings().set_task_timeout(task_path, "30s")


@given("a runner has both enabled and disabled tasks")
def given_mixed_tasks(pilot) -> None:
    tasks_path = ui(pilot).app.state.runners_path / "sh_runner" / "tasks"

    enabled_dir = tasks_path / "enabled_task"
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

    disabled_dir = tasks_path / "disabled_task"
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


@given("I selected a runner version to install")
@given("I selected a git tag to install")
@given("the Install Runner Version screen is shown")
def given_version_selected(pilot) -> None:
    from termux_tasker.ui.screens.install_runner import InstallRunnerScreen
    from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen
    given_runner_type_screen(pilot)
    ui(pilot).click_label("GitHub URL")
    ui(pilot).pause()
    ui(pilot).set_value("#input_field", "https://github.com/test/test-runner.git")
    ui(pilot).pause(0.1)
    ui(pilot).click_id("#ok")
    ui(pilot).assert_screen(InstallRunnerScreen)
    ui(pilot).click_label("Install")
    ui(pilot).pause(0.4)
    ui(pilot).assert_screen(InstallRunnerVersionScreen)


@given("I am installing a runner where all properties have defaults or are optional")
def given_runner_optional_properties(pilot, optional_runner_path: Path) -> None:
    from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen

    screen = InstallRunnerVersionScreen(optional_runner_path)
    ui(pilot).push_screen(screen)
    ui(pilot).pause(0.1)


@given("the property is non-optional")
def given_property_non_optional(pilot) -> None:
    meta = settings().load_runner_metadata(
        ui(pilot).app.state.runners_path / "sh_runner"
    )
    non_optional = [p for p in meta.properties if not p.optional]
    assert len(non_optional) > 0


@given("I am installing a runner with non-optional properties without defaults")
def given_runner_non_optional(pilot, runner_required_dir: Path) -> None:
    from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen
    from termux_tasker.ui.base.screen import InputScreen

    screen = InstallRunnerVersionScreen(runner_required_dir)
    ui(pilot).push_screen(screen)
    ui(pilot).pause(0.1)

    ui(pilot).pilot_driver.run_on_pilot(
        lambda p: screen._finalize_install("test_runner", "1.0.0", "install")   # noqa
    )
    ui(pilot).wait_until_screen(InputScreen, timeout=5)


@given("I am installing a task with non-optional properties without defaults")
def given_task_non_optional(pilot, task_required_dir: Path) -> None:
    from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen
    from termux_tasker.ui.base.screen import InputScreen

    runner_path = pilot.app.state.runners_path / "sh_runner"
    screen = InstallTaskVersionScreen(runner_path, task_required_dir)
    ui(pilot).push_screen(screen)
    ui(pilot).pause(0.1)

    ui(pilot).pilot_driver.run_on_pilot(
        lambda p: screen._finalize_install("test_task", "1.0.0", "install") # noqa
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

@given("the output directory exists")
def given_output_dir_exists(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    output_dir = task_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)


@given("the output directory exists and contains files")
def given_output_dir_has_files(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    output_dir = task_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.txt").write_text("test output")
    (output_dir / "logs").mkdir()


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
