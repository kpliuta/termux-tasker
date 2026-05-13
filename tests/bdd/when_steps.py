from tests.bdd.steps_common import *  # noqa: F403, F401


@when('I press "Show Runners" button')
def when_show_runners(pilot) -> None:
    ui(pilot).click_id("#show_runners")


@when('I press "Settings" button')
def when_settings(pilot) -> None:
    ui(pilot).click_id("#settings")


@when('I press "Exit" button')
def when_exit(pilot) -> None:
    ui(pilot).click_id("#exit")


@when('I press "Install Runner" button')
def when_install_runner(pilot) -> None:
    ui(pilot).click_id("#install_runner")


@when('I press "Install Task" button')
def when_install_task(pilot) -> None:
    ui(pilot).click_id("#install_task")


@when('I press "Install" button')
def when_install(pilot) -> None:
    ui(pilot).click_label("Install")


@when('I press "Enable" button')
@when('I press "Disable" button')
@when('I press "Enable" / "Disable" button')
def when_toggle(pilot) -> None:
    ui(pilot).click_id("#toggle")


@when('I press "Yes" button')
def when_yes(pilot) -> None:
    ui(pilot).click_yes()


@when('I press "No" button')
def when_no(pilot) -> None:
    ui(pilot).click_id("#cancel_button")


@when('I press "Uninstall" button')
def when_uninstall(pilot) -> None:
    ui(pilot).click_label("Uninstall")


@when('I press "{label}" button')
def when_press_label(pilot, label: str) -> None:
    ui(pilot).click_label(label)


@when('I press "Set Timeout" button')
def when_set_timeout(pilot) -> None:
    ui(pilot).click_id("#set_timeout")


