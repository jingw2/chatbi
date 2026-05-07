from __future__ import annotations

import re

_MAX_CELL_LEN = 200
_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)",
    r"system\s*:",
    r"###\s*(system|user|assistant)",
    r"forget\s+(previous|all|instructions)",
]
_QTY_KEYWORDS = {"qty", "quantity", "count", "volume", "数量", "出库", "入库", "amount"}


def sanitize_for_llm(
    columns: list[str],
    rows: list[list],
    max_rows: int = 50,
) -> str:
    """Convert query results to a safe string for LLM insight generation.

    Truncates to max_rows, truncates long cell values, and filters strings
    that match known prompt-injection patterns.
    """
    header = " | ".join(str(c) for c in columns)
    lines = [header, "-" * max(len(header), 10)]

    for row in rows[:max_rows]:
        cells = []
        for val in row:
            s = str(val)
            if len(s) > _MAX_CELL_LEN:
                s = s[:_MAX_CELL_LEN] + "..."
            for pat in _INJECTION_PATTERNS:
                if re.search(pat, s, re.IGNORECASE):
                    s = "[filtered]"
                    break
            cells.append(s)
        lines.append(" | ".join(cells))

    if len(rows) > max_rows:
        lines.append(f"... ({len(rows) - max_rows} more rows)")

    return "\n".join(lines)


def check_result_anomalies(columns: list[str], rows: list[list]) -> list[str]:
    """Return warning strings for suspicious result patterns.

    Currently detects negative values in columns with quantity-related names.
    """
    warnings: list[str] = []
    for i, col in enumerate(columns):
        col_lower = col.lower()
        if any(kw in col_lower for kw in _QTY_KEYWORDS):
            try:
                negatives = [
                    row[i] for row in rows
                    if isinstance(row[i], (int, float)) and row[i] < 0
                ]
                if negatives:
                    warnings.append(
                        f"Column '{col}' contains {len(negatives)} negative value(s), "
                        "which may indicate data anomalies."
                    )
            except (IndexError, TypeError):
                pass
    return warnings
