from __future__ import annotations

import os
from pathlib import Path

import pytest

from termux_tasker import proc_stats
from termux_tasker.proc_stats import (
    cpu_percent_delta,
    cpu_percent_total,
    format_bytes,
    proc_stat,
    system_summary,
    tree_stats,
)

MEMINFO = """\
MemTotal:        8000000 kB
MemFree:         2000000 kB
MemAvailable:    4000000 kB
"""

STATUS_TEMPLATE = (
    "Name:\t{name}\n"
    "State:\tS (sleeping)\n"
    "PPid:\t{ppid}\n"
    "Threads:\t{threads}\n"
    "VmSize:\t {vms_kb} kB\n"
    "VmRSS:\t {rss_kb} kB\n"
)

# comm in parens, then: state ppid pgrp session tty tpgid flags minflt
# cminflt majflt cmajflt utime stime ... (utime idx 11, stime idx 12)
STAT_TEMPLATE = "{pid} ({name}) S {ppid} 1 1 0 -1 0 0 0 0 0 {utime} {stime} 0 0 20 0 2 0 0 0 0\n"


@pytest.fixture(autouse=True)
def _clean_cpu_samples():
    proc_stats._prev_samples.clear()    # noqa
    yield
    proc_stats._prev_samples.clear()    # noqa


def _write_proc(
    proc_root: Path, pid: int, ppid: int, rss_kb: int = 1024, utime: int = 100, stime: int = 50
) -> None:
    pid_dir = proc_root / str(pid)
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "status").write_text(
        STATUS_TEMPLATE.format(name="testproc", ppid=ppid, threads=2, vms_kb=4096, rss_kb=rss_kb)
    )
    (pid_dir / "stat").write_text(
        STAT_TEMPLATE.format(pid=pid, name="testproc", ppid=ppid, utime=utime, stime=stime)
    )


class TestSystemSummary:
    def test_live_machine_has_memory(self) -> None:
        summary = system_summary()
        assert summary.mem_total is not None and summary.mem_total > 0
        assert summary.mem_percent is not None and 0 <= summary.mem_percent <= 100

    def test_fake_meminfo(self, tmp_path: Path) -> None:
        (tmp_path / "meminfo").write_text(MEMINFO)
        summary = system_summary(tmp_path)
        assert summary.mem_total == 8000000 * 1024
        assert summary.mem_available == 4000000 * 1024
        assert summary.mem_percent == 50.0

    def test_missing_meminfo_gives_nones(self, tmp_path: Path) -> None:
        summary = system_summary(tmp_path)
        assert summary.mem_total is None
        assert summary.mem_available is None
        assert summary.mem_percent is None


class TestCpuPercent:
    def test_first_sample_returns_none(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu  100 0 100 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=1) is None

    def test_second_sample_computes_percent(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu  100 0 100 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=1) is None
        (tmp_path / "stat").write_text("cpu  150 0 150 850 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1001.0, cpu_count=1) == 100.0

    def test_per_core_fallback(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu0 100 0 100 800 0 0 0 0 0 0\ncpu1 100 0 100 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=2) is None
        (tmp_path / "stat").write_text("cpu0 150 0 150 850 0 0 0 0 0 0\ncpu1 150 0 150 850 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1001.0, cpu_count=2) == 100.0

    def test_unreadable_stat_returns_none(self, tmp_path: Path) -> None:
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=1) is None

    def test_delta_first_call_returns_none(self) -> None:
        assert cpu_percent_delta("test-key", 10.0, now=1000.0) is None

    def test_delta_second_call_computes(self) -> None:
        assert cpu_percent_delta("test-key", 10.0, now=1000.0) is None
        assert cpu_percent_delta("test-key", 10.5, now=1001.0) == 50.0

    def test_delta_backwards_counter_returns_none(self) -> None:
        assert cpu_percent_delta("test-key", 10.0, now=1000.0) is None
        assert cpu_percent_delta("test-key", 9.0, now=1001.0) is None


class TestProcStat:
    def test_live_self_pid(self) -> None:
        stat = proc_stat(os.getpid())
        assert stat is not None
        assert stat.rss is not None and stat.rss > 0

    def test_missing_pid_returns_none(self, tmp_path: Path) -> None:
        assert proc_stat(123456, tmp_path) is None

    def test_fake_proc(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1)
        stat = proc_stat(100, tmp_path)
        assert stat is not None
        assert stat.pid == 100
        assert stat.name == "testproc"
        assert stat.rss == 1024 * 1024


class TestTreeStats:
    def test_empty_roots(self, tmp_path: Path) -> None:
        result = tree_stats([], tmp_path)
        assert result.num_procs == 0
        assert result.rss_total == 0
        assert result.pids == ()

    def test_single_proc(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1, rss_kb=1024)
        result = tree_stats([100], tmp_path)
        assert result.num_procs == 1
        assert result.rss_total == 1024 * 1024
        assert result.pids == (100,)

    def test_parent_and_child_aggregated(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1, rss_kb=1024)
        _write_proc(tmp_path, 101, 100, rss_kb=2048)
        result = tree_stats([100], tmp_path)
        assert result.num_procs == 2
        assert result.rss_total == 3072 * 1024
        assert set(result.pids) == {100, 101}

    def test_unrelated_proc_excluded(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1, rss_kb=1024)
        _write_proc(tmp_path, 200, 1, rss_kb=4096)
        result = tree_stats([100], tmp_path)
        assert result.num_procs == 1
        assert result.rss_total == 1024 * 1024

    def test_gone_root_gives_empty(self, tmp_path: Path) -> None:
        result = tree_stats([99999], tmp_path)
        assert result.num_procs == 0
        assert result.rss_total == 0


class TestFormatBytes:
    def test_none_gives_na(self) -> None:
        assert format_bytes(None) == "n/a"

    def test_negative_gives_na(self) -> None:
        assert format_bytes(-1) == "n/a"

    def test_bytes(self) -> None:
        assert format_bytes(512) == "512 B"

    def test_kibibytes(self) -> None:
        assert format_bytes(2048) == "2.0 KiB"

    def test_mebibytes(self) -> None:
        assert format_bytes(30 * 1024 * 1024) == "30.0 MiB"

    def test_gibibytes(self) -> None:
        assert format_bytes(int(31.3 * 1024**3)) == "31.3 GiB"

    def test_tebibytes(self) -> None:
        assert format_bytes(2 * 1024**4) == "2.0 TiB"
