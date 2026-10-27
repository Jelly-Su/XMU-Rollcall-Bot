# xmu-rollcall-cli

A command-line tool for monitoring and auto-answering Tronclass rollcalls at Xiamen University.

> This project is intended for personal learning and automation convenience. Use it at your own risk and comply with your school's rules.

## Features

- Login with XMU unified authentication through `xmulogin`
- Continuous rollcall polling (1-second interval)
- Automatic handling for:
  - Number rollcalls (fetch number code and answer directly)
  - Radar rollcalls (location solving)
- Multi-account management in one local config
- Session cookie cache and refresh support
- Android notification, sound, and vibration through Termux:API

## Installation

Install from PyPI:

```bash
pip install xmu-rollcall-cli
```

After installation, these command aliases are available:

- `xmu`
- `xmu-rollcall-cli`
- `XMUrollcall-cli`

## Quick Start

1. Configure at least one account:

```bash
xmu config
```

2. (Optional) Switch active account:

```bash
xmu switch
```

3. Start monitoring:

```bash
xmu start
```

4. If session becomes invalid, refresh cookies:

```bash
xmu refresh
```

## Timed monitoring window

Use local 24-hour time to wait for a monitoring window and exit automatically
when it ends:

```bash
xmu start --from 08:00 --until 10:30
```

Both options are required together. If today's window has already ended, the
command waits for the next day's window. Cross-midnight windows such as
`--from 23:00 --until 01:00` are supported. Keep Termux running and exempt it
from Android battery optimization while waiting or monitoring.

Running `xmu start` without these options keeps the original continuous
monitoring behavior.

## Android notifications in Termux

When a new rollcall is detected, the monitor uses `termux-notification` to show
an Android notification with sound and vibration. Each rollcall id is notified
only once, even if answering is retried.

1. Install the **Termux:API Android app** from the same source/signing family as
   the Termux app. Do not mix F-Droid and GitHub APKs.
2. In Termux, install the command-line client:

```bash
pkg install termux-api
```

3. Allow notifications for Termux:API in Android settings, then test it:

```bash
termux-notification --title "XMU 测试" --content "通知配置成功" --priority high --sound --vibrate 300,200,300
```

If Termux:API is unavailable or a notification fails, monitoring continues and
the program falls back to a terminal bell plus an on-screen alert.

## Commands

- `xmu config` - Add/delete accounts and set current account
- `xmu switch` - Switch the current account
- `xmu start` - Start rollcall monitoring loop
- `xmu refresh` - Remove cached cookies for current account
- `xmu --help` - Show help

## Configuration

The package stores local data in a `.xmu_rollcall` directory:

1. `XMU_ROLLCALL_CONFIG_DIR` (if set)
2. `~/.xmu_rollcall` (default)
3. `./.xmu_rollcall` (fallback when home is not writable)

Main files:

- `config.json`: account list and selected account
- `<account_id>.json`: cached cookies per account

Example (custom config directory):

```bash
export XMU_ROLLCALL_CONFIG_DIR="$HOME/Documents/.xmu_rollcall"
```

## Limitations

- QR code rollcalls are currently **not supported**.
- This tool depends on Tronclass/XMU API behavior and may break if upstream endpoints change.

## Supported Python Versions

- Python 3.7+

## Project Links

- Homepage: https://github.com/KrsMt-0113/XMU-Rollcall-Bot
- Issues: https://github.com/KrsMt-0113/XMU-Rollcall-Bot/issues

## License

MIT License

## Compatibility

Number rollcalls fall back to `/api/timetable_rollcalls` when the detail API does not expose `number_code`.

