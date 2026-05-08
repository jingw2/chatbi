import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Database } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

interface Datasource {
  id: number;
  name: string;
  db_type: string;
}

interface DatasourceSelectorProps {
  value: number | null;
  onChange: (id: number) => void;
}

export default function DatasourceSelector({
  value,
  onChange,
}: DatasourceSelectorProps) {
  const { data: datasources, isLoading } = useQuery<Datasource[]>({
    queryKey: ["datasources"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/datasources");
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20">
        <Skeleton className="h-10 w-64" />
      </div>
    );
  }

  if (!datasources?.length) {
    return (
      <div className="flex flex-col items-center gap-2 py-20 text-gray-400">
        <Database size={32} />
        <p className="text-sm">No datasources available</p>
        <p className="text-xs">Ask an admin to add a datasource</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 py-20">
      <Database size={32} className="text-gray-400" />
      <p className="text-sm text-gray-600">Select a datasource to start</p>
      <Select
        value={value?.toString() ?? ""}
        onValueChange={(v) => onChange(Number(v))}
      >
        <SelectTrigger className="w-64">
          <SelectValue placeholder="Choose datasource..." />
        </SelectTrigger>
        <SelectContent>
          {datasources.map((ds) => (
            <SelectItem key={ds.id} value={ds.id.toString()}>
              {ds.name} ({ds.db_type})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
