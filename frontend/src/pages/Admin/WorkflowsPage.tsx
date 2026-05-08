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

interface WorkflowItem {
  id: number;
  name: string;
  datasource_id: number;
  trigger_keywords: string[];
  steps: { name: string; sql: string }[];
  is_active: boolean;
  created_at: string;
}

interface Datasource {
  id: number;
  name: string;
}

export default function WorkflowsPage() {
  const qc = useQueryClient();
  const [dsId, setDsId] = useState<string>("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    keywords: "",
    steps: [{ name: "", sql: "" }],
  });

  const { data: datasources } = useQuery<Datasource[]>({
    queryKey: ["datasources"],
    queryFn: async () => (await api.get("/api/v1/datasources")).data,
  });

  const { data: workflows, isLoading } = useQuery<WorkflowItem[]>({
    queryKey: ["workflows", dsId],
    queryFn: async () =>
      (await api.get(`/api/v1/workflows?datasource_id=${dsId}`)).data,
    enabled: !!dsId,
  });

  const createMutation = useMutation({
    mutationFn: (body: {
      name: string;
      datasource_id: number;
      trigger_keywords: string[];
      steps: { name: string; sql: string }[];
    }) => api.post("/api/v1/workflows", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workflows", dsId] });
      setOpen(false);
      setForm({ name: "", keywords: "", steps: [{ name: "", sql: "" }] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.patch(`/api/v1/workflows/${id}`, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows", dsId] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/workflows/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workflows", dsId] }),
  });

  const addStep = () =>
    setForm({ ...form, steps: [...form.steps, { name: "", sql: "" }] });

  const updateStep = (idx: number, field: "name" | "sql", val: string) => {
    const steps = [...form.steps];
    steps[idx] = { ...steps[idx], [field]: val };
    setForm({ ...form, steps });
  };

  const removeStep = (idx: number) => {
    const steps = form.steps.filter((_, i) => i !== idx);
    setForm({ ...form, steps: steps.length ? steps : [{ name: "", sql: "" }] });
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Workflows</h1>
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
                  <Plus size={16} className="mr-1" /> Add Workflow
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add Workflow</DialogTitle>
                </DialogHeader>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    createMutation.mutate({
                      name: form.name,
                      datasource_id: Number(dsId),
                      trigger_keywords: form.keywords
                        .split(",")
                        .map((k) => k.trim())
                        .filter(Boolean),
                      steps: form.steps.filter((s) => s.name && s.sql),
                    });
                  }}
                  className="space-y-3"
                >
                  <div className="space-y-1">
                    <Label>Name</Label>
                    <Input
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Trigger Keywords (comma-separated)</Label>
                    <Input
                      value={form.keywords}
                      onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                      placeholder="月度报表, monthly report"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Steps</Label>
                      <Button type="button" variant="outline" size="sm" onClick={addStep}>
                        <Plus size={14} className="mr-1" /> Step
                      </Button>
                    </div>
                    {form.steps.map((step, i) => (
                      <div key={i} className="flex gap-2 items-start">
                        <Input
                          className="w-32"
                          placeholder="Step name"
                          value={step.name}
                          onChange={(e) => updateStep(i, "name", e.target.value)}
                        />
                        <textarea
                          className="flex-1 rounded-md border border-gray-200 px-3 py-2 text-sm min-h-[60px]"
                          placeholder="SELECT ..."
                          value={step.sql}
                          onChange={(e) => updateStep(i, "sql", e.target.value)}
                        />
                        {form.steps.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => removeStep(i)}
                          >
                            <Trash2 size={14} className="text-red-500" />
                          </Button>
                        )}
                      </div>
                    ))}
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
          Select a datasource to manage workflows
        </p>
      )}

      {dsId && isLoading && <p className="text-sm text-gray-400">Loading...</p>}

      {dsId && workflows && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Keywords</TableHead>
              <TableHead>Steps</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {workflows.map((wf) => (
              <TableRow key={wf.id}>
                <TableCell className="font-medium">{wf.name}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {wf.trigger_keywords.map((kw, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {kw}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>{wf.steps.length} step(s)</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      toggleMutation.mutate({ id: wf.id, is_active: !wf.is_active })
                    }
                  >
                    <Badge variant={wf.is_active ? "secondary" : "destructive"}>
                      {wf.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </Button>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteMutation.mutate(wf.id)}
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {workflows.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-400">
                  No workflows yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
