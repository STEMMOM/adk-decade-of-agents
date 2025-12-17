import time


def now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Observer:
    def __init__(self):
        self.logs = []
        self.traces = []
        self.metrics = {
            "total_events": 0,
            "tool_calls": 0,
            "errors": 0,
            "execution_steps": 0,
        }

    # LOGGING -----------------------------------------------------
    def log(self, message: str):
        entry = f"[LOG] {now_ts()} — {message}"
        self.logs.append(entry)
        print(entry)

    # TRACING -----------------------------------------------------
    def trace(self, step: int, message: str):
        entry = f"[TRACE] step {step}: {message}"
        self.traces.append(entry)
        print(entry)
        self.metrics["execution_steps"] += 1

    # METRICS -----------------------------------------------------
    def inc(self, key: str):
        if key in self.metrics:
            self.metrics[key] += 1

    # FINAL EXPORT ------------------------------------------------
    def dump(self):
        return {
            "logs": self.logs,
            "traces": self.traces,
            "metrics": self.metrics,
        }
