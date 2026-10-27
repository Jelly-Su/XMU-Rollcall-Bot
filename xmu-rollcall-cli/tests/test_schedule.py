import unittest
from datetime import datetime, timedelta

from xmu_rollcall.schedule import parse_clock, resolve_monitor_window, wait_until


class ScheduleTests(unittest.TestCase):
    def test_same_day_upcoming_window(self):
        now = datetime(2026, 10, 27, 7, 30)
        start, end = resolve_monitor_window(now, "08:00", "10:30")
        self.assertEqual(start, datetime(2026, 10, 27, 8, 0))
        self.assertEqual(end, datetime(2026, 10, 27, 10, 30))

    def test_current_same_day_window_starts_immediately(self):
        now = datetime(2026, 10, 27, 9, 0)
        start, end = resolve_monitor_window(now, "08:00", "10:30")
        self.assertLessEqual(start, now)
        self.assertGreater(end, now)

    def test_passed_same_day_window_uses_next_day(self):
        now = datetime(2026, 10, 27, 11, 0)
        start, end = resolve_monitor_window(now, "08:00", "10:30")
        self.assertEqual(start, datetime(2026, 10, 28, 8, 0))
        self.assertEqual(end, datetime(2026, 10, 28, 10, 30))

    def test_cross_midnight_window_after_midnight(self):
        now = datetime(2026, 10, 28, 0, 30)
        start, end = resolve_monitor_window(now, "23:00", "01:00")
        self.assertEqual(start, datetime(2026, 10, 27, 23, 0))
        self.assertEqual(end, datetime(2026, 10, 28, 1, 0))

    def test_cross_midnight_window_before_start(self):
        now = datetime(2026, 10, 27, 22, 0)
        start, end = resolve_monitor_window(now, "23:00", "01:00")
        self.assertEqual(start, datetime(2026, 10, 27, 23, 0))
        self.assertEqual(end, datetime(2026, 10, 28, 1, 0))

    def test_rejects_invalid_or_zero_length_window(self):
        with self.assertRaises(ValueError):
            parse_clock("8:00")
        with self.assertRaises(ValueError):
            resolve_monitor_window(datetime(2026, 10, 27, 8, 0), "08:00", "08:00")

    def test_wait_until_sleeps_in_bounded_steps(self):
        current = [datetime(2026, 10, 27, 7, 59, 10)]
        sleeps = []

        def now_fn():
            return current[0]

        def sleep_fn(seconds):
            sleeps.append(seconds)
            current[0] += timedelta(seconds=seconds)

        wait_until(datetime(2026, 10, 27, 8, 0), now_fn=now_fn, sleep_fn=sleep_fn)
        self.assertEqual(sleeps, [30.0, 20.0])


if __name__ == "__main__":
    unittest.main()
