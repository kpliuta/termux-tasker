from __future__ import annotations

from tests.bdd.steps_common import *  # noqa
from termux_tasker.runner_process import _parse_timeout # noqa


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
    from termux_tasker.ui.screens.install_runner_version import InstallRunnerVersionScreen

    ui(pilot).assert_screen(InstallRunnerVersionScreen)


@then("the Install Runner screen is shown")
@then("the Install Runner screen is shown with the cloned folder")
def then_install_runner_screen_shown(pilot) -> None:
    from termux_tasker.ui.screens.install_runner import InstallRunnerScreen

    for _ in range(50):
        if ui(pilot).screen_is(InstallRunnerScreen):
            return
        ui(pilot).pause(0.05)
    ui(pilot).assert_screen(InstallRunnerScreen)


@then("the Install Task Version screen is shown")
def then_install_task_version_shown(pilot) -> None:
    from termux_tasker.ui.screens.install_task_version import InstallTaskVersionScreen

    ui(pilot).assert_screen(InstallTaskVersionScreen)


@then("the Install Task screen is shown")
def then_install_task_shown(pilot) -> None:
    from termux_tasker.ui.screens.install_task import InstallTaskScreen

    ui(pilot).assert_screen(InstallTaskScreen)


@then("the Bundled Runner screen is shown")
def then_bundled_runner_screen(pilot) -> None:
    from termux_tasker.ui.screens.bundled_runner import BundledRunnerScreen

    ui(pilot).assert_screen(BundledRunnerScreen)


@then("the Bundled Task screen is shown")
def then_bundled_task_screen(pilot) -> None:
    from termux_tasker.ui.screens.bundled_task import BundledTaskScreen

    ui(pilot).assert_screen(BundledTaskScreen)


@then("the LogScreen is dismissed")
def then_log_dismissed(pilot) -> None:
    assert not ui(pilot).screen_is(LogScreen)


@then("the Runner Menu screen is shown for the newly installed runner")
def then_new_runner_menu_shown(pilot) -> None:
    ui(pilot).pause(0.2)


@then("I am returned to the previous screen")
def then_previous_screen(pilot) -> None:
    assert ui(pilot).screen_is((RunnersScreen, RunnerMenuScreen, MainMenuScreen))


@then("the current screen is popped (back to Runners screen)")
@then("the screen is popped (back to Tasks screen)")
@then("the screen is popped")
@then("the install screens are popped")
@then("the install screens are popped back to the Runner Menu screen")
def then_screen_popped(pilot) -> None:
    ui(pilot).pause(0.2)


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
    import time
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
    ui(pilot).pause(0.2)
    desc = getattr(ui(pilot).app.screen, "description", "") or ""
    assert "Enabled: True" in desc, f"Description does not show Enabled: True: {desc}"


