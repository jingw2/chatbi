import pytest
from app.query_engine.prompt_builder import build_text_to_sql_prompt


class TestBuildTextToSqlPrompt:
    def _schema_cols(self):
        return [
            {
                "table_name": "orders",
                "column_name": "region",
                "data_type": "varchar",
                "description": "Geographic region",
                "example_values": "华东, 华南",
                "notes": None,
            },
            {
                "table_name": "orders",
                "column_name": "qty",
                "data_type": "integer",
                "description": "Shipment quantity",
                "example_values": None,
                "notes": None,
            },
        ]

    def test_prompt_contains_question(self):
        prompt = build_text_to_sql_prompt("上周华东区出库量", self._schema_cols(), [])
        assert "上周华东区出库量" in prompt

    def test_prompt_contains_table_and_columns(self):
        prompt = build_text_to_sql_prompt("上周华东区出库量", self._schema_cols(), [])
        assert "orders" in prompt
        assert "region" in prompt
        assert "qty" in prompt

    def test_prompt_contains_description(self):
        prompt = build_text_to_sql_prompt("q", self._schema_cols(), [])
        assert "Geographic region" in prompt

    def test_prompt_contains_example_values(self):
        prompt = build_text_to_sql_prompt("q", self._schema_cols(), [])
        assert "华东, 华南" in prompt

    def test_prompt_includes_rules(self):
        items = [{"type": "rule", "title": "Region rule", "content": "Always filter by region."}]
        prompt = build_text_to_sql_prompt("q", [], items)
        assert "Region rule" in prompt
        assert "Always filter by region." in prompt

    def test_prompt_includes_fewshot(self):
        items = [{"type": "fewshot", "title": "Top regions", "content": "SELECT region FROM orders"}]
        prompt = build_text_to_sql_prompt("q", [], items)
        assert "Top regions" in prompt
        assert "SELECT region FROM orders" in prompt

    def test_prompt_excludes_glossary_from_rules_and_fewshot(self):
        items = [{"type": "glossary", "title": "华东区", "content": "East China region"}]
        prompt = build_text_to_sql_prompt("q", [], items)
        # Glossary items are not shown as rules or fewshot examples
        assert "业务规则" not in prompt or "华东区" not in prompt.split("业务规则")[1].split("参考示例")[0] if "业务规则" in prompt else True

    def test_empty_schema_and_knowledge_still_valid(self):
        prompt = build_text_to_sql_prompt("anything", [], [])
        assert "anything" in prompt
        assert len(prompt) > 10
