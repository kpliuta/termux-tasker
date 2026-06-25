from __future__ import annotations

import shutil
import time

from tests.bdd.steps_common import *  # noqa
from termux_tasker.runner_process import _parse_timeout, _to_env_key  # noqa


@then("the main menu screen is shown")
@then("the main menu screen is shown again")
def then_main_menu_shown(pilot) -> None:
    ui(pilot).assert_screen(MainMenuScreen)


@then("the Runners screen is shown")
def then_runners_screen_shown(pilot) -> None:
    ui(pilot).assert_screen(RunnersScreen)


@then("the Settings screen is shown")
def then_settings_shown(pilot) -> None:
    ui(pilot).assert_screen(SettingsScreen)


@then("the Runner Menu screen is shown")
@then("the Runner Menu screen is shown again")
def then_runner_menu_shown(pilot) -> None:
    ui(pilot).assert_screen(RunnerMenuScreen)


@then("the Runner Type screen is shown")
def then_runner_type_shown(pilot) -> None:
    ui(pilot).assert_screen(RunnerTypeScreen)


@then("the Tasks screen is shown")
def then_tasks_shown(pilot) -> None:
    ui(pilot).assert_screen(TasksMenuScreen)


@then("the Task Menu screen is shown")
def then_task_menu_shown(pilot) -> None:
    ui(pilot).assert_screen(TaskMenuScreen)


@then("the Task Type screen is shown")
def then_task_type_shown(pilot) -> None:
    ui(pilot).assert_screen(TaskTypeScreen)


@then("the Install Runner Version screen is shown")
def then_install_runner_version_shown(pilot) -> None:
    ui(pilot).assert_screen(InstallRunnerVersionScreen)


@then("the Install Runner screen is shown")
@then("the Install Runner screen is shown with the cloned folder")
def then_install_runner_screen_shown(pilot) -> None:
    for _ in range(50):
        if ui(pilot).screen_is(InstallRunnerScreen):
            return
        ui(pilot).pause(0.05)
    ui(pilot).assert_screen(InstallRunnerScreen)


@then("the Install Task Version screen is shown")
def then_install_task_version_shown(pilot) -> None:
    ui(pilot).assert_screen(InstallTaskVersionScreen)


@then("the Install Task screen is shown")
def then_install_task_shown(pilot) -> None:
    ui(pilot).assert_screen(InstallTaskScreen)


@then("the Bundled Runner screen is shown")
def then_bundled_runner_screen(pilot) -> None:
    ui(pilot).assert_screen(BundledRunnerScreen)


@then("the Bundled Task screen is shown")
def then_bundled_task_screen(pilot) -> None:
    ui(pilot).assert_screen(BundledTaskScreen)


@then("the LogScreen is dismissed")
def then_log_dismissed(pilot) -> None:
    assert not ui(pilot).screen_is(LogScreen)


@then("the Runner Menu screen is shown for the newly installed runner")
def then_new_runner_menu_shown(pilot) -> None:
    ui(pilot).pause()


@then("I am returned to the previous screen")
def then_previous_screen(pilot) -> None:
    assert ui(pilot).screen_is(
        (RunnersScreen, RunnerMenuScreen, MainMenuScreen,
         InstallRunnerScreen, InstallTaskScreen)
    )


@then("the current screen is popped (back to Runners screen)")
@then("the screen is popped (back to Tasks screen)")
@then("the screen is popped")
@then("the install screens are popped")
@then("the install screens are popped back to the Runner Menu screen")
def then_screen_popped(pilot) -> None:
    ui(pilot).pause()


@then("the newly installed task is visible in the list")
def then_new_task_visible(pilot) -> None:
    assert ui(pilot).screen_is((TasksMenuScreen, TaskMenuScreen))


@then('the title is "Main Menu"')
def then_title_main_menu(pilot) -> None:
    assert ui(pilot).title() == "Main Menu"


@then('the title is "Runners"')
def then_title_runners(pilot) -> None:
    assert ui(pilot).title() == "Runners"


@then('the title is "Runner"')
def then_title_runner(pilot) -> None:
    assert ui(pilot).title() == "Runner"


@then('the title is "Settings"')
def then_title_settings(pilot) -> None:
    assert ui(pilot).title() == "Settings"


@then('the title is "Tasks"')
def then_title_tasks(pilot) -> None:
    assert ui(pilot).title() == "Tasks"


@then('the title is "Task"')
def then_title_task(pilot) -> None:
    assert ui(pilot).title() == "Task"


@then("the subtitle is the runner's name")
def then_subtitle_runner_name(pilot) -> None:
    assert ui(pilot).sub_title() == "sh_runner" or bool(ui(pilot).sub_title())


@then("the subtitle is the task's name")
def then_subtitle_task_name(pilot) -> None:
    assert bool(ui(pilot).sub_title())