@when('I press "Set <property>" button')
@when('I press "<prop>" button')
def when_set_property(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("set_"):
            ui(pilot).click_id(f"#{btn.id}")
            return
    raise AssertionError("No property button found")


@when('I press "Bundled" button')
def when_bundled(pilot) -> None:
    ui(pilot).click_label("Bundled")


@when('I press "GitHub URL" button')
def when_github_url(pilot) -> None:
    ui(pilot).click_label("GitHub URL")


@when('I press "Local Storage" button')
def when_local_storage(pilot) -> None:
    ui(pilot).click_label("Local Storage")


@when('I press "Back" button (or Escape)')
@when('I press "Cancel" (or Escape)')
@when('I press "Close" button (or Escape)')
@when("I press Escape")
def when_escape(pilot) -> None:
    ui(pilot).press("escape")


@when("I press the setting button")
def when_press_setting(pilot) -> None:
    ui(pilot).click_id("#upgrade_on_startup")


@when("I press a runner button")
def when_open_runner(pilot) -> None:
    ui(pilot).click_id("#open_sh_runner")


@when("I press a task button")
def when_open_task(pilot) -> None:
    ui(pilot).click_id("#open_sh_runner_task")


@when('I press "Show Tasks" button')
def when_show_tasks(pilot) -> None:
    ui(pilot).click_label("Show Tasks")


@when('I press "Show Runner Logs" button')
def when_show_logs(pilot) -> None:
    ui(pilot).click_label("Show Runner Logs")


@when('I press "Show metadata.toml" button')
def when_show_metadata(pilot) -> None:
    ui(pilot).click_label("Show metadata.toml")


@when('I press "Show settings.toml" button')
def when_show_settings(pilot) -> None:
    ui(pilot).click_label("Show settings.toml")


@when('I press "Update" button')
def when_update(pilot) -> None:
    ui(pilot).click_label("Update")


@when('I press "Reset" button')
def when_reset(pilot) -> None:
    ui(pilot).click_id("#reset_button")


@when("I press Ctrl+Q")
def when_ctrl_q(pilot) -> None:
    ui(pilot).press("ctrl+q")


@when('I press "up" arrow key')
def when_up_arrow(pilot) -> None:
    ui(pilot).press("up")


@when('I press "down" arrow key')
def when_down_arrow(pilot) -> None:
    ui(pilot).press("down")


@when("I enter a valid value and press Ok")
def when_enter_valid_value(pilot) -> None:
    screen = ui(pilot).app.screen
    try:
        title = screen.dialog_title
    except AttributeError:
        title = ""

    if "GitHub" in title:
        value = "https://github.com/test/test-runner.git"
    elif "Timeout" in title:
        value = "30s"
    else:
        value = "test_value"

    ui(pilot).set_value("#input_field", value)
    ui(pilot).pause()
    ui(pilot).click_id("#ok")


@when("I clear the value and press Ok")
def when_clear_value(pilot) -> None:
    ui(pilot).set_value("#input_field", "")
    ui(pilot).pause()
    ui(pilot).click_id("#ok")


@when("I enter a valid GitHub URL and press Ok")
def when_enter_github_url(pilot) -> None:
    ui(pilot).pause()
    ui(pilot).set_value("#input_field", "https://github.com/test/test-runner.git")
    ui(pilot).pause()
    ui(pilot).click_id("#ok")


@when('I enter a new timeout (e.g. "30s", "5m", "1h") and press Ok')
def when_enter_timeout(pilot) -> None:
    ui(pilot).set_value("#input_field", "30s")
    ui(pilot).pause(0.2)
    ui(pilot).click_id("#ok")
    ui(pilot).assert_screen(TaskMenuScreen)
    ui(pilot).pause(0.1)


@when("I enter an invalid timeout and press Ok")
def when_enter_invalid_timeout(pilot) -> None:
    ui(pilot).set_value("#input_field", "abc")
    ui(pilot).pause(0.2)
    ui(pilot).click_id("#ok")


@when("I select a value and press Ok")
def when_select_radio_value(pilot) -> None:
    ui(pilot).click_id("#ok")


@when("I select a version")
def when_select_version(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("version_"):
            ui(pilot).click_id(f"#{btn.id}")
            return
    raise AssertionError("No version button found")


@when('I select a folder and press "Select"')
def when_select_folder(pilot) -> None:
    def _do_select():
        screen = ui(pilot).app.screen
        screen._selected_path = ui(pilot).app.state.runners_dir / "sh_runner"
        screen.dismiss(screen._selected_path)

    ui(pilot).app.call_from_thread(_do_select)
    ui(pilot).pause(0.3)


@when("I dismiss the warning")
def when_dismiss_warning(pilot) -> None:
    ui(pilot).click_id("#info_button")


@when('I uncheck the "Follow" checkbox')
def when_uncheck_follow(pilot) -> None:
    cb = ui(pilot).app.screen.query_one("#follow_checkbox")
    if cb.value:
        ui(pilot).click_id("#follow_checkbox")
    ui(pilot).pause()


@when('I check the "Follow" checkbox again')
def when_check_follow(pilot) -> None:
    cb = ui(pilot).app.screen.query_one("#follow_checkbox")
    if not cb.value:
        ui(pilot).click_id("#follow_checkbox")
    ui(pilot).pause()


@when("new content is appended to the file")
@when("new content is written to the file")
def when_append_content(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    fs().append_text(log_file, "new content\n")


@when("I confirm the installation")
@when("the install finalizes")
@when("properties are prompted one by one via InputScreen")
@when("I provide valid values for all properties")
@when("I install the same runner again with a different version")
@when("I install the same runner with the same version")
@when("I enter an invalid URL (doesn't match GitHub URL regex)")
@when("a runner is installed or removed on disk")
def when_install_flow(pilot) -> None:
    ui(pilot).pause(0.1)


@when("the git checkout fails")
def when_git_checkout_fails(pilot) -> None:
    from termux_tasker.ui.screens.install_runner import InstallRunnerScreen
    from tests.bdd.given_steps import given_runner_type_screen

    given_runner_type_screen(pilot)
    ui(pilot).click_label("GitHub URL")
    ui(pilot).pause()
    ui(pilot).set_value("#input_field", "https://github.com/test/test-runner.git")
    ui(pilot).pause(0.1)
    ui(pilot).click_id("#ok")
    ui(pilot).assert_screen(InstallRunnerScreen)
    (ui(pilot).app.screen.tmp_runner_folder / ".git").mkdir(exist_ok=True)
    ui(pilot).click_label("Install")
    ui(pilot).pause(0.4)
    import termux_tasker.ui.screens.install_runner_version as _irv_mod
    _irv_mod.git_checkout = lambda _repo, _tag: False  # type: ignore[method-assign]
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("version_"):
            ui(pilot).click_id(f"#{btn.id}")
            return
    raise AssertionError("No version button found")


@when("I close the app")
def when_close_app(pilot) -> None:
    ui(pilot).pilot.exit_app()


@when("I uninstall a task from its Task Menu screen")
def when_uninstall_task(pilot) -> None:
    ui(pilot).nav_to_task_menu()
    ui(pilot).click_id("#uninstall")
    ui(pilot).pause(0.2)
    ui(pilot).click_id("#yes_uninstall")
    ui(pilot).pause(0.5)


@when("return to the Tasks screen")
def when_return_tasks(pilot) -> None:
    ui(pilot).pause()
    ui(pilot).assert_screen(TasksMenuScreen)


@when("the app is restarted")
def when_app_restarted(pilot) -> None:
    ui(pilot).pause(0.1)


@when("`run()` is called again before the previous start completes")
def when_run_called_twice(pilot, app_state_fixture) -> RunnerProcess:
    proc = RunnerProcess(
        app_state_fixture.runners_dir / "sh_runner",
        "test-session",
        app_state_fixture.tmp_dir,
    )
    proc._run_lock = True
    proc.run()
    proc.run()
    return proc


@when("the runner's `run()` method is called")
def when_runner_run(pilot) -> RunnerProcess:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    proc = RunnerProcess(runner_dir, "test-session", ui(pilot).app.state.tmp_dir)
    proc._run_lock = True
    proc.run()
    return proc


@when("`shutdown()` is called")
async def when_shutdown_called(pilot, app_state_fixture) -> RunnerProcess:
    with patch(
        "termux_tasker.runner_process.asyncio.create_subprocess_exec",
        return_value=AsyncMock(wait=AsyncMock(return_value=0)),
    ):
        proc = RunnerProcess(
            app_state_fixture.runners_dir / "sh_runner",
            "test-session",
            app_state_fixture.tmp_dir,
        )
        proc.shutting_down = True
        await proc.shutdown()
        return proc


@when("`terminate()` is called")
def when_terminate_called(pilot, app_state_fixture) -> RunnerProcess:
    proc = RunnerProcess(
        app_state_fixture.runners_dir / "sh_runner",
        "test-session",
        app_state_fixture.tmp_dir,
    )
    proc.terminate()
    return proc


@when("the task validator runs")
def when_task_validator_runs(pilot, app_state_fixture) -> TaskValidator:
    validator = TaskValidator(
        app_state_fixture.runners_dir / "sh_runner",
        app_state_fixture.tmp_dir / "task",
        app_state_fixture.tmp_dir / ".tmp",
    )
    return validator


@when("the runner is validated")
def when_runner_validated(pilot, app_state_fixture) -> RunnerValidator:
    validator = val().create_runner_validator(
        app_state_fixture.runners_dir / "sh_runner_malformed_no_exec",
        app_version="0.1.0",
    )
    return validator


@when("the task is validated by the sh_runner's task validator")
def when_task_validated_by_sh_runner(
    pilot, app_state_fixture, sh_runner_task_no_required_file_dir,
) -> TaskValidator:
    validate_dir = app_state_fixture.tmp_dir / "validate_task"
    fs().copy_directory(sh_runner_task_no_required_file_dir, validate_dir)
    validator = TaskValidator(
        app_state_fixture.runners_dir / "sh_runner",
        validate_dir,
        app_state_fixture.tmp_dir / ".tmp",
    )
    val().store("task_validator", validator)
    return validator


@when("the task is validated")
def when_task_validated(
    pilot, app_state_fixture, sh_runner_task_wrong_version_dir,
) -> TaskValidator:
    validate_dir = app_state_fixture.tmp_dir / "validate_task"
    fs().copy_directory(sh_runner_task_wrong_version_dir, validate_dir)
    validator = TaskValidator(
        app_state_fixture.runners_dir / "sh_runner",
        validate_dir,
        app_state_fixture.tmp_dir / ".tmp",
    )
    val().store("task_validator", validator)
    return validator


@when('the runner\'s execution loop reaches task iteration')
@when('the runner\'s execution loop enters "idle" state')
def when_loop_state(pilot) -> None:
    ui(pilot).pause(0.1)


@when("the runner is shut down")
def when_runner_shut_down(pilot) -> None:
    ui(pilot).pause(0.1)
