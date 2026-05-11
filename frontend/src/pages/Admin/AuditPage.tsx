import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface QueryLog {
  id: number;
  user_id: number;
  datasource_id: number | null;
  user_question: string;
  intent: string | null;
  execution_ms: number | null;
  row_count: number | null;
  error_msg: string | null;
  created_at: string;
}

export default function AuditPage() {
  const { data: logs, isLoading } = useQuery<QueryLog[]>({
    queryKey: ["audit-query-logs"],
    queryFn: async () => (await api.get("/api/v1/audit/query-logs")).data,
  });

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold mb-4">Audit Log</h1>
      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : !logs?.length ? (
        <p className="text-sm text-gray-400">No query logs yet</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Datasource</TableHead>
              <TableHead>Question</TableHead>
              <TableHead>Intent</TableHead>
              <TableHead>Rows</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="whitespace-nowrap text-xs text-gray-500">
                  {new Date(log.created_at).toLocaleString()}
                </TableCell>
                <TableCell>{log.user_id}</TableCell>
                <TableCell>{log.datasource_id ?? "-"}</TableCell>
                <TableCell className="max-w-md truncate">
                  {log.user_question}
                </TableCell>
                <TableCell>{log.intent ?? "-"}</TableCell>
                <TableCell>{log.row_count ?? "-"}</TableCell>
                <TableCell>
                  <Badge variant={log.error_msg ? "destructive" : "secondary"}>
                    {log.error_msg ? "Error" : `${log.execution_ms ?? 0}ms`}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
