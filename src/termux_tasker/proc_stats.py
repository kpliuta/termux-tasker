"""Lightweight /proc-based system and process stats (no third-party deps).

Reads only small text files under /proc, so it stays cheap enough for the
dashboard's 1-second refresh tick on both Termux (Android) and regular Linux.
Every reader degrades to None/empty when a node is missing or hidden
(non-root Android hides foreign PIDs) instead of raising.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

_PROC_ROOT = Path("/proc")


def _clk_tck() -> int:
    try:
        return os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError):
        return 100


_CLK_TCK = _clk_tck()


@dataclass(frozen=True)
class SystemSummary:
    """Machine-wide CPU and memory snapshot; None fields mean unreadable."""

    cpu_percent: float | None
    load_1: float | None
    load_5: float | None
    load_15: float | None
    cpu_count: int | None
    mem_total: int | None
    mem_available: int | None
    mem_percent: float | None


@dataclass(frozen=True)
class ProcStat:
    """Resource snapshot of a single PID; None fields mean hidden/unreadable."""

    pid: int
    name: str | None
    rss: int | None
    vms: int | None
    threads: int | None
    cpu_s: float | None
    num_fds: int | None


@dataclass(frozen=True)
class TreeStats:
    """Aggregate over a root PID plus all its recursive descendants."""

    pids: tuple[int, ...]
    num_procs: int
    rss_total: int
    cpu_s_total: float
    threads_total: int


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _parse_meminfo(text: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            values[parts[0].rstrip(":")] = int(parts[1]) * 1024
        except ValueError:
            continue
    return values


def system_summary(proc_root: Path = _PROC_ROOT) -> SystemSummary:
    """Snapshot CPU percent, load average, CPU count and memory (best-effort).

    ``cpu_percent`` is None on the first call (it needs two samples); the
    dashboard's 1-second tick provides the second one.
    """
    try:
        load_1, load_5, load_15 = os.getloadavg()
    except OSError:
        load_1, load_5, load_15 = None, None, None
    mem_total: int | None = None
    mem_available: int | None = None
    mem_percent: float | None = None
    raw = _read_text(proc_root / "meminfo")
    if raw is not None:
        mem = _parse_meminfo(raw)
        total = mem.get("MemTotal", 0)
        if total > 0:
            mem_total = total
            mem_available = mem.get("MemAvailable", mem.get("MemFree", 0))
            mem_percent = round((total - mem_available) / total * 100, 1)
    return SystemSummary(
        cpu_percent=cpu_percent_total(proc_root),
        load_1=load_1,
        load_5=load_5,
        load_15=load_15,
        cpu_count=os.cpu_count(),
        mem_total=mem_total,
        mem_available=mem_available,
        mem_percent=mem_percent,
    )


_prev_samples: dict[str, tuple[float, float]] = {}


def cpu_percent_delta(key: str, cpu_seconds: float, now: float | None = None) -> float | None:
    """Busy percent of a monotonically growing CPU-seconds counter.

    Feed the same ``key`` (e.g. one per runner) with a fresh counter reading
    on every tick; returns the busy % over the interval since the previous
    call, or None when there is no usable previous sample (first call,
    clock issue, or the counter went backwards because PIDs were recycled).
    """
    current_t = time.monotonic() if now is None else now
    previous = _prev_samples.get(key)
    _prev_samples[key] = (cpu_seconds, current_t)
    if len(_prev_samples) > 1024:
        _prev_samples.clear()
        _prev_samples[key] = (cpu_seconds, current_t)
    if previous is None:
        return None
    wall_dt = current_t - previous[1]
    cpu_dt = cpu_seconds - previous[0]
    if wall_dt <= 0 or cpu_dt < 0:
        return None
    return round(cpu_dt / wall_dt * 100, 1)


def _parse_stat_total(text: str) -> tuple[float, float] | None:
    """Split the aggregate ``cpu`` line into (busy_seconds, total_seconds)."""
    first = text.splitlines()[0] if text else ""
    parts = first.split()
    if len(parts) < 5 or parts[0] != "cpu":
        return None
    try:
        values = [float(part) / _CLK_TCK for part in parts[1:]]
    except ValueError:
        return None
    total = sum(values)
    idle = values[3] + (values[4] if len(values) > 4 else 0.0)
    return total - idle, total


def cpu_percent_total(proc_root: Path = _PROC_ROOT, now: float | None = None) -> float | None:
    """Total CPU busy % across all cores since the previous call.

    Normalized to 0-100% of overall capacity (all cores combined), matching
    ``psutil.cpu_percent()``. A multithreaded single tree (see
    ``tree_cpu_percent``) may still exceed 100%. None on the first call or
    when /proc/stat is unreadable.
    """
    raw = _read_text(proc_root / "stat")
    if raw is None:
        return None
    parsed = _parse_stat_total(raw)
    if parsed is None:
        return None
    busy, _ = parsed
    cores = os.cpu_count() or 1
    percent = cpu_percent_delta(f"sys:{proc_root}", busy, now)
    return round(percent / cores, 1) if percent is not None else None


def tree_cpu_percent(
    roots: list[int], proc_root: Path = _PROC_ROOT, now: float | None = None
) -> float | None:
    """CPU busy % of a PID tree since the previous call with the same roots.

    Not normalized: a multithreaded tree may exceed 100% (htop convention).
    """
    if not roots:
        return None
    tree = tree_stats(roots, proc_root)
    if tree.num_procs == 0:
        return None
    key = f"tree:{proc_root}:{','.join(str(pid) for pid in sorted(set(roots)))}"
    return cpu_percent_delta(key, tree.cpu_s_total, now)


def _parse_status(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def _kb_field(fields: dict[str, str], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    try:
        return int(value.split()[0]) * 1024
    except (ValueError, IndexError):
        return None


def _parse_stat_cpu(text: str) -> float | None:
    rparen = text.rfind(")")
    if rparen == -1:
        return None
    after = text[rparen + 2 :].split()
    if len(after) < 13:
        return None
    try:
        return (int(after[11]) + int(after[12])) / _CLK_TCK
    except (ValueError, IndexError):
        return None


def proc_stat(pid: int, proc_root: Path = _PROC_ROOT) -> ProcStat | None:
    """Snapshot one PID; None when the process is gone or hidden."""
    raw_status = _read_text(proc_root / str(pid) / "status")
    if raw_status is None:
        return None
    fields = _parse_status(raw_status)
    if not fields:
        return None
    threads_raw = fields.get("Threads")
    try:
        threads = int(threads_raw) if threads_raw is not None else None
    except ValueError:
        threads = None
    cpu_s: float | None = None
    raw_stat = _read_text(proc_root / str(pid) / "stat")
    if raw_stat is not None:
        cpu_s = _parse_stat_cpu(raw_stat)
    try:
        num_fds = sum(1 for _ in (proc_root / str(pid) / "fd").iterdir())
    except OSError:
        num_fds = None
    return ProcStat(
        pid=pid,
        name=fields.get("Name"),
        rss=_kb_field(fields, "VmRSS"),
        vms=_kb_field(fields, "VmSize"),
        threads=threads,
        cpu_s=cpu_s,
        num_fds=num_fds,
    )


def _ppid_map(proc_root: Path) -> dict[int, list[int]]:
    """Map parent PID to child PIDs via a single bounded /proc scan."""
    children: dict[int, list[int]] = {}
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return children
    for entry in entries:
        if not entry.name.isdigit():
            continue
        raw = _read_text(entry / "status")
        if raw is None:
            continue
        ppid: int | None = None
        for line in raw.splitlines():
            if line.startswith("PPid:"):
                try:
                    ppid = int(line.split()[1])
                except (ValueError, IndexError):
                    ppid = None
                break
        if ppid is None:
            continue
        children.setdefault(ppid, []).append(int(entry.name))
    return children


def tree_stats(roots: list[int], proc_root: Path = _PROC_ROOT) -> TreeStats:
    """Aggregate stats over root PIDs plus all recursive descendants."""
    if not roots:
        return TreeStats(pids=(), num_procs=0, rss_total=0, cpu_s_total=0.0, threads_total=0)
    children = _ppid_map(proc_root)
    visited: set[int] = set()
    stack = list(roots)
    found: list[int] = []
    rss_total = 0
    cpu_total = 0.0
    threads_total = 0
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stat = proc_stat(current, proc_root)
        if stat is None:
            continue
        found.append(current)
        rss_total += stat.rss or 0
        cpu_total += stat.cpu_s or 0.0
        threads_total += stat.threads or 0
        stack.extend(children.get(current, []))
    return TreeStats(
        pids=tuple(found),
        num_procs=len(found),
        rss_total=rss_total,
        cpu_s_total=round(cpu_total, 1),
        threads_total=threads_total,
    )


def format_bytes(num: int | None) -> str:
    """Format a byte count for a narrow screen; n/a when unknown."""
    if num is None:
        return "n/a"
    if num < 0:
        return "n/a"
    mib = num / (1024 * 1024)
    if mib >= 1024:
        return f"{mib / 1024:.1f} GiB"
    return f"{mib:.1f} MiB"


def format_cpu(seconds: float | None) -> str:
    """Format accumulated CPU seconds; n/a when unknown."""
    if seconds is None:
        return "n/a"
    return f"{seconds:.1f}s"
