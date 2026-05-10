import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2 } from "lucide-react";

interface Datasource {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  created_by: number;
}

export default function DatasourcesPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    db_type: "postgres",
    host: "",
    port: "5432",
    database: "",
    username: "",
    password: "",
    readonly_user: "",
    readonly_password: "",
  });

  const { data: datasources, isLoading } = useQuery<Datasource[]>({
    queryKey: ["datasources"],
    queryFn: async () => (await api.get("/api/v1/datasources")).data,
  });

  const createMutation = useMutation({
    mutationFn: (body: typeof form) =>
      api.post("/api/v1/datasources", { ...body, port: Number(body.port) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasources"] });
      setOpen(false);
      setForm({
        name: "", db_type: "postgres", host: "", port: "5432",
        database: "", username: "", password: "",
        readonly_user: "", readonly_password: "",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/datasources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasources"] }),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(form);
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Datasources</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus size={16} className="mr-1" /> Add Datasource
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Datasource</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="space-y-1">
                <Label>Name</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="space-y-1">
                <Label>DB Type</Label>
                <Select value={form.db_type} onValueChange={(v) => setForm({ ...form, db_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="postgres">PostgreSQL</SelectItem>
                    <SelectItem value="mysql">MySQL</SelectItem>
                    <SelectItem value="clickhouse">ClickHouse</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2 space-y-1">
                  <Label>Host</Label>
                  <Input value={form.host} onChange={(e) => setForm({ ...form, host: e.target.value })} required />
                </div>
                <div className="space-y-1">
                  <Label>Port</Label>
                  <Input type="number" value={form.port} onChange={(e) => setForm({ ...form, port: e.target.value })} required />
                </div>
              </div>
              <div className="space-y-1">
                <Label>Database</Label>
                <Input value={form.database} onChange={(e) => setForm({ ...form, database: e.target.value })} required />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label>Username</Label>
                  <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
                </div>
                <div className="space-y-1">
                  <Label>Password</Label>
                  <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label>Read-only User</Label>
                  <Input value={form.readonly_user} onChange={(e) => setForm({ ...form, readonly_user: e.target.value })} required />
                </div>
                <div className="space-y-1">
                  <Label>Read-only Password</Label>
                  <Input type="password" value={form.readonly_password} onChange={(e) => setForm({ ...form, readonly_password: e.target.value })} required />
                </div>
              </div>
              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Host</TableHead>
              <TableHead>Database</TableHead>
              <TableHead className="w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {datasources?.map((ds) => (
              <TableRow key={ds.id}>
                <TableCell className="font-medium">{ds.name}</TableCell>
                <TableCell>{ds.db_type}</TableCell>
                <TableCell>{ds.host}:{ds.port}</TableCell>
                <TableCell>{ds.database}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      if (window.confirm(`Delete datasource "${ds.name}"? This cannot be undone.`)) {
                        deleteMutation.mutate(ds.id);
                      }
                    }}
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {datasources?.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-400">
                  No datasources yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
