"""Deterministic, offline launch-day Twitch quantiles from comparable curves."""

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path


LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]


def round2(x):
    """Round half up to two decimals, emitting whole values as integers."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def parse_ts(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def comparable_day(comparable):
    """Return hours 1..24, log-interpolating gaps, or None if insufficient."""
    start = parse_ts(comparable["day_start"])
    points = {}
    for point in comparable["hourly"]:
        delta = (parse_ts(point["from"]) - start).total_seconds()
        if 0 <= delta < 24 * 3600 and point["viewers"] > 0:
            points[int(delta // 3600) + 1] = float(point["viewers"])
    if 1 not in points or len(points) < 20:
        return None

    day = []
    for hour in range(1, 25):
        if hour in points:
            day.append(points[hour])
            continue
        lo = max((h for h in points if h < hour), default=None)
        hi = min((h for h in points if h > hour), default=None)
        if lo is None:
            day.append(points[hi])
        elif hi is None:
            day.append(points[lo])
        else:
            fraction = (hour - lo) / (hi - lo)
            day.append(math.exp(
                math.log(points[lo])
                + fraction * (math.log(points[hi]) - math.log(points[lo]))
            ))
    return day


def build_pool(case, p1):
    pool = []
    for comparable in case["comparables"]:
        if "before release" in comparable["name"].lower():
            continue
        day = comparable_day(comparable)
        if day is None:
            continue
        share = day[0] / max(day)
        platforms = comparable["platforms"]
        console_only = not re.search(r"\bPC\b", platforms) and "Stadia" not in platforms
        weight = math.exp(-((math.log(p1) - math.log(day[0])) ** 2) / (2 * 1.0 ** 2))
        if console_only:
            weight *= 2.0
        if share < 0.15:
            weight *= 0.15
        pool.append((day, weight))
    return pool


def weighted_quantile(values, tau):
    """First sorted value whose cumulative weight reaches tau of total."""
    target = tau * sum(weight for _, weight in values)
    cumulative = 0.0
    for value, weight in values:
        cumulative += weight
        if cumulative >= target:
            return value
    return values[-1][0]


def forecast_case(case):
    if case["levels"] != LEVELS:
        raise ValueError("expected levels [0.05, 0.25, 0.5, 0.75, 0.95]")
    first = next(row for row in case["known"] if row["hour"] == 1)
    p1 = max(1, first["viewers"])
    pool = build_pool(case, p1)
    hours = []
    for row in case["forecast"]:
        hour = row["hour"]
        if not pool:
            quantiles = [
                round2(p1 * math.exp(z * 0.15 * math.sqrt(hour - 1)))
                for z in Z
            ]
        else:
            values = []
            for day, weight in pool:
                for hh in (hour - 1, hour, hour + 1):
                    if 2 <= hh <= 24:
                        values.append((
                            math.log(day[hh - 1] / day[0]),
                            weight * (0.5 if hh != hour else 1.0),
                        ))
            values.sort(key=lambda item: item[0])
            qs = [weighted_quantile(values, tau) for tau in LEVELS]
            median = qs[2]
            adjusted = [median + (q - median) * 0.85 for q in qs]
            quantiles = sorted(round2(p1 * math.exp(q)) for q in adjusted)
        hours.append({"hour": hour, "q": quantiles})
    return {"hours": hours}


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_dir.glob("*.in"), key=lambda item: item.name):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast_case(case)
        (output_dir / f"{case['id']}.out").write_text(
            json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
