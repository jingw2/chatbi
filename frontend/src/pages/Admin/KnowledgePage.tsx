import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

interface KnowledgeItem {
  id: number;
  datasource_id: number;
  type: string;
  title: string;
  content: string;
  created_by: number;
}

interface Datasource {
  id: number;
  name: string;
}

export default function KnowledgePage() {
  const qc = useQueryClient();
  const [dsId, setDsId] = useState<string>("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    type: "rule",
    title: "",
    content: "",
  });

  const { data: datasources } = useQuery<Datasource[]>({
    queryKey: ["datasources"],
    queryFn: async () => (await api.get("/api/v1/datasources")).data,
  });

  const { data: items, isLoading } = useQuery<KnowledgeItem[]>({
    queryKey: ["knowledge", dsId],
    queryFn: async () =>
      (await api.get(`/api/v1/knowledge?datasource_id=${dsId}`)).data,
    enabled: !!dsId,
  });

  const createMutation = useMutation({
    mutationFn: (body: { datasource_id: number; type: string; title: string; content: string }) =>
      api.post("/api/v1/knowledge", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge", dsId] });
      setOpen(false);
      setForm({ type: "rule", title: "", content: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/knowledge/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge", dsId] }),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Knowledge Base</h1>
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
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus size={16} className="mr-1" /> Add Item
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Knowledge Item</DialogTitle>
                </DialogHeader>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    createMutation.mutate({
                      datasource_id: Number(dsId),
                      ...form,
                    });
                  }}
                  className="space-y-3"
                >
                  <div className="space-y-1">
                    <Label>Type</Label>
                    <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rule">Rule</SelectItem>
                        <SelectItem value="fewshot">Few-shot Example</SelectItem>
                        <SelectItem value="glossary">Glossary</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Title</Label>
                    <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
                  </div>
                  <div className="space-y-1">
                    <Label>Content</Label>
                    <textarea
                      value={form.content}
                      onChange={(e) => setForm({ ...form, content: e.target.value })}
                      className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm min-h-[100px]"
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                    {createMutation.isPending ? "Creating..." : "Create"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {!dsId && (
        <p className="text-sm text-gray-400 py-8 text-center">
          Select a datasource to manage knowledge items
        </p>
      )}

      {dsId && isLoading && <p className="text-sm text-gray-400">Loading...</p>}

      {dsId && items && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Content</TableHead>
              <TableHead className="w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <Badge variant="secondary">{item.type}</Badge>
                </TableCell>
                <TableCell className="font-medium">{item.title}</TableCell>
                <TableCell className="max-w-md truncate text-gray-600 text-xs">
                  {item.content}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteMutation.mutate(item.id)}
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-gray-400">
                  No knowledge items yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
