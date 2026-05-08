import { ScrollText } from "lucide-react";

export default function AuditPage() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-4">Audit Log</h1>
      <div className="flex flex-col items-center gap-2 py-20 text-gray-400">
        <ScrollText size={32} />
        <p className="text-sm">Query audit logs</p>
        <p className="text-xs">
          Audit log viewing requires the query_logs list endpoint (planned for a future release)
        </p>
      </div>
    </div>
  );
}
