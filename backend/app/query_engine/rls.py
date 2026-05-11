from __future__ import annotations

import re

# Roles that bypass RLS entirely (they have no user_data_scopes by design).
_RLS_EXEMPT_ROLES = {"superadmin"}
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def inject_rls(sql: str, scopes: dict[str, str], role: str) -> str:
    """Wrap SQL as a subquery and append WHERE filters from user data scopes.

    Bypassed when:
    - scopes is empty (user has no data scope restrictions)
    - role is superadmin

    WARNING: scope values are interpolated directly. This is safe only because
    scope values are admin-controlled DB data, never raw user input.
    """
    if not scopes or role in _RLS_EXEMPT_ROLES:
        return sql

    filters: list[str] = []
    for key, value in scopes.items():
        if not _IDENTIFIER_RE.fullmatch(key):
            raise ValueError(f"Invalid RLS scope key: {key}")
        filters.append(f"{key} = {_quote_literal(value)}")
    inner = sql.rstrip(";").rstrip()
    return f"SELECT * FROM ({inner}) AS _chatbi_rls WHERE {' AND '.join(filters)}"
