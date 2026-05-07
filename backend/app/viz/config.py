from __future__ import annotations

from app.viz.infer import _TIME_KEYWORDS


def build_chart_config(
    chart_type: str,
    columns: list[str],
    rows: list[list],
) -> dict | None:
    """Build an ECharts-compatible option dict for the given chart type.

    Returns None for chart_type="table", unknown types, or empty data.
    The returned dict is JSON-serializable and can be passed directly
    to echarts-for-react on the frontend.
    """
    if not columns or not rows:
        return None

    builder = _BUILDERS.get(chart_type)
    if builder is None:
        return None
    return builder(columns, rows)


def _build_line(columns: list[str], rows: list[list]) -> dict:
    if len(columns) == 2:
        return _build_line_simple(columns, rows)
    return _build_line_multi_series(columns, rows)


def _build_line_simple(columns: list[str], rows: list[list]) -> dict:
    x_data = [row[0] for row in rows]
    y_data = [row[1] for row in rows]
    return {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": {"type": "value"},
        "series": [{"name": columns[1], "type": "line", "data": y_data}],
    }


def _build_line_multi_series(columns: list[str], rows: list[list]) -> dict:
    """3-column line: dimension + time + metric. Group by dimension."""
    time_idx = _find_time_col_index(columns)
    dim_idx = 0 if time_idx != 0 else 1
    val_idx = next(i for i in range(3) if i != time_idx and i != dim_idx)

    x_values: list[str] = []
    seen_x: set[str] = set()
    for row in rows:
        x = str(row[time_idx])
        if x not in seen_x:
            x_values.append(x)
            seen_x.add(x)

    groups: dict[str, dict[str, object]] = {}
    for row in rows:
        dim = str(row[dim_idx])
        x = str(row[time_idx])
        if dim not in groups:
            groups[dim] = {}
        groups[dim][x] = row[val_idx]

    series_names = list(groups.keys())
    series = [
        {
            "name": name,
            "type": "line",
            "data": [groups[name].get(x, None) for x in x_values],
        }
        for name in series_names
    ]

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": series_names},
        "xAxis": {"type": "category", "data": x_values},
        "yAxis": {"type": "value"},
        "series": series,
    }


def _build_bar(columns: list[str], rows: list[list]) -> dict:
    x_data = [row[0] for row in rows]
    y_data = [row[1] for row in rows]
    return {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": {"type": "value"},
        "series": [{"name": columns[1], "type": "bar", "data": y_data}],
    }


def _build_bar_horizontal(columns: list[str], rows: list[list]) -> dict:
    y_data = [row[0] for row in rows]
    x_data = [row[1] for row in rows]
    return {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "value"},
        "yAxis": {"type": "category", "data": y_data},
        "series": [{"name": columns[1], "type": "bar", "data": x_data}],
    }


def _build_pie(columns: list[str], rows: list[list]) -> dict:
    data = [{"name": row[0], "value": row[1]} for row in rows]
    return {
        "tooltip": {"trigger": "item"},
        "legend": {"data": [row[0] for row in rows]},
        "series": [
            {
                "type": "pie",
                "radius": "60%",
                "data": data,
            }
        ],
    }


def _build_dual_axis(columns: list[str], rows: list[list]) -> dict:
    x_data = [row[0] for row in rows]
    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": [columns[1], columns[2]]},
        "xAxis": {"type": "category", "data": x_data},
        "yAxis": [
            {"type": "value", "name": columns[1]},
            {"type": "value", "name": columns[2]},
        ],
        "series": [
            {"name": columns[1], "type": "bar", "data": [row[1] for row in rows]},
            {
                "name": columns[2],
                "type": "line",
                "yAxisIndex": 1,
                "data": [row[2] for row in rows],
            },
        ],
    }


def _build_big_number(columns: list[str], rows: list[list]) -> dict:
    return {
        "type": "big_number",
        "label": columns[0],
        "value": rows[0][0],
    }


def _find_time_col_index(columns: list[str]) -> int:
    """Return the index of the first time-related column, or 1 as fallback."""
    for i, col in enumerate(columns):
        col_lower = col.lower()
        if any(kw in col_lower for kw in _TIME_KEYWORDS):
            return i
    return 1


_BUILDERS: dict[str, callable] = {
    "line": _build_line,
    "bar": _build_bar,
    "bar_horizontal": _build_bar_horizontal,
    "pie": _build_pie,
    "dual_axis": _build_dual_axis,
    "big_number": _build_big_number,
}
