# adk_runtime/trace_context.py
import uuid

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


