from __future__ import annotations


def build_text_to_sql_prompt(
    question: str,
    schema_cols: list[dict],
    knowledge_items: list[dict],
) -> str:
    """Assemble the text-to-SQL prompt from schema columns and knowledge items.

    schema_cols: list of dicts with keys table_name, column_name, data_type,
                 description, example_values, notes  (from retrieve_schema)
    knowledge_items: list of dicts with keys type, title, content
                     (from retrieve_knowledge; only type=rule and type=fewshot are used)
    """
    lines: list[str] = [
        "你是一名专业的数据分析师，请根据以下数据库结构信息将用户问题转换为SQL查询。",
        "",
    ]

    # Schema section
    if schema_cols:
        lines.append("## 数据库表结构")
        lines.append("")
        tables: dict[str, list[dict]] = {}
        for col in schema_cols:
            tables.setdefault(col["table_name"], []).append(col)

        for table_name, cols in tables.items():
            lines.append(f"表: {table_name}")
            for col in cols:
                entry = f"  - {col['column_name']} ({col['data_type']})"
                if col.get("description"):
                    entry += f": {col['description']}"
                if col.get("example_values"):
                    entry += f" [示例: {col['example_values']}]"
                if col.get("notes"):
                    entry += f" [备注: {col['notes']}]"
                lines.append(entry)
            lines.append("")

    # Business rules
    rules = [k for k in knowledge_items if k["type"] == "rule"]
    if rules:
        lines.append("## 业务规则")
        lines.append("")
        for r in rules:
            lines.append(f"- {r['title']}: {r['content']}")
        lines.append("")

    # Few-shot examples
    fewshots = [k for k in knowledge_items if k["type"] == "fewshot"]
    if fewshots:
        lines.append("## 参考示例")
        lines.append("")
        for f in fewshots:
            lines.append(f"问题: {f['title']}")
            lines.append(f"SQL: {f['content']}")
            lines.append("")

    # User question
    lines.extend([
        "## 用户问题",
        "",
        question,
        "",
        "请输出SQL查询语句，只输出SQL，不要有其他解释。",
    ])

    return "\n".join(lines)