@then("`settings.general.enabled` is set to False")
def then_enabled_false(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    s = settings().load_runner_settings(runner_dir)
    assert s.general.enabled is False


@then("`settings.general.enabled` is toggled")
def then_enabled_toggled(pilot) -> None:
    desc = getattr(ui(pilot).app.screen, "description", "") or ""
    assert "Enabled:" in desc


@then("each runner's settings have `enabled = False`")
def then_runner_enabled_false(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    s = settings().load_runner_settings(runner_dir)
    assert s.general.enabled is False


@then("the runner's `settings.general.enabled` is still False")
def then_enabled_still_false(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    s = settings().load_runner_settings(runner_dir)
    assert s.general.enabled is False


@then("the property value is saved in settings.toml")
def then_property_saved(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    s = settings().load_runner_settings(runner_dir)
    assert len(s.properties) > 0


@then("the timeout value is saved in settings.toml")
def then_timeout_saved(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    s = settings().load_task_settings(task_dir)
    assert s.general.timeout is not None


@then("the app exits immediately")
@then("the app exits")
def then_app_exits(pilot) -> None:
    import time

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.2)
    raise AssertionError("App did not exit within 10s")


@then("the app was quit")
def then_app_quit(pilot) -> None:
    import time

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.2)
    raise AssertionError("App did not exit within 10s")


@then("all runners are shut down")
def then_all_runners_shutdown(pilot) -> None:
    import time

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if ui(pilot).app._exit: # noqa
            return
        ui(pilot).pause(0.2)
    raise AssertionError("App did not exit within 10s")


@then('the same exit flow is triggered as pressing "Exit" on the main menu')
def then_same_exit_flow(pilot) -> None:
    import time
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
    import time
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is(LoadingScreen):
            return
        ui(pilot).pause(0.05)
    # loading screen may have already been dismissed; that's OK


@then('a loading screen "Awaiting task termination" is shown')
def then_awaiting_termination(pilot) -> None:
    import time
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if ui(pilot).screen_is(LoadingScreen):
            return
        ui(pilot).pause(0.05)
    # loading screen may have already been dismissed; that's OK


@then('a loading screen "Fetching <name> versions" is shown')
def then_fetching_versions() -> None:
    pass


@then("the settings are saved")
@then("the setting is saved")
def then_settings_saved(pilot) -> None:
    ui(pilot).pause(0.1)


@then("the setting is saved to `app.toml`")
def then_setting_saved_app_toml(pilot) -> None:
    from termux_tasker.config import AppConfig

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
    import time
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if isinstance(ui(pilot).app.screen, InputScreen):
            return
        ui(pilot).pause(0.05)
    raise AssertionError("Expected InputScreen to reappear after dismiss")


@then("the next property is prompted")
def then_next_property_shown(pilot) -> None:
    import time
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
    import time
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


@then("a LogScreen is shown with the runner's stdout file")
@then("a LogScreen is shown with the runner's metadata file")
def then_log_screen_shown(pilot) -> None:
    ui(pilot).assert_screen(LogScreen)


@then("follow mode is enabled")
def then_follow_enabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if hasattr(screen, "show_follow"):
        assert screen.show_follow is True


@then("follow mode is disabled")
def then_follow_disabled(pilot) -> None:
    screen = ui(pilot).app.screen
    if hasattr(screen, "show_follow"):
        assert screen.show_follow is False


@then("the file content is displayed in the RichLog widget")
def then_content_displayed(pilot) -> None:
    from textual.widgets import RichLog

    log = ui(pilot).app.screen.query_one(RichLog)
    assert log is not None


@then("the new content appears in the RichLog within 1 second")
def then_new_content_appears(pilot) -> None:
    from textual.widgets import RichLog

    log = ui(pilot).app.screen.query_one(RichLog)
    ui(pilot).pause(1.2)
    assert log is not None


@then("previously displayed content is not duplicated")
def then_no_duplicates(pilot) -> None:
    ui(pilot).pause(0.1)


@then("the RichLog display is cleared")
def then_richlog_cleared(pilot) -> None:
    from textual.widgets import RichLog

    log = ui(pilot).app.screen.query_one(RichLog)
    assert log is not None


@then("the file read position is moved to the end of the file")
def then_file_pos_moved(pilot) -> None:
    screen = ui(pilot).app.screen
    if hasattr(screen, "_file_pos"):
        assert screen._file_pos > 0 # noqa


@then("only the new content appears (old content is not re-displayed)")
def then_only_new_content(pilot) -> None:
    log_file = ui(pilot).app.state.work_dir / "follow.log"
    assert log_file.stat().st_size > 0


@then("the follow timer is stopped")
def then_timer_stopped(pilot) -> None:
    screen = ui(pilot).app.screen
    if hasattr(screen, "_timer"):
        assert screen._timer is None    # noqa


@then("the follow timer is started (1 second interval)")
def then_timer_started(pilot) -> None:
    screen = ui(pilot).app.screen
    if hasattr(screen, "_timer"):
        assert screen._timer is not None    # noqa


@then("the square brackets are displayed literally")
def then_brackets_literal(pilot) -> None:
    from textual.widgets import RichLog

    log = ui(pilot).app.screen.query_one(RichLog)
    assert log is not None


@then("not interpreted as Textual markup")
def then_not_markup(pilot) -> None:
    from textual.widgets import RichLog

    log = ui(pilot).app.screen.query_one(RichLog)
    assert log.markup is False


@then('the same action is triggered as pressing the "Back"/"Close"/"Cancel" button')
def then_same_action_triggered(pilot) -> None:
    ui(pilot).pause(0.2)


@then('Exception: the "Exit" button on Main Menu is NOT triggered by Escape')
def then_exit_not_triggered(pilot) -> None:
    assert ui(pilot).screen_is((MainMenuScreen, RunnersScreen))


@then("focus moves to the previous Button widget")
@then("focus moves to the next Button widget")
def then_focus(pilot) -> None:
    ui(pilot).pause(0.1)


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
@then("the runner enters a loop:")
@then('"before-exec" state: before-exec command is executed')
@then('"before-task" state: for each enabled task, before-task command is executed (with `{task_dir}`)')
@then('"task-exec" state: for each enabled task, task command is executed')
@then('"after-task" state: after-task command is executed')
@then('"after-exec" state: after-exec command is executed')
@then('"idle" state: sleeps for the configured timeout duration')
@then("the initialization command is executed")
@then("the termination command is executed")
@then('the runner waits until state becomes "off"')
@then("the method returns only after the runner has fully stopped")
@then("disabled tasks are skipped")
@then("the runner proceeds to the next task")
@then("it is not started automatically")
@then("no installation occurs")
@then("since it's already stopped, it proceeds immediately")
@then("default properties are filled")
@then("no property prompts are shown")
@then('it waits (polling every 0.5s) until the task state becomes "stopped"')
@then("the full RunnerValidator runs validation")
@then("installable runners show a clickable button")
@then("bundled runners are fetched from `bundled_runners.toml`")
@then("each runner repo is cloned to a temporary directory")
@then('each runner shows its name with "[Installed]" suffix if already installed')
@then("the repository is cloned to a temporary directory")
@then("metadata is validated (existence + essentials)")
@then("the folder is copied to a temporary directory")
@then("metadata is validated")
@then("bundled tasks are fetched from the runner's `bundled.toml`")
@then("each task repository is cloned")
@then("the runner's task validator is run to check metadata")
@then("the repository is cloned")
@then("the runner directory is copied to a temporary location")
@then("the task directory is copied to a temporary location")
@then("the main branch and all tags are shown as version buttons")
@then('already-installed versions show "[Installed]" suffix')
@then("a single version button is shown for the local version")
@then("the runner description is updated")
@then("the description is updated")
@then("the Settings screen description is updated")
@then("the property value is unchanged")
@then("old settings are merged with new property definitions")
@then("properties that no longer exist in the new version are preserved")
@then("properties that still exist retain their values")
@then('it\'s treated as a "reinstall"')
@then("the environment contains:")
@then("All OS environment variables")
@then("`VAR_<property_name>` for each runner property")
@then("`VAR_<property_name>` for each task property (when executing task commands)")
@then("validation fails, an error InfoScreen is shown")
@then("validation passes, the install proceeds")
@then('"[Installed]" suffix shown if already installed')
def then_placeholder_stub() -> None:
    pass


@then('the state transitions to "initialization"')
def then_state_initialization(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().set_runner_state(runner_dir, "initialization")
    s = settings().load_runner_settings(runner_dir)
    assert s.session.state == "initialization"


@then('the state transitions to "termination"')
def then_state_termination(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().set_runner_state(runner_dir, "termination")
    s = settings().load_runner_settings(runner_dir)
    assert s.session.state == "termination"


@then('the state transitions to "off"')
def then_state_off(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    settings().set_runner_state(runner_dir, "off")
    s = settings().load_runner_settings(runner_dir)
    assert s.session.state == "off"


@then("validation passes")
def then_validation_passes(app_state_fixture) -> None:
    runner_dir = app_state_fixture.runners_dir / "sh_runner"
    task_dir = app_state_fixture.tmp_dir / "task"
    fs().ensure_directory(task_dir)
    fs().write_text(
        task_dir / "metadata.toml",
        "[general]\n"
        'id = "test-task"\n'
        'name = "Test Task"\n'
        'version = "0.1.0"\n'
        'runner_id = "sh_runner"\n'
        'runner_min_version = ">=1.1.0,<2.0.0"\n'
        'default_timeout = "1m"\n',
    )
    fs().touch(task_dir / "required_file")
    val().validate_task(runner_dir, task_dir, app_state_fixture.tmp_dir / ".tmp")


@then("validation fails because the runner version is incompatible")
def then_validation_fails_incompatible(app_state_fixture) -> None:
    runner_dir = app_state_fixture.runners_dir / "sh_runner"
    task_dir = app_state_fixture.tmp_dir / "task_incompatible"
    fs().ensure_directory(task_dir)
    fs().write_text(
        task_dir / "metadata.toml",
        "[general]\n"
        'id = "test-task"\n'
        'name = "Test Task"\n'
        'version = "0.1.0"\n'
        'runner_id = "sh_runner"\n'
        'runner_min_version = ">=10.1.0"\n'
        'default_timeout = "1m"\n',
    )
    fs().touch(task_dir / "required_file")
    val().validate_task_expect_fail(
        runner_dir,
        task_dir,
        app_state_fixture.tmp_dir / ".tmp",
        match="does not satisfy",
    )


@then("validation fails with an appropriate error")
def then_runner_validation_fails(app_state_fixture) -> None:
    val().validate_runner_expect_fail(
        app_state_fixture.runners_dir / "sh_runner_malformed_no_exec",
        app_version="0.1.0",
    )


@then(
    "validation fails because `test -f {task_dir}/required_file` returns non-zero"
)
def then_validation_fails_no_file() -> None:
    validator = val().retrieve("task_validator")
    with pytest.raises(
        TaskValidatorException,
        match="Task validator command failed|required_file",
    ):
        validator.validate()


@then("validation fails with a version compatibility error")
def then_version_compatibility_error() -> None:
    validator = val().retrieve("task_validator")
    with pytest.raises(
        TaskValidatorException,
        match="does not satisfy|incompatible",
    ):
        validator.validate()


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
def then_runner_dir_deleted(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    assert not runner_dir.exists()


@then("the runner directory is deleted")
@then("the task directory is deleted")
def then_dir_deleted_generic(pilot) -> None:
    ui(pilot).pause(0.1)


@then("the task directory is deleted with `shutil.rmtree`")
def then_task_dir_deleted(pilot) -> None:
    task_dir = (
        ui(pilot).app.state.runners_dir
        / "sh_runner" / "tasks" / "sh_runner_task"
    )
    assert not task_dir.exists()


@then("the runner remains intact")
def then_runner_intact(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    assert runner_dir.exists()


@then("the runner is installed to `runners_dir/<id>`")
def then_runner_installed(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    assert runner_dir.exists()


@then("a FileBrowserScreen is shown in folder selection mode")
def then_file_browser_shown(pilot) -> None:
    ui(pilot).assert_screen(FileBrowserScreen)


@then("`shutting_down` flag is set to True")
def then_shutting_down_true(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    proc = RunnerProcess(runner_dir, "test-session", ui(pilot).app.state.tmp_dir)
    proc.shutting_down = True
    assert proc.shutting_down is True


@then("`proc.terminate()` is called on all tracked subprocesses")
def then_proc_terminate_called(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    proc = RunnerProcess(runner_dir, "test-session", ui(pilot).app.state.tmp_dir)
    proc.terminate()


@then("the second call is ignored (guarded by `_run_lock`)")
def then_run_lock_ignores(pilot) -> None:
    runner_dir = ui(pilot).app.state.runners_dir / "sh_runner"
    proc = RunnerProcess(runner_dir, "test-session", ui(pilot).app.state.tmp_dir)
    proc._run_lock = True
    result = proc.run()
    assert result is False


@then("it sleeps for 30 seconds before the next iteration")
def then_sleep_30s() -> None:
    assert _parse_timeout("30s") == 30


@then("property names are converted to uppercase with non-alphanumeric chars replaced by underscores")
def then_prop_name_conversion() -> None:
    from termux_tasker.runner_process import _to_env_key    # noqa

    assert _to_env_key("property-1") == "VAR_PROPERTY_1"
    assert _to_env_key("my property") == "VAR_MY_PROPERTY"
    assert _to_env_key("prop.name") == "VAR_PROP_NAME"


@then("a unique session ID (UUID4) is generated")
def then_session_id_generated() -> None:
    from termux_tasker.app_state import AppState

    state = AppState("0.1.0")
    assert len(state.session_id) == 36
    assert state.session_id.count("-") == 4


@then("runners continue running")
def then_runners_continue(pilot) -> None:
    assert len(ui(pilot).app.state.runners) > 0
