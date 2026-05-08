import type { QueryResponseData } from "@/stores/chat";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface WorkflowResultPanelProps {
  queryResponse: QueryResponseData;
}

interface StepResult {
  name: string;
  columns: string[];
  rows: unknown[][];
  execution_ms: number;
  error: string | null;
}

export default function WorkflowResultPanel({
  queryResponse,
}: WorkflowResultPanelProps) {
  // workflow_result is embedded in the response but not in the typed schema yet
  // We access it via the raw response object
  const raw = queryResponse as unknown as Record<string, unknown>;
  const workflowResult = raw.workflow_result as {
    workflow_name: string;
    step_results: StepResult[];
    total_execution_ms: number;
  } | undefined;

  if (!workflowResult) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-700">
          Workflow: {workflowResult.workflow_name}
        </span>
        <Badge variant="secondary" className="text-[10px]">
          {workflowResult.total_execution_ms}ms
        </Badge>
      </div>

      {workflowResult.step_results.map((step, i) => (
        <Card key={i} className={step.error ? "border-red-200" : ""}>
          <CardHeader className="p-3 pb-0">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              {step.name}
              {step.error && (
                <Badge variant="destructive" className="text-[10px]">
                  Error
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-2">
            {step.error ? (
              <p className="text-xs text-red-600">{step.error}</p>
            ) : step.rows.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b">
                      {step.columns.map((col) => (
                        <th
                          key={col}
                          className="px-2 py-1 text-left font-medium text-gray-500"
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {step.rows.slice(0, 20).map((row, ri) => (
                      <tr key={ri} className="border-b last:border-0">
                        {(row as unknown[]).map((cell, ci) => (
                          <td key={ci} className="px-2 py-1 text-gray-700">
                            {String(cell ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {step.rows.length > 20 && (
                  <p className="mt-1 text-[10px] text-gray-400">
                    Showing 20 of {step.rows.length} rows
                  </p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400">No rows returned</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
