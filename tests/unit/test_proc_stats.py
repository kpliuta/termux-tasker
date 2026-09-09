from __future__ import annotations

import os
from pathlib import Path

from termux_tasker import proc_stats
from termux_tasker.proc_stats import (
    cpu_percent_delta,
    cpu_percent_total,
    format_bytes,
    format_cpu,
    proc_stat,
    system_summary,
    tree_cpu_percent,
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
    "voluntary_ctxt_switches:\t10\n"
    "nonvoluntary_ctxt_switches:\t2\n"
)

# comm in parens, then state ppid pgrp session tty tpgid flags minflt
# cminflt majflt cmajflt utime stime cutime cstime ... (utime idx 11, stime idx 12)
STAT_TEMPLATE = "{pid} ({name}) S {ppid} 1 1 0 -1 0 0 0 0 0 {utime} {stime} 0 0 20 0 2 0 0 0 0\n"


def _write_proc(proc_root: Path, pid: int, ppid: int, rss_kb: int = 1024) -> None:
    pid_dir = proc_root / str(pid)
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "status").write_text(
        STATUS_TEMPLATE.format(name="testproc", ppid=ppid, threads=2, vms_kb=4096, rss_kb=rss_kb)
    )
    (pid_dir / "stat").write_text(
        STAT_TEMPLATE.format(pid=pid, name="testproc", ppid=ppid, utime=100, stime=50)
    )
    (pid_dir / "fd").mkdir(exist_ok=True)


class TestSystemSummary:
    def test_live_machine_has_memory(self) -> None:
        summary = system_summary()
        assert summary.mem_total is not None and summary.mem_total > 0
        assert summary.cpu_count is not None and summary.cpu_count >= 1

    def test_fake_meminfo(self, tmp_path: Path) -> None:
        (tmp_path / "meminfo").write_text(MEMINFO)
        summary = system_summary(tmp_path)
        assert summary.mem_total == 8000000 * 1024
        assert summary.mem_available == 4000000 * 1024
        assert summary.mem_percent == 50.0

    def test_missing_meminfo_gives_nones(self, tmp_path: Path) -> None:
        summary = system_summary(tmp_path)
        assert summary.mem_total is None
        assert summary.mem_percent is None


class TestProcStat:
    def test_live_self_pid(self) -> None:
        stat = proc_stat(os.getpid())
        assert stat is not None
        assert stat.rss is not None and stat.rss > 0
        assert stat.threads is not None and stat.threads >= 1

    def test_missing_pid_returns_none(self, tmp_path: Path) -> None:
        assert proc_stat(123456, tmp_path) is None

    def test_fake_proc(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1)
        stat = proc_stat(100, tmp_path)
        assert stat is not None
        assert stat.name == "testproc"
        assert stat.rss == 1024 * 1024
        assert stat.vms == 4096 * 1024
        assert stat.threads == 2
        assert stat.cpu_s is not None and stat.cpu_s > 0
        assert stat.num_fds == 0


class TestTreeStats:
    def test_empty_roots(self, tmp_path: Path) -> None:
        result = tree_stats([], tmp_path)
        assert result.num_procs == 0
        assert result.rss_total == 0

    def test_parent_plus_child_aggregated(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1, rss_kb=1024)
        _write_proc(tmp_path, 101, 100, rss_kb=2048)
        result = tree_stats([100], tmp_path)
        assert result.num_procs == 2
        assert result.rss_total == 3 * 1024 * 1024
        assert sorted(result.pids) == [100, 101]

    def test_unrelated_pid_excluded(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1)
        _write_proc(tmp_path, 200, 1)
        result = tree_stats([100], tmp_path)
        assert result.num_procs == 1
        assert result.pids == (100,)

    def test_gone_root_skipped(self, tmp_path: Path) -> None:
        result = tree_stats([999999], tmp_path)
        assert result.num_procs == 0

    def test_live_self_tree(self) -> None:
        result = tree_stats([os.getpid()])
        assert result.num_procs >= 1
        assert os.getpid() in result.pids


