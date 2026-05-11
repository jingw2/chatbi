import pytest
from app.viz.config import build_chart_config


class TestBuildChartConfigLine:
    def test_line_has_xaxis_and_series(self):
        cfg = build_chart_config(
            "line",
            ["month", "revenue"],
            [["2024-01", 100], ["2024-02", 120], ["2024-03", 150]],
        )
        assert cfg["xAxis"]["data"] == ["2024-01", "2024-02", "2024-03"]
        assert len(cfg["series"]) == 1
        assert cfg["series"][0]["type"] == "line"
        assert cfg["series"][0]["data"] == [100, 120, 150]
        assert cfg["series"][0]["name"] == "revenue"

    def test_line_three_cols_multi_series(self):
        cfg = build_chart_config(
            "line",
            ["region", "month", "sales"],
            [
                ["华东", "2024-01", 100],
                ["华东", "2024-02", 120],
                ["华南", "2024-01", 80],
                ["华南", "2024-02", 90],
            ],
        )
        assert "2024-01" in cfg["xAxis"]["data"]
        assert "2024-02" in cfg["xAxis"]["data"]
        assert len(cfg["series"]) == 2
        series_names = {s["name"] for s in cfg["series"]}
        assert series_names == {"华东", "华南"}
        assert set(cfg["legend"]["data"]) == series_names

    def test_line_has_tooltip(self):
        cfg = build_chart_config("line", ["month", "val"], [["Jan", 1]])
        assert cfg["tooltip"]["trigger"] == "axis"


class TestBuildChartConfigBar:
    def test_bar_has_xaxis_and_series(self):
        cfg = build_chart_config(
            "bar",
            ["region", "sales"],
            [["华东", 1000], ["华南", 800], ["华北", 600]],
        )
        assert cfg["xAxis"]["data"] == ["华东", "华南", "华北"]
        assert len(cfg["series"]) == 1
        assert cfg["series"][0]["type"] == "bar"
        assert cfg["series"][0]["data"] == [1000, 800, 600]

    def test_bar_has_tooltip(self):
        cfg = build_chart_config("bar", ["a", "b"], [["x", 1]])
        assert "tooltip" in cfg


class TestBuildChartConfigBarHorizontal:
    def test_horizontal_swaps_axes(self):
        cfg = build_chart_config(
            "bar_horizontal",
            ["category", "count"],
            [["A", 10], ["B", 20]],
        )
        assert cfg["yAxis"]["data"] == ["A", "B"]
        assert cfg["xAxis"]["type"] == "value"
        assert cfg["series"][0]["type"] == "bar"
        assert cfg["series"][0]["data"] == [10, 20]


class TestBuildChartConfigPie:
    def test_pie_has_series_data(self):
        cfg = build_chart_config(
            "pie",
            ["region", "share"],
            [["华东", 0.4], ["华南", 0.35], ["华北", 0.25]],
        )
        assert cfg["series"][0]["type"] == "pie"
        data = cfg["series"][0]["data"]
        assert len(data) == 3
        assert data[0] == {"name": "华东", "value": 0.4}
        assert data[1] == {"name": "华南", "value": 0.35}

    def test_pie_has_tooltip_and_legend(self):
        cfg = build_chart_config("pie", ["a", "b"], [["x", 1]])
        assert "tooltip" in cfg
        assert "legend" in cfg


class TestBuildChartConfigDualAxis:
    def test_dual_axis_has_two_yaxes_and_two_series(self):
        cfg = build_chart_config(
            "dual_axis",
            ["region", "sales", "profit"],
            [["华东", 1000, 200], ["华南", 800, 150]],
        )
        assert cfg["xAxis"]["data"] == ["华东", "华南"]
        assert len(cfg["yAxis"]) == 2
        assert len(cfg["series"]) == 2
        assert cfg["series"][0]["name"] == "sales"
        assert cfg["series"][0]["type"] == "bar"
        assert cfg["series"][1]["name"] == "profit"
        assert cfg["series"][1]["type"] == "line"
        assert cfg["series"][1]["yAxisIndex"] == 1


class TestBuildChartConfigBigNumber:
    def test_big_number_returns_value_and_label(self):
        cfg = build_chart_config("big_number", ["total_sales"], [[100000]])
        assert cfg["value"] == 100000
        assert cfg["label"] == "total_sales"
        assert cfg["type"] == "big_number"


class TestBuildChartConfigTable:
    def test_table_returns_none(self):
        cfg = build_chart_config("table", ["a", "b", "c", "d"], [["x", 1, 2, 3]])
        assert cfg is None

    def test_unknown_type_returns_none(self):
        cfg = build_chart_config("unknown", ["a"], [[1]])
        assert cfg is None


class TestBuildChartConfigEmpty:
    def test_empty_rows_returns_none(self):
        cfg = build_chart_config("bar", ["a", "b"], [])
        assert cfg is None

    def test_empty_columns_returns_none(self):
        cfg = build_chart_config("bar", [], [])
        assert cfg is None


class TestBuildChartConfigIntegration:
    """Test that build_chart_config + infer_chart_type work together."""

    def test_infer_then_build_bar(self):
        from app.viz.infer import infer_chart_type

        columns = ["region", "sales"]
        rows = [["华东", 1000], ["华南", 800]]
        chart_type = infer_chart_type(columns, rows)
        cfg = build_chart_config(chart_type, columns, rows)

        assert chart_type == "bar"
        assert cfg is not None
        assert cfg["series"][0]["type"] == "bar"

    def test_infer_then_build_table_returns_none(self):
        from app.viz.infer import infer_chart_type

        columns = ["a", "b", "c", "d"]
        rows = [["x", 1, 2, 3]]
        chart_type = infer_chart_type(columns, rows)
        cfg = build_chart_config(chart_type, columns, rows)

        assert chart_type == "table"
        assert cfg is None
