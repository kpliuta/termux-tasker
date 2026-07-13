"""Sync bridge to drive a running Textual app via the Pilot API."""

from __future__ import annotations

import asyncio
import queue
import threading
from concurrent.futures import Future
from typing import Any, Callable

from textual.app import App
from textual.css.query import NoMatches, TooManyMatches
from textual.pilot import Pilot, OutOfBounds
from textual.widgets import Button, Checkbox


class PilotDriver:
    """Drives a Textual app from sync code by running it on a background thread.

    Usage:
        app = TermuxTaskerApp(app_version="0.1.0")
        driver = PilotDriver(app)
        driver.start()
        driver.click("#my_button")
        assert "expected" in driver.app.screen.title
        driver.stop()
    """

    def __init__(self, app: App, size: tuple[int, int] = (80, 40)):
        self._app = app
        self._size = size
        self._pilot: Pilot | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stop_flag = False
        self._exception: BaseException | None = None
        self._cmd_queue: queue.SimpleQueue[tuple[Callable, Future]] = (
            queue.SimpleQueue()
        )
        self._async_cmd_event: asyncio.Event | None = None

    # -- public helpers -------------------------------------------------------

    @property
    def pilot(self) -> Pilot:
        assert self._pilot is not None, "driver not started yet"
        return self._pilot

    @property
    def app(self) -> Any:
        return self.pilot.app

    def start(self, timeout: float = 10) -> PilotDriver:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        assert self._thread is not None
        self._thread.start()
        if not self._ready.wait(timeout):
            raise RuntimeError("Timed out waiting for the app to start")
        if self._exception:
            raise RuntimeError("App failed to start") from self._exception
        return self

    def stop(self, timeout: float = 5) -> None:
        self._stop_flag = True
        if self._thread is not None:
            self._thread.join(timeout)

    # -- Public action methods -----------------------------------------------

    def press(self, *keys: str) -> Any:
        return self._submit(lambda p: p.press(*keys))

    def pause(self, delay: float = 0.02) -> Any:
        return self._submit(lambda p: p.pause(delay))

    def resize_terminal(self, width: int, height: int) -> Any:
        return self._submit(lambda p: p.resize_terminal(width, height))

    def wait_for_animation(self) -> Any:
        return self._submit(lambda p: p.wait_for_animation())

    def push_screen(self, screen: Any = None, *, factory: Callable | None = None) -> Any:
        if factory is not None:
            return self._submit(
                lambda p: p.app.push_screen(factory())
            )
        else:
            return self._submit(
                lambda p: p.app.push_screen(screen)
            )

    def pop_screen(self) -> Any:
        return self._submit(lambda p: p.app.pop_screen())

    def run_on_pilot(self, make_coro: Callable) -> Any:
        """Submit a callable ``(Pilot) -> Awaitable`` and block until done.

        Allows external callers to execute arbitrary async code on the
        background thread's event loop, bypassing the public action methods.
        """
        return self._submit(make_coro)

    def exit_app(self) -> Any:
        def _do(pilot: Any) -> Any:
            pilot.app.exit()
            return asyncio.sleep(0)
        return self._submit(_do)

    def set_value(self, selector: str, value: str, timeout: float = 5) -> Any:
        async def _do(pilot: Any) -> None:
            import time
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    widget = pilot.app.screen.query_one(selector)
                except (NoMatches, TooManyMatches):
                    await pilot.pause(0.02)
                    continue
                try:
                    widget.value = value
                    await asyncio.sleep(0)
                    return
                except (AttributeError, TypeError, AssertionError):
                    await pilot.pause(0.02)
            raise AssertionError(f"Timed out waiting for {selector!r}")
        return self._submit(_do)

    def click(self, selector: str, timeout: float = 5) -> Any:
        async def _do(pilot: Any) -> None:
            import time
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    widget = pilot.app.screen.query_one(selector)
                    if isinstance(widget, Button):
                        try:
                            widget.scroll_visible()
                        except Exception:
                            pass
                        widget.press()
                        await pilot.pause()
                    elif isinstance(widget, Checkbox):
                        widget.toggle()
                    else:
                        await pilot.click(widget)
                    return
                except (AttributeError, TypeError, AssertionError, OutOfBounds):
                    await pilot.pause(0.02)
            raise AssertionError(f"Timed out clicking {selector!r}")
        return self._submit(_do)

    def wait_until_screen(self, screen_type: type, timeout: float = 5) -> None:
        """Block until the current screen is an instance of *screen_type*."""
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pause(0.01)
            if isinstance(self.app.screen, screen_type):
                return
        raise AssertionError(
            f"Timed out waiting for screen {screen_type.__name__}"
        )

    # -- internals ------------------------------------------------------------

    def _run(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        except Exception as exc:
            self._exception = exc
            self._ready.set()
        finally:
            self._loop.close()

    async def _main(self) -> None:
        async with self._app.run_test(size=self._size) as pilot:
            self._pilot = pilot
            self._async_cmd_event = asyncio.Event()
            self._ready.set()
            while not self._stop_flag:
                while not self._cmd_queue.empty():
                    make_coro, future = self._cmd_queue.get_nowait()
                    try:
                        coro = make_coro(pilot)
                        result = await coro
                        future.set_result(result)
                    except BaseException as exc:
                        future.set_exception(exc)
                self._async_cmd_event.clear()
                try:
                    await asyncio.wait_for(self._async_cmd_event.wait(), timeout=0.01)
                except asyncio.TimeoutError:
                    pass

    def _submit(self, make_coro: Callable) -> Any:
        """Submit a command to be executed in the background thread.

        *make_coro* is a callable ``(Pilot) -> Awaitable`` that will be
        called on the background thread.  The returned awaitable is
        awaited and the result is returned to the caller.
        """
        future: Future = Future()
        self._cmd_queue.put((make_coro, future))
        if self._async_cmd_event is not None and self._loop is not None:
            self._loop.call_soon_threadsafe(self._async_cmd_event.set)
        return future.result()
