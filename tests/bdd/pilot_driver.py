"""Sync bridge to drive a running Textual app via the Pilot API."""

from __future__ import annotations

import asyncio
import queue
import threading
from concurrent.futures import Future

from textual.widgets import Button, Checkbox
from textual.pilot import Pilot


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

    def __init__(self, app, size: tuple[int, int] = (80, 40)):
        self._app = app
        self._size = size
        self._pilot: Pilot | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stop_flag = False
        self._exception: BaseException | None = None
        # Queue of (async_callable, Future) pairs
        self._cmd_queue: queue.SimpleQueue[tuple[callable, Future]] = (
            queue.SimpleQueue()
        )

    # -- public helpers -------------------------------------------------------

    @property
    def pilot(self) -> Pilot:
        assert self._pilot is not None, "driver not started yet"
        return self._pilot

    @property
    def app(self):
        return self.pilot.app

    def start(self, timeout: float = 10) -> PilotDriver:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
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

    def press(self, *keys: str):
        return self._submit(lambda p: p.press(*keys))

    def pause(self, delay: float = 0.1):
        return self._submit(lambda p: p.pause(delay))

    def resize_terminal(self, width: int, height: int):
        return self._submit(lambda p: p.resize_terminal(width, height))

    def wait_for_animation(self):
        return self._submit(lambda p: p.wait_for_animation())

    def push_screen(self, screen=None, *, factory=None):
        """Push a screen on the background app's screen stack.

        Accept either an already-created *screen* instance, or a
        zero-argument *factory* callable that creates the screen
        on the background thread.
        """
        if factory is not None:
            return self._submit(
                lambda p: p.app.push_screen(factory())
            )
        else:
            return self._submit(
                lambda p: p.app.push_screen(screen)
            )

    def pop_screen(self):
        return self._submit(lambda p: p.app.pop_screen())

    def exit_app(self):
        def _do(pilot):
            pilot.app.exit()
            return asyncio.sleep(0)
        return self._submit(_do)

    def set_value(self, selector: str, value, timeout: float = 5):
        async def _do(pilot):
            import time
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    widget = pilot.app.screen.query_one(selector)
                except Exception:
                    await pilot.pause(0.05)
                    continue
                try:
                    widget.value = value
                    await asyncio.sleep(0)
                    return
                except Exception:
                    await pilot.pause(0.05)
            raise AssertionError(f"Timed out waiting for {selector!r}")
        return self._submit(_do)

    def click(self, selector: str, timeout: float = 5):
        async def _do(pilot):
            import time
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    widget = pilot.app.screen.query_one(selector)
                    if isinstance(widget, Button):
                        widget.scroll_visible()
                        await pilot.wait_for_animation()
                        await pilot.click(widget)
                    elif isinstance(widget, Checkbox):
                        widget.scroll_visible()
                        await pilot.wait_for_animation()
                        widget.toggle()
                    else:
                        await pilot.click(widget)
                    return
                except Exception:
                    await pilot.pause(0.05)
            raise AssertionError(f"Timed out clicking {selector!r}")
        return self._submit(_do)

    def wait_until_screen(self, screen_type, timeout: float = 5):
        """Block until the current screen is an instance of *screen_type*."""
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pause(0.05)
            if isinstance(self.app.screen, screen_type):
                return
        raise AssertionError(
            f"Timed out waiting for screen {screen_type.__name__}"
        )

    # -- internals ------------------------------------------------------------

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        except Exception as exc:
            self._exception = exc
            self._ready.set()

    async def _main(self) -> None:
        async with self._app.run_test(size=self._size) as pilot:
            self._pilot = pilot
            self._ready.set()
            while not self._stop_flag:
                # Drain submitted commands.
                try:
                    make_coro, future = self._cmd_queue.get_nowait()
                    try:
                        coro = make_coro(pilot)
                        result = await coro
                        future.set_result(result)
                    except BaseException as exc:
                        future.set_exception(exc)
                except queue.Empty:
                    pass
                await asyncio.sleep(0.05)

    def _submit(self, make_coro):
        """Submit a command to be executed in the background thread.

        *make_coro* is a callable ``(Pilot) -> Awaitable`` that will be
        called on the background thread.  The returned awaitable is
        awaited and the result is returned to the caller.
        """
        future: Future = Future()
        self._cmd_queue.put((make_coro, future))
        return future.result()
