from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from termux_tasker.config import AppConfig


@dataclass
class InitIssue:
    message: str
    severity: str = "warning"  # "warning" or "error"


@dataclass
class InitResult:
    issues: list[InitIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def add_warning(self, message: str) -> None:
        self.issues.append(InitIssue(message=message, severity="warning"))

    def add_error(self, message: str) -> None:
        self.issues.append(InitIssue(message=message, severity="error"))


def _is_f_droid_version(termux_version: str) -> bool:
    """Check if the Termux version is from F-Droid (>= 0.118.3).

    Google Play version is notoriously outdated and breaks if `pkg upgrade`
    is run due to bootstrap incompatibilities. Only F-Droid builds can safely
    upgrade.
    """
    parts = re.split(r"[.-]", termux_version)
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch) >= (0, 118, 3)
    except (ValueError, IndexError):
        return False


async def run_android_checks(app_config_file: Path) -> InitResult:
    """Run Android/Termux initialization checks.

    Returns an InitResult containing any issues found.
    """
    result = InitResult()
    is_termux = "TERMUX_VERSION" in os.environ

    if not is_termux:
        result.add_error(
            "Not running in a Termux environment.\n"
            "Use --skip-android-init flag if running locally on a PC."
        )
        return result

    termux_version = os.environ["TERMUX_VERSION"]
    is_f_droid = _is_f_droid_version(termux_version)

    # ── Storage access ──
    sdcard = Path("/sdcard")
    if not sdcard.exists():
        proc = await asyncio.create_subprocess_exec("termux-setup-storage")
        await proc.wait()

        if not sdcard.exists():
            result.add_error(
                "Storage access permission is required.\n"
                "Please run `termux-setup-storage` and grant the permission."
            )
            return result

    # ── Upgrade on startup ──
    cfg = AppConfig.load(app_config_file)
    if cfg.settings.upgrade_on_startup:
        if not is_f_droid:
            result.add_warning(
                "Termux upgrade skipped: Google Play version detected.\n"
                "Upgrading would break the bootstrap. Install Termux from F-Droid instead."
            )
        else:
            env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
            proc = await asyncio.create_subprocess_exec(
                "apt-get", "update", "-y",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env=env,
            )
            await proc.wait()
            if proc.returncode != 0:
                result.add_warning("Termux update failed. Run manually: apt-get update")
                return result

            proc = await asyncio.create_subprocess_exec(
                "apt-get", "dist-upgrade", "-y", "-o", "Dpkg::Options::=--force-confdef",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                env=env,
            )
            await proc.wait()
            if proc.returncode != 0:
                result.add_warning(
                    "Termux upgrade encountered issues. You can retry manually:\n"
                    "  apt-get update && apt-get dist-upgrade"
                )

    return result
