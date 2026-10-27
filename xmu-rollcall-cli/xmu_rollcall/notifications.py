"""Android/Termux notifications for newly detected rollcalls."""

import shutil
import subprocess
import sys


def _rollcall_type(rollcall):
    if rollcall.get("is_radar"):
        return "雷达签到"
    if rollcall.get("is_number"):
        return "数字签到"
    return "二维码签到"


def _notification_text(rollcalls):
    details = []
    for rollcall in rollcalls[:3]:
        course = rollcall.get("course_title") or "未知课程"
        details.append(f"{course}（{_rollcall_type(rollcall)}）")
    if len(rollcalls) > 3:
        details.append(f"另有 {len(rollcalls) - 3} 个签到")
    return "；".join(details)


class RollcallNotifier:
    """Notify once for each rollcall id without making Termux:API mandatory."""

    def __init__(self, command_finder=shutil.which, runner=subprocess.run):
        self._command = command_finder("termux-notification")
        self._runner = runner
        self._notified_ids = set()

    @property
    def android_available(self):
        return self._command is not None

    def notify_new(self, data):
        rollcalls = data.get("rollcalls", [])
        new_rollcalls = []
        for rollcall in rollcalls:
            rollcall_id = rollcall.get("rollcall_id")
            identity = rollcall_id if rollcall_id is not None else repr(rollcall)
            if identity not in self._notified_ids:
                self._notified_ids.add(identity)
                new_rollcalls.append(rollcall)

        if not new_rollcalls:
            return False

        title = f"检测到 {len(new_rollcalls)} 个新签到"
        content = _notification_text(new_rollcalls)

        if self._command:
            try:
                result = self._runner(
                    [
                        self._command,
                        "--id", "xmu-rollcall",
                        "--title", title,
                        "--content", content,
                        "--priority", "high",
                        "--sound",
                        "--vibrate", "300,200,300",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    return True
                error = (result.stderr or result.stdout or "未知错误").strip()
                print(f"\nAndroid 通知发送失败：{error}")
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"\nAndroid 通知发送失败：{exc}")

        # Keep monitoring even when Termux:API is missing or failed.
        sys.stdout.write(f"\a\n[签到提醒] {title}：{content}\n")
        sys.stdout.flush()
        return False

