import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw, ChevronDown, ChevronRight } from "lucide-react";

interface SchemaTable {
  id: number;
  datasource_id: number;
  table_name: string;
  description: string | null;
  is_active: boolean;
}

interface SchemaColumn {
  id: number;
  table_id: number;
  column_name: string;
  data_type: string;
  description: string | null;
  example_values: string | null;
  notes: string | null;
}

interface Datasource {
  id: number;
  name: string;
  db_type: string;
}

export default function SchemaPage() {
  const qc = useQueryClient();
  const [dsId, setDsId] = useState<string>("");
  const [expandedTable, setExpandedTable] = useState<number | null>(null);

  const { data: datasources } = useQuery<Datasource[]>({
    queryKey: ["datasources"],
    queryFn: async () => (await api.get("/api/v1/datasources")).data,
  });

  const { data: tables, isLoading: tablesLoading } = useQuery<SchemaTable[]>({
    queryKey: ["schema-tables", dsId],
    queryFn: async () => (await api.get(`/api/v1/schema/${dsId}/tables`)).data,
    enabled: !!dsId,
  });

  const { data: columns } = useQuery<SchemaColumn[]>({
    queryKey: ["schema-columns", expandedTable],
    queryFn: async () =>
      (await api.get(`/api/v1/schema/tables/${expandedTable}/columns`)).data,
    enabled: expandedTable !== null,
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/schema/${dsId}/sync`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schema-tables", dsId] }),
  });

  const updateTableMutation = useMutation({
    mutationFn: ({ id, ...body }: { id: number; description?: string; is_active?: boolean }) =>
      api.patch(`/api/v1/schema/tables/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schema-tables", dsId] }),
  });

  const updateColumnMutation = useMutation({
    mutationFn: ({ id, ...body }: { id: number; description?: string; example_values?: string; notes?: string }) =>
      api.patch(`/api/v1/schema/columns/${id}`, body),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["schema-columns", expandedTable] }),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Schema Manager</h1>
        <div className="flex items-center gap-2">
          <Select value={dsId} onValueChange={setDsId}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select datasource" />
            </SelectTrigger>
            <SelectContent>
              {datasources?.map((ds) => (
                <SelectItem key={ds.id} value={ds.id.toString()}>
                  {ds.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {dsId && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
            >
              <RefreshCw size={14} className={syncMutation.isPending ? "animate-spin mr-1" : "mr-1"} />
              Sync
            </Button>
          )}
        </div>
      </div>

      {!dsId && (
        <p className="text-sm text-gray-400 py-8 text-center">
          Select a datasource to manage its schema
        </p>
      )}

      {dsId && tablesLoading && (
        <p className="text-sm text-gray-400">Loading tables...</p>
      )}

      {dsId && tables && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Table</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="w-24">Active</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tables.map((tbl) => (
              <>
                <TableRow key={tbl.id}>
                  <TableCell>
                    <button
                      onClick={() =>
                        setExpandedTable(expandedTable === tbl.id ? null : tbl.id)
                      }
                    >
                      {expandedTable === tbl.id ? (
                        <ChevronDown size={14} />
                      ) : (
                        <ChevronRight size={14} />
                      )}
                    </button>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{tbl.table_name}</TableCell>
                  <TableCell>
                    <Input
                      className="h-8 text-xs"
                      defaultValue={tbl.description ?? ""}
                      placeholder="Add description..."
                      onBlur={(e) => {
                        if (e.target.value !== (tbl.description ?? "")) {
                          updateTableMutation.mutate({
                            id: tbl.id,
                            description: e.target.value,
                          });
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        updateTableMutation.mutate({
                          id: tbl.id,
                          is_active: !tbl.is_active,
                        })
                      }
                    >
                      <Badge variant={tbl.is_active ? "secondary" : "destructive"}>
                        {tbl.is_active ? "Yes" : "No"}
                      </Badge>
                    </Button>
                  </TableCell>
                </TableRow>
                {expandedTable === tbl.id && columns && (
                  <TableRow key={`cols-${tbl.id}`}>
                    <TableCell colSpan={4} className="bg-gray-50 p-4">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b text-gray-500">
                            <th className="py-1 text-left font-medium">Column</th>
                            <th className="py-1 text-left font-medium">Type</th>
                            <th className="py-1 text-left font-medium">Description</th>
                            <th className="py-1 text-left font-medium">Examples</th>
                            <th className="py-1 text-left font-medium">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {columns.map((col) => (
                            <tr key={col.id} className="border-b last:border-0">
                              <td className="py-1.5 font-mono">{col.column_name}</td>
                              <td className="py-1.5 text-gray-500">{col.data_type}</td>
                              <td className="py-1.5">
                                <Input
                                  className="h-6 text-xs"
                                  defaultValue={col.description ?? ""}
                                  placeholder="—"
                                  onBlur={(e) => {
                                    if (e.target.value !== (col.description ?? "")) {
                                      updateColumnMutation.mutate({
                                        id: col.id,
                                        description: e.target.value,
                                      });
                                    }
                                  }}
                                />
                              </td>
                              <td className="py-1.5">
                                <Input
                                  className="h-6 text-xs"
                                  defaultValue={col.example_values ?? ""}
                                  placeholder="—"
                                  onBlur={(e) => {
                                    if (e.target.value !== (col.example_values ?? "")) {
                                      updateColumnMutation.mutate({
                                        id: col.id,
                                        example_values: e.target.value,
                                      });
                                    }
                                  }}
                                />
                              </td>
                              <td className="py-1.5">
                                <Input
                                  className="h-6 text-xs"
                                  defaultValue={col.notes ?? ""}
                                  placeholder="—"
                                  onBlur={(e) => {
                                    if (e.target.value !== (col.notes ?? "")) {
                                      updateColumnMutation.mutate({
                                        id: col.id,
                                        notes: e.target.value,
                                      });
                                    }
                                  }}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </TableCell>
                  </TableRow>
                )}
              </>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
