import ReactECharts from "echarts-for-react";

interface ChartPanelProps {
  config: Record<string, unknown>;
}

export default function ChartPanel({ config }: ChartPanelProps) {
  // big_number is a custom type — render as a centered value card
  if (config.type === "big_number") {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border bg-white p-8">
        <span className="text-4xl font-bold text-gray-900">
          {String(config.value ?? "—")}
        </span>
        {config.label && (
          <span className="mt-1 text-sm text-gray-500">
            {String(config.label)}
          </span>
        )}
      </div>
    );
  }

  // Standard ECharts option
  return (
    <div className="rounded-lg border bg-white p-4">
      <ReactECharts
        option={config}
        style={{ height: 320, width: "100%" }}
        notMerge
        lazyUpdate
      />
    </div>
  );
}
