from __future__ import annotations

import shutil

import termux_tasker.ui.screens.install_runner_version as _irv_mod  # noqa

from tests.bdd.steps_common import *  # noqa


@when('I press "Show Runners" button')
def when_show_runners(pilot) -> None:
    ui(pilot).click_id("#show_runners")


@when('I press "Settings" button')
def when_settings(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    else:
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
    ui(pilot).wait_until_screen(ConfirmationScreen)


@when('I press "{label}" button')
def when_press_label(pilot, label: str) -> None:
    ui(pilot).click_label(label)


@when('I press "Set Timeout" button')
def when_set_timeout(pilot) -> None:
    ui(pilot).click_id("#set_timeout")


@when('I press "Set <property>" button')
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


@when('I press "Update" button')
def when_update(pilot) -> None:
    ui(pilot).click_label("Update")


@when('I press "Show output" button')
def when_show_output(pilot) -> None:
    ui(pilot).click_label("Show output")


@when('I press "Close" button in Settings')
def when_close_settings(pilot) -> None:
    ui(pilot).click_label("Close")
    ui(pilot).pause()


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
    ui(pilot).pause()
    ui(pilot).click_id("#ok")
    ui(pilot).assert_screen(TaskMenuScreen)


@when("I enter an invalid timeout and press Ok")
def when_enter_invalid_timeout(pilot) -> None:
    ui(pilot).set_value("#input_field", "abc")
    ui(pilot).pause()
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
        screen._selected_path = ui(pilot).app.state.runners_path / "sh_runner"
        screen.dismiss(screen._selected_path)   # noqa

    ui(pilot).app.call_from_thread(_do_select)
    ui(pilot).pause(0.1)


@when("I dismiss the warning")
def when_dismiss_warning(pilot) -> None:
    ui(pilot).click_id("#info_button")


@when('I enable Auto-scroll in Settings')
def when_enable_auto_scroll(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    cb = ui(pilot).app.screen.query_one("#auto_scroll_checkbox")
    if not cb.value:
        ui(pilot).click_id("#auto_scroll_checkbox")
    ui(pilot).pause()


@when('I disable Auto-scroll in Settings')
def when_disable_auto_scroll(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    cb = ui(pilot).app.screen.query_one("#auto_scroll_checkbox")
    if cb.value:
        ui(pilot).click_id("#auto_scroll_checkbox")
    ui(pilot).pause()


@when('I click "Clear Screen" in Settings')
def when_clear_screen(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    ui(pilot).click_id("#clear_screen_button")
    ui(pilot).pause()


@when('I check "Word Wrap" in Settings')
def when_check_wrap_in_settings(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    cb = ui(pilot).app.screen.query_one("#wrap_checkbox")
    if not cb.value:
        ui(pilot).click_id("#wrap_checkbox")
    ui(pilot).pause()


@when('I uncheck "Word Wrap" in Settings')
def when_uncheck_wrap_in_settings(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    cb = ui(pilot).app.screen.query_one("#wrap_checkbox")
    if cb.value:
        ui(pilot).click_id("#wrap_checkbox")
    ui(pilot).pause()


@when('I open Help from Settings')
def when_open_help(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    ui(pilot).click_id("#help_button")
    ui(pilot).pause()


@when("new content is appended to the file")
def when_append_content(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    fs().append_text(log_file, "new content\n")


@when("I cancel the property prompt")
def when_cancel_property(pilot) -> None:
    ui(pilot).press("escape")
    ui(pilot).pause()


@when("I provide a valid value and press Ok")
def when_provide_valid_value(pilot) -> None:
    ui(pilot).set_value("#input_field", "test_value")
    ui(pilot).pause()
    ui(pilot).click_id("#ok")


@when("I confirm the installation")
def when_confirm_install(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("version_"):
            ui(pilot).click_id(f"#{btn.id}")
            ui(pilot).pause()
            break


@when("the install finalizes")
def when_install_finalizes(pilot) -> None:
    if isinstance(ui(pilot).app.screen, InputScreen):
        ui(pilot).set_value("#input_field", "test_value")
        ui(pilot).pause()
        ui(pilot).click_id("#ok")
        ui(pilot).pause()


@when("properties are prompted one by one via InputScreen")
def when_properties_prompted(pilot) -> None:
    ui(pilot).assert_screen(InputScreen)


@when("I provide valid values for all properties")
def when_provide_all_values(pilot) -> None:
    for _ in range(10):
        screen = ui(pilot).app.screen
        if not isinstance(screen, InputScreen):
            break
        ui(pilot).set_value("#input_field", "test_value")
        ui(pilot).pause()
        ui(pilot).click_id("#ok")
        ui(pilot).pause()


@when("I install the same runner again with a different version")
@when("I install the same runner with the same version")
def when_reinstall_runner(pilot) -> None:
    from tests.bdd.given_steps import given_runner_type_screen
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
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("version_"):
            ui(pilot).click_id(f"#{btn.id}")
            ui(pilot).pause()
            break


@when("I enter an invalid URL (doesn't match GitHub URL regex)")
def when_invalid_url(pilot) -> None:
    ui(pilot).set_value("#input_field", "not-a-url")
    ui(pilot).pause(0.1)
    ui(pilot).click_id("#ok")


@when("a runner is installed or removed on disk")
def when_runner_disk_change(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    if runner_path.exists():
        shutil.rmtree(runner_path)


@when("the git checkout fails")
def when_git_checkout_fails(pilot) -> None:
    _irv_mod.git_checkout = lambda _repo, _tag: False  # type: ignore[method-assign]
    tmp_folder = getattr(ui(pilot).app.screen, "tmp_runner_folder", None)
    if tmp_folder:
        (tmp_folder / ".git").mkdir(exist_ok=True)
    for btn in ui(pilot).app.screen.query("Button"):
        if btn.id and btn.id.startswith("version_"):
            ui(pilot).click_id(f"#{btn.id}")
            ui(pilot).pause()
            break
    if isinstance(ui(pilot).app.screen, ConfirmationScreen):
        ui(pilot).click_yes()
        ui(pilot).pause()


@when("I uninstall a task from its Task Menu screen")
def when_uninstall_task(pilot) -> None:
    ui(pilot).nav_to_task_menu()
    ui(pilot).click_id("#uninstall")
    ui(pilot).wait_until_screen(ConfirmationScreen)
    ui(pilot).click_id("#yes_uninstall")
    ui(pilot).pause(0.5)


@when("return to the Tasks screen")
def when_return_tasks(pilot) -> None:
    ui(pilot).pause()
    ui(pilot).assert_screen(TasksMenuScreen)


@when("the app is restarted")
def when_app_restarted(pilot) -> None:
    app = pilot.app
    app.state.runners.clear()
    app.state.ensure_dirs()
    app._exit = False  # noqa


@when("the runner's `run()` method is called")
def when_runner_run(pilot) -> RunnerProcess:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    proc = RunnerProcess(runner_path, "test-session", ui(pilot).app.state.tmp_dir)
    proc._run_lock = True
    proc.run()
    return proc


@when('the runner\'s execution loop reaches task iteration')
@when('the runner\'s execution loop enters "idle" state')
def when_loop_state(pilot) -> None:
    runner = ui(pilot).app.state.runners.get("sh_runner")
    if runner and hasattr(runner, "_run_lock"):
        runner._run_lock = True  # noqa


@when("the runner is shut down")
def when_runner_shut_down(pilot) -> None:
    ui(pilot).app.state.runners.pop("sh_runner", None)
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "termination")


@when('I click "Clear Log File" in Settings')
def when_click_clear_log_file(pilot) -> None:
    if isinstance(ui(pilot).app.screen, LogScreen):
        ui(pilot).click_id("#settings_button")
        ui(pilot).pause()
    ui(pilot).click_id("#clear_log_file_button")
    ui(pilot).pause()


@when("I cancel the clear confirmation")
def when_cancel_clear(pilot) -> None:
    ui(pilot).click_id("#cancel_button")
    ui(pilot).pause()


@when("I confirm the clear")
def when_confirm_clear(pilot) -> None:
    ui(pilot).click_id("#delete_button")
    ui(pilot).pause()
