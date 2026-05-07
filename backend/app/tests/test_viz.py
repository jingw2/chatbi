import pytest
from app.viz.infer import infer_chart_type


class TestInferChartType:
    def test_empty_returns_table(self):
        assert infer_chart_type([], []) == "table"

    def test_single_value_returns_big_number(self):
        assert infer_chart_type(["total_sales"], [[100000]]) == "big_number"

    def test_two_cols_few_rows_returns_bar(self):
        rows = [["华东", 1000], ["华南", 800], ["华北", 600]]
        assert infer_chart_type(["region", "sales"], rows) == "bar"

    def test_two_cols_many_rows_returns_bar_horizontal(self):
        rows = [[str(i), i * 100] for i in range(15)]
        assert infer_chart_type(["category", "count"], rows) == "bar_horizontal"

    def test_time_col_returns_line(self):
        rows = [["2024-01", 100], ["2024-02", 120]]
        assert infer_chart_type(["month", "revenue"], rows) == "line"

    def test_date_col_returns_line(self):
        rows = [["2024-01-01", 50]]
        assert infer_chart_type(["order_date", "qty"], rows) == "line"

    def test_proportion_col_returns_pie(self):
        rows = [["华东", 0.4], ["华南", 0.35], ["华北", 0.25]]
        assert infer_chart_type(["region", "share"], rows) == "pie"

    def test_pct_col_returns_pie(self):
        rows = [["A", 60], ["B", 40]]
        assert infer_chart_type(["product", "pct"], rows) == "pie"

    def test_three_cols_with_time_returns_line(self):
        rows = [["华东", "2024-01", 100]]
        assert infer_chart_type(["region", "month", "sales"], rows) == "line"

    def test_three_cols_no_time_returns_dual_axis(self):
        rows = [["华东", 1000, 200]]
        assert infer_chart_type(["region", "sales", "profit"], rows) == "dual_axis"

    def test_four_cols_returns_table(self):
        rows = [["华东", 1, 2, 3]]
        assert infer_chart_type(["a", "b", "c", "d"], rows) == "table"
