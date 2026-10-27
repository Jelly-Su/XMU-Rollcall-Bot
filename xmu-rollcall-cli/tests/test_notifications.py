import subprocess
import unittest
from unittest.mock import Mock

from xmu_rollcall.notifications import RollcallNotifier


def rollcall(rollcall_id, course="测试课程", is_number=True, is_radar=False):
    return {
        "rollcall_id": rollcall_id,
        "course_title": course,
        "is_number": is_number,
        "is_radar": is_radar,
    }


class NotificationTests(unittest.TestCase):
    def test_termux_notification_uses_sound_and_vibration(self):
        runner = Mock(
            return_value=subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        )
        notifier = RollcallNotifier(
            command_finder=lambda name: "/data/data/com.termux/files/usr/bin/termux-notification",
            runner=runner,
        )

        sent = notifier.notify_new({"rollcalls": [rollcall(101)]})

        self.assertTrue(sent)
        command = runner.call_args.args[0]
        self.assertIn("--sound", command)
        self.assertIn("--vibrate", command)
        self.assertIn("测试课程（数字签到）", command)

    def test_same_rollcall_only_notifies_once(self):
        runner = Mock(
            return_value=subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        )
        notifier = RollcallNotifier(command_finder=lambda name: name, runner=runner)
        data = {"rollcalls": [rollcall(101)]}

        self.assertTrue(notifier.notify_new(data))
        self.assertFalse(notifier.notify_new(data))
        self.assertEqual(runner.call_count, 1)

    def test_missing_termux_api_falls_back_without_crashing(self):
        runner = Mock()
        notifier = RollcallNotifier(command_finder=lambda name: None, runner=runner)

        sent = notifier.notify_new({"rollcalls": [rollcall(101)]})

        self.assertFalse(sent)
        runner.assert_not_called()

    def test_new_id_triggers_another_notification(self):
        runner = Mock(
            return_value=subprocess.CompletedProcess([], returncode=0, stdout="", stderr="")
        )
        notifier = RollcallNotifier(command_finder=lambda name: name, runner=runner)

        notifier.notify_new({"rollcalls": [rollcall(101)]})
        notifier.notify_new({"rollcalls": [rollcall(101), rollcall(102, "第二门课")]})

        self.assertEqual(runner.call_count, 2)


if __name__ == "__main__":
    unittest.main()

