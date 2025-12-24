# adk_runtime/trace_context.py
import uuid
import contextvars

# Process-level identity context (system/process/run) — authoritative run_id from boot.
_system_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("system_id", default=None)
_process_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("process_id", default=None)
_run_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("run_id", default=None)

class TraceContext:
    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self._stack = []

    def new_span(self) -> str:
        span_id = str(uuid.uuid4())
        parent = self._stack[-1] if self._stack else None
        self._stack.append(span_id)
        return span_id, parent

    def end_span(self):
        if self._stack:
            self._stack.pop()


# P09/P10: set/get process-level identities
def set_process_context(system_id: str | None, process_id: str | None, run_id: str | None) -> None:
    _system_id_var.set(system_id)
    _process_id_var.set(process_id)
    _run_id_var.set(run_id)


def get_system_id() -> str | None:
    return _system_id_var.get()


def get_process_id() -> str | None:
    return _process_id_var.get()


def get_run_id() -> str | None:
    return _run_id_var.get()
