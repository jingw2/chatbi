from __future__ import annotations

_TIME_KEYWORDS = {"date", "time", "year", "month", "day", "week", "quarter", "period", "dt", "ts"}
_PROP_KEYWORDS = {"share", "proportion", "ratio", "pct", "percent", "rate", "占比", "比例"}


def infer_chart_type(columns: list[str], rows: list[list]) -> str:
    """Infer ECharts chart type from query result shape.

    Rules (in priority order):
    - 0 cols or 0 rows → table
    - 1 col, 1 row    → big_number
    - 2 cols, proportion keyword in any col → pie
    - 2 cols, time keyword in any col → line
    - 2 cols, ≤10 rows → bar
    - 2 cols, >10 rows → bar_horizontal
    - 3 cols, time keyword → line
    - 3 cols, no time  → dual_axis
    - 4+ cols          → table
    """
    n_cols = len(columns)
    n_rows = len(rows)

    if n_cols == 0 or n_rows == 0:
        return "table"

    if n_cols == 1 and n_rows == 1:
        return "big_number"

    col_lower = [c.lower() for c in columns]
    has_time = any(kw in name for name in col_lower for kw in _TIME_KEYWORDS)
    has_prop = any(kw in name for name in col_lower for kw in _PROP_KEYWORDS)

    if n_cols == 2:
        if has_prop:
            return "pie"
        if has_time:
            return "line"
        return "bar" if n_rows <= 10 else "bar_horizontal"

    if n_cols == 3:
        return "line" if has_time else "dual_axis"

    return "table"
