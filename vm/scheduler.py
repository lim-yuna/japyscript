"""
JapyScript — green-thread scheduler for async / await.

The scheduler implements cooperative multitasking over generator-based
coroutines. `async def` functions compile to generator functions; `await`
yields a `_Yield` sentinel back to the scheduler, which resumes the task when
the awaited value is ready.

This module is the reference scheduler. Production VMs may implement the same
public interface over OS threads or an event loop; the observable semantics
are identical.
"""

from __future__ import annotations
from collections import deque
from typing import Any, Callable, Generator


class JpyAsyncError(Exception):
    pass


class _Yield:
    """Sentinel yielded to the scheduler by an `await` expression."""
    __slots__ = ("awaited",)

    def __init__(self, awaited):
        self.awaited = awaited

    def __repr__(self):
        return f"_Yield({self.awaited!r})"


class Task:
    """A scheduled coroutine."""

    __slots__ = ("gen", "name", "state", "result", "error", "waiters")

    PENDING   = "pending"
    RUNNING   = "running"
    SUSPENDED = "suspended"
    DONE      = "done"
    FAILED    = "failed"

    def __init__(self, gen, name=None):
        self.gen = gen
        self.name = name or f"task-{id(gen):x}"
        self.state = Task.PENDING
        self.result = None
        self.error = None
        self.waiters: list[Task] = []

    def done(self) -> bool:
        return self.state in (Task.DONE, Task.FAILED)

    def __repr__(self):
        return f"Task({self.name}, {self.state})"


class Scheduler:
    """Cooperative single-threaded event loop."""

    def __init__(self):
        self.ready: deque[Task] = deque()
        self.timers: list[tuple[float, Task]] = []
        self.future_callbacks: dict[int, list[Callable[[Any], None]]] = {}
        self.futures: dict[int, Any] = {}
        self.running = False

    # ---- public API -------------------------------------------------------
    def spawn(self, gen, name=None) -> Task:
        """Register a new coroutine with the scheduler."""
        task = Task(gen, name)
        self.ready.append(task)
        return task

    def await_value(self, task: Task, awaited) -> Any:
        """Suspend `task` until `awaited` resolves."""
        if isinstance(awaited, Task):
            if awaited.done():
                if awaited.state == Task.FAILED:
                    raise awaited.error
                return awaited.result
            awaited.waiters.append(task)
            task.state = Task.SUSPENDED
            return _Yield(awaited)
        # Plain value: no suspension needed.
        return awaited

    def sleep(self, task: Task, seconds: float) -> Any:
        """Suspend `task` for at least `seconds`."""
        import time
        self.timers.append((time.monotonic() + seconds, task))
        task.state = Task.SUSPENDED
        return _Yield(None)

    # ---- loop -------------------------------------------------------------
    def run_until_complete(self, main_task: Task) -> Any:
        self.running = True
        self.ready.append(main_task)
        while not main_task.done() and self.running:
            self.tick()
        if main_task.state == Task.FAILED:
            raise main_task.error
        return main_task.result

    def tick(self) -> None:
        import time
        # Wake any expired timers.
        now = time.monotonic()
        still_waiting = []
        for when, task in self.timers:
            if when <= now:
                self.ready.append(task)
            else:
                still_waiting.append((when, task))
        self.timers = still_waiting

        if not self.ready:
            return

        task = self.ready.popleft()
        self._step(task)

    def _step(self, task: Task) -> None:
        task.state = Task.RUNNING
        try:
            yielded = next(task.gen)
        except StopIteration as stop:
            task.state = Task.DONE
            task.result = stop.value
            self._wake_waiters(task)
            return
        except BaseException as exc:
            task.state = Task.FAILED
            task.error = exc
            self._wake_waiters(task)
            return

        if isinstance(yielded, _Yield) and isinstance(yielded.awaited, Task):
            task.state = Task.SUSPENDED
            return

        # Any other yielded value: immediately eligible again.
        task.state = Task.PENDING
        self.ready.append(task)

    def _wake_waiters(self, task: Task) -> None:
        for waiter in task.waiters:
            self.ready.append(waiter)
        task.waiters.clear()

    def stop(self) -> None:
        self.running = False


def run(coroutine):
    """Run a top-level coroutine to completion and return its result."""
    sched = Scheduler()
    task = sched.spawn(coroutine, name="main")
    return sched.run_until_complete(task)
