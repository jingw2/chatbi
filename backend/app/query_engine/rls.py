from __future__ import annotations

# Roles that bypass RLS entirely (they have no user_data_scopes by design).
_RLS_EXEMPT_ROLES = {"superadmin"}


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

    filters = [f"{key} = '{value}'" for key, value in scopes.items()]
    inner = sql.rstrip(";").rstrip()
    return f"SELECT * FROM ({inner}) AS _chatbi_rls WHERE {' AND '.join(filters)}"
