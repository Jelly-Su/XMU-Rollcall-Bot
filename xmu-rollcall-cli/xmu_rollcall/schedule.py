"""Local-time scheduling helpers for one monitoring window."""

from datetime import datetime, time as clock_time, timedelta
import re
import time


def parse_clock(value):
    """Parse a strict 24-hour HH:MM value."""
    if not isinstance(value, str) or re.fullmatch(r"\d{2}:\d{2}", value) is None:
        raise ValueError("时间必须使用 24 小时制 HH:MM，例如 08:00。")
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except (TypeError, ValueError) as exc:
        raise ValueError("时间必须使用 24 小时制 HH:MM，例如 08:00。") from exc
    return clock_time(parsed.hour, parsed.minute)


def resolve_monitor_window(now, start_value, end_value):
    """Resolve the current or next occurrence of a local-time window."""
    start_clock = parse_clock(start_value)
    end_clock = parse_clock(end_value)
    if start_clock == end_clock:
        raise ValueError("开始时间和结束时间不能相同。")

    start_at = datetime.combine(now.date(), start_clock)
    end_at = datetime.combine(now.date(), end_clock)

    if end_clock > start_clock:
        if now >= end_at:
            start_at += timedelta(days=1)
            end_at += timedelta(days=1)
        return start_at, end_at

    # Cross-midnight window, for example 23:00-01:00.
    if now.time() < end_clock:
        start_at -= timedelta(days=1)
    else:
        end_at += timedelta(days=1)
    return start_at, end_at


def wait_until(start_at, now_fn=datetime.now, sleep_fn=time.sleep):
    """Wait interruptibly until start_at without busy polling."""
    while True:
        remaining = (start_at - now_fn()).total_seconds()
        if remaining <= 0:
            return
        sleep_fn(min(remaining, 30.0))