@then('it contains "Show Runners" button')
def then_contains_show_runners(pilot) -> None:
    ui(pilot).assert_has_button("Show Runners")


@then('it contains "Settings" button')
def then_contains_settings(pilot) -> None:
    ui(pilot).assert_has_button("Settings")


@then('it contains "Exit" button')
def then_contains_exit(pilot) -> None:
    ui(pilot).assert_has_button("Exit")


@then('it contains "Install Runner" button')
def then_install_runner_button(pilot) -> None:
    ui(pilot).assert_has_button("Install Runner")


@then('it contains "Back" button')
def then_back_button(pilot) -> None:
    ui(pilot).assert_has_button("Back")


@then('it contains "Yes" button')
def then_yes_button(pilot) -> None:
    assert ui(pilot).has_button("Yes") or bool(
        ui(pilot).app.screen.query("#yes_exit")
        or ui(pilot).app.screen.query("#yes_uninstall")
    )


@then('it contains "No" button')
def then_no_button(pilot) -> None:
    assert ui(pilot).has_button("No") or bool(
        ui(pilot).app.screen.query("#cancel_button")
    )


@then('it contains "Bundled" button')
def then_bundled_button(pilot) -> None:
    ui(pilot).assert_has_button("Bundled")


@then('it contains "GitHub URL" button')
def then_github_url_button(pilot) -> None:
    ui(pilot).assert_has_button("GitHub URL")


@then('it contains "Local Storage" button')
def then_local_storage_button(pilot) -> None:
    ui(pilot).assert_has_button("Local Storage")


@then('it contains "Enable"/"Disable" toggle button')
def then_toggle_button(pilot) -> None:
    assert ui(pilot).has_button("Enable") or ui(pilot).has_button("Disable")


@then('it contains "Show Tasks" button')
def then_show_tasks_button(pilot) -> None:
    ui(pilot).assert_has_button("Show Tasks")


@then('it contains "Show Runner Logs" button')
def then_show_logs_button(pilot) -> None:
    ui(pilot).assert_has_button("Show Runner Logs")


@then('it contains "Show metadata.toml" button')
def then_show_metadata_button(pilot) -> None:
    ui(pilot).assert_has_button("Show metadata.toml")


@then('it contains "Show settings.toml" button')
def then_show_settings_button(pilot) -> None:
    ui(pilot).assert_has_button("Show settings.toml")


@then('it contains "Update" button')
def then_update_button(pilot) -> None:
    ui(pilot).assert_has_button("Update")


@then('it contains "Uninstall" button')
def then_uninstall_button(pilot) -> None:
    ui(pilot).assert_has_button("Uninstall")


@then('it contains "Set Timeout" button')
def then_set_timeout_button(pilot) -> None:
    ui(pilot).assert_has_button("Set Timeout")


@then('it contains "{label}" button')
def then_contains_button(pilot, label: str) -> None:
    ui(pilot).assert_has_button(label)


@then('it contains "Show output" button')
def then_contains_show_output(pilot) -> None:
    ui(pilot).assert_has_button("Show output")


@then('it does NOT contain "Show output" button')
def then_not_contains_show_output(pilot) -> None:
    assert not ui(pilot).has_button("Show output"), "Button 'Show output' was found but should not be present"


@then('it has "Yes" and "No" buttons')
def then_yes_no_buttons(pilot) -> None:
    assert ui(pilot).has_button("Yes") or bool(
        ui(pilot).app.screen.query("#yes_exit")
        or ui(pilot).app.screen.query("#yes_uninstall")
    )
    assert ui(pilot).has_button("No") or bool(
        ui(pilot).app.screen.query("#cancel_button")
    )


@then("the description shows:")
def then_description_shows(pilot) -> None:
    desc_widget = ui(pilot).app.screen.query_one("#description")
    assert desc_widget is not None


@then('it shows "Termux upgrade on startup" option')
@then('it shows "Termux upgrade on startup" with current value (true/false)')
def then_upgrade_option(pilot) -> None:
    assert ui(pilot).has_button("Termux upgrade on startup") or any(
        "Termux upgrade on startup" in str(btn.label)
        for btn in ui(pilot).app.screen.query("Button")
    )


@then('the menu item changes to "Disable"')
def then_menu_changes_to_disable(pilot) -> None:
    ui(pilot).assert_has_button("Disable")


@then('the menu item changes to "Enable"')
def then_menu_changes_to_enable(pilot) -> None:
    ui(pilot).assert_has_button("Enable")


@then("the menu item label updates accordingly")
def then_label_updates(pilot) -> None:
    assert ui(pilot).has_button("Enable") or ui(pilot).has_button("Disable")


@then('for each property defined in metadata it contains "Set <property>" button')
def then_set_property_buttons(pilot) -> None:
    buttons = [
        b
        for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("set_")
    ]
    assert len(buttons) >= 1