class TestCpuPercent:
    def test_delta_needs_two_samples(self) -> None:
        assert cpu_percent_delta("test-once", 1.0, now=1000.0) is None

    def test_delta_computes_percent(self) -> None:
        assert cpu_percent_delta("test-pct", 1.0, now=1000.0) is None
        assert cpu_percent_delta("test-pct", 1.5, now=1001.0) == 50.0

    def test_delta_backwards_counter_returns_none(self) -> None:
        assert cpu_percent_delta("test-back", 2.0, now=1000.0) is None
        assert cpu_percent_delta("test-back", 1.0, now=1001.0) is None

    def test_delta_zero_wall_time_returns_none(self) -> None:
        assert cpu_percent_delta("test-zero", 1.0, now=1000.0) is None
        assert cpu_percent_delta("test-zero", 2.0, now=1000.0) is None

    def test_total_needs_two_samples(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu  100 0 0 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0) is None

    def test_total_computes_busy_percent(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu  100 0 0 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=2) is None
        (tmp_path / "stat").write_text("cpu  200 0 0 900 0 0 0 0 0 0\n")
        # +100 busy ticks over 2s wall time, normalized by 2 cores
        assert cpu_percent_total(tmp_path, now=1002.0, cpu_count=2) == 25.0

    def test_total_finds_aggregate_past_first_line(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("cpu  100 0 0 800 0 0 0 0 0 0\n")
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=1) is None
        (tmp_path / "stat").write_text(
            "intr 12345\ncpu  200 0 0 900 0 0 0 0 0 0\ncpu0  200 0 0 900 0 0 0 0 0 0\n"
        )
        assert cpu_percent_total(tmp_path, now=1002.0, cpu_count=1) == 50.0

    def test_total_falls_back_to_per_core_lines(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text(
            "cpu0  100 0 0 800 0 0 0 0 0 0\ncpu1  100 0 0 800 0 0 0 0 0 0\n"
        )
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=2) is None
        (tmp_path / "stat").write_text(
            "cpu0  200 0 0 900 0 0 0 0 0 0\ncpu1  200 0 0 900 0 0 0 0 0 0\n"
        )
        # +200 busy ticks over 2s wall time, normalized by 2 cores
        assert cpu_percent_total(tmp_path, now=1002.0, cpu_count=2) == 50.0

    def test_total_garbage_stat_returns_none(self, tmp_path: Path) -> None:
        (tmp_path / "stat").write_text("nothing useful here\n")
        assert cpu_percent_total(tmp_path) is None

    def test_total_falls_back_to_proc_scan(self, tmp_path: Path) -> None:
        # No "stat" file at all (locked-down kernel) — only per-PID stats.
        _write_proc(tmp_path, 100, 1)
        assert cpu_percent_total(tmp_path, now=1000.0, cpu_count=1) is None
        pid_dir = tmp_path / "100"
        (pid_dir / "stat").write_text(
            STAT_TEMPLATE.format(pid=100, name="testproc", ppid=1, utime=200, stime=50)
        )
        # +100 ticks = 1.0s over 1s wall time on 1 core
        assert cpu_percent_total(tmp_path, now=1001.0, cpu_count=1) == 100.0

    def test_total_scan_nothing_visible_returns_none(self, tmp_path: Path) -> None:
        assert cpu_percent_total(tmp_path) is None

    def test_total_missing_stat_returns_none(self, tmp_path: Path) -> None:
        assert cpu_percent_total(tmp_path) is None

    def test_tree_percent_two_samples(self, tmp_path: Path) -> None:
        _write_proc(tmp_path, 100, 1)
        assert tree_cpu_percent([100], tmp_path, now=1000.0) is None
        pid_dir = tmp_path / "100"
        (pid_dir / "stat").write_text(
            STAT_TEMPLATE.format(pid=100, name="testproc", ppid=1, utime=150, stime=50)
        )
        assert tree_cpu_percent([100], tmp_path, now=1001.0) == 50.0

    def test_tree_percent_empty_or_gone(self, tmp_path: Path) -> None:
        assert tree_cpu_percent([], tmp_path) is None
        assert tree_cpu_percent([999999], tmp_path) is None


class TestFormat:
    def test_bytes_none(self) -> None:
        assert format_bytes(None) == "n/a"

    def test_bytes_mib(self) -> None:
        assert format_bytes(30 * 1024 * 1024) == "30.0 MiB"

    def test_bytes_gib(self) -> None:
        assert format_bytes(2 * 1024 * 1024 * 1024) == "2.0 GiB"

    def test_cpu_none(self) -> None:
        assert format_cpu(None) == "n/a"

    def test_cpu_value(self) -> None:
        assert format_cpu(12.345) == "12.3s"

    def test_proc_stats_module_importable(self) -> None:
        assert proc_stats._CLK_TCK > 0
