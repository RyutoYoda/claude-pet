from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

INPUT_PRICE = 3.0 / 1_000_000
OUTPUT_PRICE = 15.0 / 1_000_000
CACHE_WRITE_PRICE = 3.75 / 1_000_000
CACHE_READ_PRICE = 0.30 / 1_000_000

_DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _calc_cost(input_t: int, output_t: int, cache_w: int, cache_r: int) -> float:
    return (
        input_t * INPUT_PRICE
        + output_t * OUTPUT_PRICE
        + cache_w * CACHE_WRITE_PRICE
        + cache_r * CACHE_READ_PRICE
    )


def _fmt_tokens(t: int) -> str:
    if t >= 1_000_000:
        return f"{t / 1_000_000:.1f}M"
    if t >= 1_000:
        return f"{t / 1_000:.0f}K"
    return str(t)


@dataclass
class DailyStat:
    label: str
    date_str: str  # "7/28"
    tokens: int
    cost: float
    is_today: bool


@dataclass
class UsageStats:
    today_tokens: int
    today_cost: float
    week_tokens: int
    week_cost: float
    month_tokens: int
    month_cost: float
    daily_stats: list[DailyStat] = field(default_factory=list)


def load_usage_stats() -> UsageStats:
    projects_dir = Path.home() / ".claude" / "projects"
    jsonl_files = glob.glob(str(projects_dir / "**" / "*.jsonl"), recursive=True)

    now = datetime.now(tz=UTC)
    today: date = now.date()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    day_tokens: dict[date, float] = {d: 0.0 for d in days}
    day_cost: dict[date, float] = {d: 0.0 for d in days}

    seen: set[str] = set()
    today_t = today_c = 0.0
    week_t = week_c = 0.0
    month_t = month_c = 0.0

    for fpath in jsonl_files:
        try:
            with open(fpath, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if entry.get("type") != "assistant":
                        continue

                    request_id = entry.get("requestId") or entry.get("uuid", "")
                    if not request_id or request_id in seen:
                        continue
                    seen.add(request_id)

                    ts_str = entry.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except (ValueError, AttributeError):
                        continue

                    msg = entry.get("message") or {}
                    usage = msg.get("usage") or {}
                    input_t = int(usage.get("input_tokens") or 0)
                    output_t = int(usage.get("output_tokens") or 0)
                    cache_w = int(usage.get("cache_creation_input_tokens") or 0)
                    cache_r = int(usage.get("cache_read_input_tokens") or 0)
                    tokens = input_t + output_t + cache_w + cache_r
                    cost = _calc_cost(input_t, output_t, cache_w, cache_r)

                    if ts >= month_start:
                        month_t += tokens
                        month_c += cost
                        if ts >= week_start:
                            week_t += tokens
                            week_c += cost
                            if ts >= today_start:
                                today_t += tokens
                                today_c += cost

                    entry_date = ts.date()
                    if entry_date in day_tokens:
                        day_tokens[entry_date] += tokens
                        day_cost[entry_date] += cost
        except OSError:
            continue

    daily_stats = [
        DailyStat(
            label=_DOW_JA[d.weekday()],
            date_str=f"{d.month}/{d.day}",
            tokens=int(day_tokens[d]),
            cost=day_cost[d],
            is_today=(d == today),
        )
        for d in days
    ]

    return UsageStats(
        today_tokens=int(today_t),
        today_cost=today_c,
        week_tokens=int(week_t),
        week_cost=week_c,
        month_tokens=int(month_t),
        month_cost=month_c,
        daily_stats=daily_stats,
    )