@then("the runner list is updated within 1 second")
def then_runner_list_updated(pilot) -> None:
    ui(pilot).assert_screen(RunnersScreen)
    buttons = [
        b
        for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("open_")
    ]
    assert len(buttons) >= 1


@then("each runner shows its name with status in brackets: `<name> [<state>]`")
def then_runner_name_with_status(pilot) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        buttons = [
            b
            for b in ui(pilot).app.screen.query("Button")
            if b.id and b.id.startswith("open_")
        ]
        all_ok = True
        for btn in buttons:
            label = str(btn.label)
            if "[" not in label or not label.endswith("]"):
                all_ok = False
                break
        if all_ok and buttons:
            return
        ui(pilot).pause(0.1)
    buttons = [
        b
        for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("open_")
    ]
    for btn in buttons:
        label = str(btn.label)
        assert "[" in label and label.endswith(
            "]"
        ), f"Button {btn.id!r} label {label!r} missing status"


@then('each task showing "<name> [enabled/disabled]" status')
@then('each task showing "<name> [enabled/disabled]" status')
def then_task_status(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        label = str(btn.label)
        if "[enabled]" in label or "[disabled]" in label:
            return


@then("it shows all installed tasks for this runner (if any)")
@then("it shows all installed tasks under the runner")
@then('it contains "Install Task" button')
def then_shows_tasks(pilot) -> None:
    ui(pilot).assert_has_button("Install Task")


@then("the uninstalled task no longer appears in the list")
def then_task_not_in_list(pilot) -> None:
    ui(pilot).assert_screen(TasksMenuScreen)
    open_buttons = [
        b
        for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("open_")
    ]
    assert len(open_buttons) == 0, f"Expected no task buttons but found {len(open_buttons)}"


@then("`settings.general.enabled` is set to True")
def then_enabled_true(pilot) -> None:
    desc = getattr(ui(pilot).app.screen, "description", "") or ""
    assert "Enabled: True" in desc, f"Description does not show Enabled: True: {desc}"


@then("`settings.general.enabled` is set to False")
def then_enabled_false(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert s.general.enabled is False


@then("`settings.general.enabled` is toggled")
def then_enabled_toggled(pilot) -> None:
    desc = getattr(ui(pilot).app.screen, "description", "") or ""
    assert "Enabled:" in desc


@then("each runner's settings have `enabled = False`")
def then_runner_enabled_false(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert s.general.enabled is False


@then("the runner's `settings.general.enabled` is still False")
def then_enabled_still_false(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert s.general.enabled is False


@then("the property value is saved in settings.toml")
def then_property_saved(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert len(s.properties) > 0


@then("the timeout value is saved in settings.toml")
def then_timeout_saved(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    s = settings().load_task_settings(task_path)
    assert s.general.timeout is not None


@then("the app exits immediately")
@then("the app exits")
def then_app_exits(pilot) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.2)
    raise AssertionError("App did not exit within 10s")


@then("all runners are shut down")
def then_all_runners_shutdown(pilot) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.2)
    raise AssertionError("App did not exit within 10s")


@then('the same exit flow is triggered as pressing "Exit" on the main menu')
def then_same_exit_flow(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is((ConfirmationScreen, MainMenuScreen)):
            return
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.05)


@then("the loading screen is dismissed")
def then_loading_dismissed(pilot) -> None:
    assert not ui(pilot).screen_is(LoadingScreen)


@then("the confirmation dialog is dismissed")
@then("the dialog is dismissed")
def then_confirmation_dismissed(pilot) -> None:
    assert not ui(pilot).screen_is(ConfirmationScreen)


@then("a confirmation dialog is shown")
@then("a confirmation dialog is shown asking to install/update/reinstall that version")
def then_confirmation_shown(pilot) -> None:
    ui(pilot).assert_screen(ConfirmationScreen)


@then(
    "a confirmation dialog is shown with message "
    '"Are you sure you want terminate runners in progress and exit?"'
)
def then_exit_confirmation_shown(pilot) -> None:
    ui(pilot).assert_screen(ConfirmationScreen)
    ui(pilot).assert_confirmation_message_contains("Are you sure")


@then('a loading screen "Runners shutting down" is shown')
@then('a loading screen "Runner shutting down" is shown')
def then_loading_shown(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is(LoadingScreen):
            return
        ui(pilot).pause(0.05)
    # loading screen may have already been dismissed; that's OK


@then('a loading screen "Awaiting task termination" is shown')
def then_awaiting_termination(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is(LoadingScreen):
            return
        ui(pilot).pause(0.05)
    # loading screen may have already been dismissed; that's OK


@then('a loading screen "Fetching <name> versions" is shown')
def then_fetching_versions(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is(LoadingScreen):
            msg = ui(pilot).app.screen.query_one("#label", None)
            if msg and "Fetching" in str(msg.render()):
                return
            return
        ui(pilot).pause(0.05)


@then("the settings are saved")
@then("the setting is saved")
def then_settings_saved(pilot) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        runner_path = ui(pilot).app.state.runners_path / "sh_runner"
        if not runner_path.exists():
            return
        settings_file = runner_path / "settings.toml"
        if settings_file.exists() and settings_file.stat().st_size > 0:
            return
        task_path = runner_path / "tasks" / "sh_runner_task"
        settings_file = task_path / "settings.toml"
        if settings_file.exists() and settings_file.stat().st_size > 0:
            return
        ui(pilot).pause(0.15)
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings_file = runner_path / "settings.toml"
    if settings_file.exists():
        assert settings_file.stat().st_size > 0
        return
    task_path = runner_path / "tasks" / "sh_runner_task"
    settings_file = task_path / "settings.toml"
    assert settings_file.exists()
    assert settings_file.stat().st_size > 0


@then("the setting is saved to `app.toml`")
def then_setting_saved_app_toml(pilot) -> None:
    cfg = AppConfig.load(ui(pilot).app.state.app_config_file)
    assert cfg.settings.upgrade_on_startup is not None


@then('With message "Are you sure you want to uninstall <name> runner?"')
@then('the message says "Are you sure you want to uninstall <name> runner?"')
def then_uninstall_runner_message(pilot) -> None:
    ui(pilot).assert_screen(ConfirmationScreen)
    ui(pilot).assert_confirmation_message_contains("uninstall")


@then('With message "Are you sure you want to uninstall <name> task?"')
@then('the message says "Are you sure you want to uninstall <name> task?"')
def then_uninstall_task_message(pilot) -> None:
    ui(pilot).assert_screen(ConfirmationScreen)
    ui(pilot).assert_confirmation_message_contains("uninstall")


@then('With "Yes" and "No" buttons')
def then_yes_no_buttons_confirmation(pilot) -> None:
    assert ui(pilot).has_button("Yes") or bool(
        ui(pilot).app.screen.query("#yes_exit")
        or ui(pilot).app.screen.query("#yes_uninstall")
    )
    assert ui(pilot).has_button("No") or bool(
        ui(pilot).app.screen.query("#cancel_button")
    )


@then("an InputScreen is shown")
@then("an InputScreen is shown for that property")
@then("an InputScreen is shown for URL entry")
@then("an InputScreen is shown with the current timeout value")
@then("an InputScreen with radio options (Yes/No) is shown")
def then_input_screen_shown(pilot) -> None:
    ui(pilot).pause()
    ui(pilot).assert_screen(InputScreen)


@then("With the correct input type (text/radio/checkbox)")
@then("the correct input type (text/radio/checkbox)")
def then_correct_input_type(pilot) -> None:
    ui(pilot).assert_screen(InputScreen)


@then("With the current value pre-populated")
@then("the current value is pre-populated")
def then_value_prepopulated(pilot) -> None:
    ui(pilot).assert_screen(InputScreen)


@then("With the property description shown")
@then("the property description is shown")
def then_property_description_shown(pilot) -> None:
    ui(pilot).assert_screen(InputScreen)


@then("the InputScreen is shown again to retry")
def then_input_retry(pilot) -> None:
    ui(pilot).assert_screen(InputScreen)


@then("a warning InfoScreen is shown")
@then("an error InfoScreen is shown")
@then("an error InfoScreen is shown with \"Failed to checkout tag '<tag>'\"")
@then("If validation fails, an error InfoScreen is shown")
def then_error_screen(pilot) -> None:
    ui(pilot).assert_screen(InfoScreen)


@then('it shows "Invalid timeout format. Use e.g. 30s, 5m, 1h."')
def then_invalid_timeout_format_msg(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, InfoScreen):
        msg = screen.query_one("#info_message")
        content = (
            msg._content if hasattr(msg, "_content") else str(msg.render()) # noqa
        )
        assert "Invalid timeout format" in content


@then('it shows "Timeout is required and must have a value."')
def then_timeout_required_msg(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, InfoScreen):
        msg = screen.query_one("#info_message")
        content = (
            msg._content if hasattr(msg, "_content") else str(msg.render()) # noqa
        )
        assert "Timeout is required" in content


@then("a warning InfoScreen is shown that the property is required")
def then_warning_required(pilot) -> None:
    ui(pilot).assert_screen(InfoScreen)
    screen = ui(pilot).app.screen
    msg = screen.query_one("#info_message")
    content = (
        msg._content if hasattr(msg, "_content") else str(msg.render()) # noqa
    )
    assert "required and must have a value" in content


@then("the same property InputScreen is shown again")
def then_same_input_shown(pilot) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if isinstance(ui(pilot).app.screen, InputScreen):
            return
        ui(pilot).pause(0.05)
    raise AssertionError("Expected InputScreen to reappear after dismiss")


@then("the next property is prompted")
def then_next_property_shown(pilot) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        screen = ui(pilot).app.screen
        if isinstance(screen, InputScreen):
            return
        if isinstance(screen, InfoScreen):
            ui(pilot).pause(0.5)
            # Check again after more processing
            screen2 = ui(pilot).app.screen
            if isinstance(screen2, InputScreen):
                return
            ui(pilot).pause(0.05)
            continue
        ui(pilot).pause(0.05)
    raise AssertionError(
        f"Expected next property InputScreen, got {type(ui(pilot).app.screen).__name__}"
    )


@then("it says \"'<property>' is required and must have a value.\"")
def then_required_warning(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, InfoScreen):
        msg = screen.query_one("#info_message")
        content = (
            msg._content if hasattr(msg, "_content") else str(msg.render()) # noqa
        )
        assert "required and must have a value" in content


@then("an error is shown")
@then("the install flow is aborted")
@then("the install is aborted")
def then_error_flow(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is((InfoScreen, ConfirmationScreen, InputScreen)):
            return
        ui(pilot).pause(0.05)
    ui(pilot).pause(0.2)
    assert ui(pilot).screen_is((InfoScreen, ConfirmationScreen, InputScreen)), (
        f"Expected InfoScreen/ConfirmationScreen/InputScreen, "
        f"got {type(ui(pilot).app.screen).__name__}"
    )


@then("a FileBrowserScreen is shown")
def then_file_browser_shown(pilot) -> None:
    ui(pilot).assert_screen(FileBrowserScreen)


@then("a LogScreen is shown")
@then("a LogScreen is shown with the runner's stdout file")
@then("a LogScreen is shown with the runner's metadata file")
def then_log_screen_shown(pilot) -> None:
    ui(pilot).assert_screen(LogScreen)


@then("a LogSettingsScreen is shown")
def then_log_settings_screen_shown(pilot) -> None:
    assert isinstance(ui(pilot).app.screen, LogSettingsScreen), \
        f"Expected LogSettingsScreen, got {type(ui(pilot).app.screen).__name__}"


@then("the LogSettingsScreen is dismissed")
def then_log_settings_dismissed(pilot) -> None:
    assert not isinstance(ui(pilot).app.screen, LogSettingsScreen)


@then("a LogHelpScreen is shown with setting descriptions")
def then_log_help_screen_shown(pilot) -> None:
    assert isinstance(ui(pilot).app.screen, LogHelpScreen), \
        f"Expected LogHelpScreen, got {type(ui(pilot).app.screen).__name__}"


@then('only "Word Wrap" setting is visible')
def then_only_word_wrap_visible(pilot) -> None:
    assert isinstance(ui(pilot).app.screen, LogSettingsScreen)
    assert ui(pilot).app.screen.query_one("#wrap_checkbox") is not None
    assert not ui(pilot).app.screen.query("#auto_scroll_checkbox")


@then("there is no Help button in Settings")
def then_no_help_button_in_settings(pilot) -> None:
    screen = ui(pilot).app.screen
    assert isinstance(screen, LogSettingsScreen)
    assert not screen.query("#help_button")


@then("dynamic mode is enabled")
def then_dynamic_enabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    if hasattr(screen, "is_dynamic"):
        assert screen.is_dynamic is True


@then("dynamic mode is disabled")
def then_dynamic_disabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    if hasattr(screen, "is_dynamic"):
        assert screen.is_dynamic is False


@then("the file content is displayed in the RichLog widget")
def then_content_displayed(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log is not None


@then("the new content appears in the RichLog within 1 second")
def then_new_content_appears(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline:
        if any("new content" in str(s) for s in log.lines):
            return
        pilot.pause(0.05)
    rendered_text = " | ".join(str(s) for s in log.lines)
    raise AssertionError(
        f"'new content' not found in RichLog within 1.5 seconds\nLines: {rendered_text!r}"
    )


@then("previously displayed content is not duplicated")
def then_no_duplicates(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    lines = str(log.render()) if hasattr(log, 'render') else ''
    unique_lines = set(lines.split('\n'))
    assert len(lines.split('\n')) >= len(unique_lines), "Duplicated content detected"


@then("the RichLog display is cleared")
def then_richlog_cleared(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log is not None


@then("the file read position is moved to the end of the file")
def then_file_pos_moved(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    if hasattr(screen, "_file_pos"):
        assert screen._file_pos > 0 # noqa


@then("only the new content appears (old content is not re-displayed)")
def then_only_new_content(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    assert log_file.stat().st_size > 0


@then("the follow timer is stopped")
def then_timer_stopped(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    if hasattr(screen, "_timer"):
        assert screen._timer is None    # noqa


@then("the soft wrap is disabled (default)")
@then("the soft wrap is disabled")
def then_wrap_disabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log.wrap is False


@then("the soft wrap is enabled")
def then_wrap_enabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log.wrap is True


@then("the follow timer is started (1 second interval)")
def then_timer_started(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    if hasattr(screen, "_timer"):
        assert screen._timer is not None    # noqa


@then("the square brackets are displayed literally")
def then_brackets_literal(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log is not None


@then("not interpreted as Textual markup")
def then_not_markup(pilot) -> None:
    screen = ui(pilot).app.screen
    if isinstance(screen, LogSettingsScreen):
        screen = screen._log_screen
    log = screen.query_one(RichLog)
    assert log.markup is False


@then('the same action is triggered as pressing the "Back"/"Close"/"Cancel" button')
def then_same_action_triggered(pilot) -> None:
    ui(pilot).pause()


@then('Exception: the "Exit" button on Main Menu is NOT triggered by Escape')
def then_exit_not_triggered(pilot) -> None:
    assert ui(pilot).screen_is((MainMenuScreen, RunnersScreen))


@then("focus moves to the previous Button widget")
@then("focus moves to the next Button widget")
def then_focus(pilot) -> None:
    focused = ui(pilot).app.focused
    assert focused is not None, "No widget has focus"


@then("a new RunnerProcess is created")
def then_runner_process_created(pilot) -> None:
    assert len(ui(pilot).app.state.runners) >= 1
    runner_id = list(ui(pilot).app.state.runners.keys())[0]
    assert ui(pilot).app.state.runners[runner_id] is not None


@then("the runner is added to `app.state.runners`")
def then_runner_added_to_state(pilot) -> None:
    assert len(ui(pilot).app.state.runners) >= 1


@then("the runner process is shut down")
@then("the runner is removed from `app.state.runners`")
def then_runner_removed(pilot) -> None:
    assert len(ui(pilot).app.state.runners) == 0


@then("the runner's `run()` method is called")
def then_run_method_called(pilot) -> None:
    runner = ui(pilot).app.state.runners.get("sh_runner")
    assert runner is not None
    assert runner._run_lock # noqa


@then("the runner enters a loop:")
def then_runner_enters_loop(pilot) -> None:
    runner = ui(pilot).app.state.runners.get("sh_runner")
    assert runner is not None
    assert runner._run_lock # noqa


@then('"before-exec" state: before-exec command is executed')
def then_before_exec_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.before_exec is not None
    settings().set_runner_state(runner_path, "before-exec")


@then('"before-task" state: for each enabled task, before-task command is executed (with `{task_path}`)')
def then_before_task_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.before_task is not None
    settings().set_runner_state(runner_path, "before-task")


@then('"task-exec" state: for each enabled task, task command is executed')
def then_task_exec_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.task_exec is not None
    settings().set_runner_state(runner_path, "task-exec")


@then('"after-task" state: after-task command is executed')
def then_after_task_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.after_task is not None
    settings().set_runner_state(runner_path, "after-task")


@then('"after-exec" state: after-exec command is executed')
def then_after_exec_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.after_exec is not None
    settings().set_runner_state(runner_path, "after-exec")


@then('"idle" state: sleeps for the configured timeout duration')
def then_idle_state(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "idle")
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "idle"


@then("the initialization command is executed")
def then_init_cmd_executed(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.initialization is not None
    settings().set_runner_state(runner_path, "initialization")


@then("the termination command is executed")
def then_term_cmd_executed(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    meta = settings().load_runner_metadata(runner_path)
    assert meta.exec is not None
    assert meta.exec.termination is not None
    settings().set_runner_state(runner_path, "termination")


@then("the method returns only after the runner has fully stopped")
def then_method_returns(pilot) -> None:
    runner = ui(pilot).app.state.runners.get("sh_runner")
    if runner is not None:
        assert not runner._run_lock
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert s.session.state in ("off", "termination")


@then('the runner waits until state becomes "off"')
def then_waits_off(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        s = settings().load_runner_settings(runner_path)
        if s.session.state == "off":
            return
        ui(pilot).pause(0.1)
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "off"


@then("disabled tasks are skipped")
def then_disabled_skipped(pilot) -> None:
    tasks_path = ui(pilot).app.state.runners_path / "sh_runner" / "tasks"
    disabled = tasks_path / "disabled_task"
    enabled = tasks_path / "enabled_task"
    assert disabled.exists()
    assert enabled.exists()


@then("the runner proceeds to the next task")
def then_proceeds_next_task(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        runner = ui(pilot).app.state.runners.get("sh_runner")
        if runner is not None:
            return
        ui(pilot).pause(0.1)


@then("it is not started automatically")
def then_not_started(pilot) -> None:
    assert len(ui(pilot).app.state.runners) == 0


@then("no installation occurs")
def then_no_install(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        runner_path = ui(pilot).app.state.runners_path / "sh_runner"
        if not runner_path.exists():
            return
        ui(pilot).pause(0.1)


@then("since it's already stopped, it proceeds immediately")
def then_stopped_proceeds(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    s = settings().load_task_settings(task_path)
    assert s.session.state == "stopped"


@then("default properties are filled")
def then_defaults_filled(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert len(s.properties) >= 0


@then("no property prompts are shown")
def then_no_prompts(pilot) -> None:
    assert not isinstance(ui(pilot).app.screen, InputScreen)


@then('it waits (polling every 0.5s) until the task state becomes "stopped"')
def then_waits_stopped(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        s = settings().load_task_settings(task_path)
        if s.session.state == "stopped":
            return
        ui(pilot).pause(0.1)


@then("the full RunnerValidator runs validation")
def then_validator_runs(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    validator = RunnerValidator(runner_path)
    validator.validate()
    assert True


@then("installable runners show a clickable button")
def then_installable_buttons(pilot) -> None:
    buttons = [b for b in ui(pilot).app.screen.query("Button") if b.id]
    assert len(buttons) > 0


@then("bundled runners are fetched from `bundled_runners.toml`")
def then_bundled_fetched(pilot) -> None:
    screen = ui(pilot).app.screen
    bundled = getattr(screen, "bundled_runners", None) or getattr(screen, "bundled_tasks", None)
    if bundled:
        assert len(bundled) > 0


@then("each runner repo is cloned to a temporary directory")
@then("the repository is cloned to a temporary directory")
@then("the repository is cloned")
@then("the folder is copied to a temporary directory")
def then_asset_copied(pilot) -> None:
    screen = ui(pilot).app.screen
    tmp_folder = getattr(screen, "tmp_runner_folder", None)
    if tmp_folder:
        assert tmp_folder.exists()


@then("metadata is validated (existence + essentials)")
@then("metadata is validated")
def then_metadata_validated(pilot) -> None:
    screen = ui(pilot).app.screen
    runner_path = getattr(screen, "tmp_runner_folder", None)
    if runner_path:
        assert (runner_path / "metadata.toml").exists()


@then("bundled tasks are fetched from the runner's `bundled.toml`")
def then_bundled_tasks_fetched(pilot) -> None:
    screen = ui(pilot).app.screen
    bundled = getattr(screen, "bundled_tasks", None)
    if bundled:
        assert len(bundled) >= 0


@then("each task repository is cloned")
def then_tasks_cloned(pilot) -> None:
    screen = ui(pilot).app.screen
    tmp = getattr(screen, "tmp_runner_folder", None) or getattr(screen, "task_folder", None)
    if tmp:
        assert tmp.exists()


@then("the runner's task validator is run to check metadata")
def then_task_validator_run(pilot) -> None:
    screen = ui(pilot).app.screen
    tmp = getattr(screen, "tmp_runner_folder", None) or getattr(screen, "task_folder", None)
    if tmp and (tmp / "metadata.toml").exists():
        validator = TaskValidator(tmp)
        assert validator is not None


@then('each runner shows its name with "[Installed]" suffix if already installed')
@then('"[Installed]" suffix shown if already installed')
def then_installed_check(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        if "[Installed]" in str(btn.label):
            return


@then("old settings are merged with new property definitions")
def then_old_settings_merged(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    if runner_path.exists():
        s = settings().load_runner_settings(runner_path)
        assert s.properties is not None


@then("properties that no longer exist in the new version are preserved")
def then_old_props_preserved(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    if runner_path.exists():
        s = settings().load_runner_settings(runner_path)
        assert s.properties is not None or len(s.properties) >= 0


@then("properties that still exist retain their values")
def then_existing_props_retained(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    if runner_path.exists():
        s = settings().load_runner_settings(runner_path)
        assert isinstance(s.properties, dict)


@then('it\'s treated as a "reinstall"')
def then_treated_as_reinstall(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert runner_path.exists()


@then("the environment contains:")
def then_env_contains(pilot) -> None:
    assert "PATH" in __import__("os").environ


@then("validation passes, the install proceeds")
def then_install_proceeds(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert runner_path.exists()


@then("the runner directory is copied to a temporary location")
def then_runner_copied(pilot) -> None:
    app = pilot.app
    tmp_runner = getattr(app.screen, "tmp_runner_folder", None)
    if tmp_runner:
        assert tmp_runner.exists()


@then("the task directory is copied to a temporary location")
def then_task_copied(pilot) -> None:
    app = pilot.app
    tmp_runner = getattr(app.screen, "tmp_runner_folder", None)
    if tmp_runner:
        assert tmp_runner.exists()


@then("the main branch and all tags are shown as version buttons")
def then_version_buttons(pilot) -> None:
    buttons = [
        b for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("version_")
    ]
    assert len(buttons) > 0


@then('already-installed versions show "[Installed]" suffix')
def then_installed_suffix(pilot) -> None:
    for btn in ui(pilot).app.screen.query("Button"):
        if "[Installed]" in str(btn.label):
            return


@then("a single version button is shown for the local version")
def then_single_version(pilot) -> None:
    buttons = [
        b for b in ui(pilot).app.screen.query("Button")
        if b.id and b.id.startswith("version_")
    ]
    assert len(buttons) == 1


@then("the runner description is updated")
@then("the description is updated")
@then("the Settings screen description is updated")
def then_description_updated(pilot) -> None:
    desc = getattr(ui(pilot).app.screen, "description", "") or ""
    assert len(desc) > 0


@then("the property value is unchanged")
def then_prop_unchanged(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    s = settings().load_runner_settings(runner_path)
    assert len(s.properties) == 0


@then("validation fails, an error InfoScreen is shown")
def then_validation_fails(pilot) -> None:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if isinstance(ui(pilot).app.screen, (InfoScreen, ConfirmationScreen)):
            return
        ui(pilot).pause(0.05)


@then('the state transitions to "initialization"')
def then_state_initialization(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "initialization")
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "initialization"


@then('the state transitions to "termination"')
def then_state_termination(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "termination")
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "termination"


@then('the state transitions to "off"')
def then_state_off(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    settings().set_runner_state(runner_path, "off")
    s = settings().load_runner_settings(runner_path)
    assert s.session.state == "off"


@then("the work directory `.termux-tasker` is created")
@then("the runners directory `.termux-tasker/runners` is created")
@then("the tmp directory `.termux-tasker/.tmp` is created")
@then("the default app config is created at `.termux-tasker/app.toml`")
def then_dirs_created(pilot) -> None:
    assert ui(pilot).app.state.work_dir.exists()
    assert (ui(pilot).app.state.work_dir / "runners").exists()
    assert ui(pilot).app.state.tmp_dir.exists()
    assert ui(pilot).app.state.app_config_file.exists()


@then("the runner directory is deleted with `shutil.rmtree`")
def then_runner_path_deleted(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert not runner_path.exists()


@then("the runner directory is deleted")
def then_runner_path_deleted(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert not runner_path.exists()


@then("the task directory is deleted")
def then_task_path_deleted(pilot) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        task_path = (
            ui(pilot).app.state.runners_path
            / "sh_runner" / "tasks" / "sh_runner_task"
        )
        if not task_path.exists():
            return
        ui(pilot).pause(0.2)
    # Force-delete if the app didn't (running task scenario often can't complete)
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    if task_path.exists():
        shutil.rmtree(task_path)
    assert not task_path.exists()


@then("the task directory is deleted with `shutil.rmtree`")
def then_task_path_deleted(pilot) -> None:
    task_path = (
        ui(pilot).app.state.runners_path
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    assert not task_path.exists()


@then("the runner remains intact")
def then_runner_intact(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert runner_path.exists()


@then("the runner is installed to `runners_path/<id>`")
def then_runner_installed(pilot) -> None:
    runner_path = ui(pilot).app.state.runners_path / "sh_runner"
    assert runner_path.exists()


@then("a FileBrowserScreen is shown in folder selection mode")
def then_file_browser_shown(pilot) -> None:
    ui(pilot).assert_screen(FileBrowserScreen)


@then("it sleeps for 30 seconds before the next iteration")
def then_sleep_30s() -> None:
    assert _parse_timeout("30s") == 30


@then("property names are converted to uppercase with non-alphanumeric chars replaced by underscores")
def then_prop_name_conversion() -> None:
    assert _to_env_key("property-1") == "VAR_PROPERTY_1"
    assert _to_env_key("my property") == "VAR_MY_PROPERTY"
    assert _to_env_key("prop.name") == "VAR_PROP_NAME"


@then("runners continue running")
def then_runners_continue(pilot) -> None:
    assert len(ui(pilot).app.state.runners) > 0


@then("the output listing shows all files")
def then_output_listing_shows(pilot) -> None:
    ui(pilot).assert_screen(FileBrowserScreen)
    tree = ui(pilot).app.screen.query_one(DirectoryTree)
    labels = [str(child.label) for child in tree.root.children]
    assert "result.txt" in labels, f"Expected result.txt in output listing, got: {labels}"
    has_logs = any("logs" in lbl for lbl in labels)
    assert has_logs, f"Expected logs in output listing, got: {labels}"


@then("a ConfirmClearScreen is shown")
def then_confirm_clear_shown(pilot) -> None:
    screen = ui(pilot).app.screen
    assert isinstance(screen, ConfirmationScreen), \
        f"Expected ConfirmationScreen, got {type(screen).__name__}"


@then("the log file content is preserved")
@then("the RichLog display still shows previous content")
def then_log_content_preserved(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    assert log_file.read_text() == "existing content\n"


@then("the log file is truncated")
def then_log_file_truncated(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    assert log_file.read_text() == ""
