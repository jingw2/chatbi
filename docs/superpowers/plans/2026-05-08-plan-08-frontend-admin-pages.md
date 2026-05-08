# Frontend Admin Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the five admin management pages linked from the sidebar: Datasources, Schema, Knowledge, Workflows, and Users. Each page is a table-based CRUD UI backed by existing REST APIs. Also add an Audit (query logs) read-only page.

**Architecture:** Each admin page follows the same pattern: a react-query list query, a table component, and modal dialogs for create/edit. All admin pages are protected by role check (admin/superadmin). Pages are routed under `/admin/*` and rendered inside the existing `MainLayout`. Shared UI components (`Dialog`, `Table`, `Tabs`) are created once and reused across all pages.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui (Radix), react-query, lucide-react

---

## File Map

```
frontend/src/
├── components/ui/
│   ├── dialog.tsx               # CREATE: shadcn Dialog
│   ├── table.tsx                # CREATE: shadcn Table
│   └── tabs.tsx                 # CREATE: shadcn Tabs
├── pages/Admin/
│   ├── DatasourcesPage.tsx      # CREATE: CRUD datasources
│   ├── SchemaPage.tsx           # CREATE: tables/columns management + sync
│   ├── KnowledgePage.tsx        # CREATE: knowledge items CRUD
│   ├── WorkflowsPage.tsx       # CREATE: workflow definitions CRUD
│   ├── UsersPage.tsx            # CREATE: user management
│   └── AuditPage.tsx            # CREATE: query logs read-only table
└── App.tsx                      # MODIFY: add admin routes
```

**Backend API contracts:**
- Datasources: `GET/POST /api/v1/datasources`, `DELETE /api/v1/datasources/{id}`
- Schema: `GET /api/v1/schema/{ds_id}/tables`, `PATCH /api/v1/schema/tables/{id}`, `GET /api/v1/schema/tables/{id}/columns`, `PATCH /api/v1/schema/columns/{id}`, `POST /api/v1/schema/{ds_id}/sync`
- Knowledge: `GET/POST /api/v1/knowledge?datasource_id=`, `PATCH/DELETE /api/v1/knowledge/{id}`
- Workflows: `GET/POST /api/v1/workflows?datasource_id=`, `PATCH/DELETE /api/v1/workflows/{id}`
- Users: `GET/POST /api/v1/users`, `PATCH /api/v1/users/{id}`

---

## Task 1: Shared UI Components (Dialog, Table, Tabs)

**Files:**
- Create: `frontend/src/components/ui/dialog.tsx`
- Create: `frontend/src/components/ui/table.tsx`
- Create: `frontend/src/components/ui/tabs.tsx`

- [ ] **Step 1: Install Radix primitives**

```bash
cd E:\chatbi\frontend
npm install @radix-ui/react-dialog @radix-ui/react-tabs
```

- [ ] **Step 2: Create `frontend/src/components/ui/dialog.tsx`**

```tsx
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogClose = DialogPrimitive.Close;
const DialogPortal = DialogPrimitive.Portal;

const DialogOverlay = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-white p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)}
    {...props}
  />
);
DialogHeader.displayName = "DialogHeader";

const DialogTitle = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold leading-none tracking-tight", className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ComponentRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-gray-500", className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Dialog,
  DialogTrigger,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
};
```

- [ ] **Step 3: Create `frontend/src/components/ui/table.tsx`**

```tsx
import * as React from "react";
import { cn } from "@/lib/utils";

const Table = React.forwardRef<
  HTMLTableElement,
  React.HTMLAttributes<HTMLTableElement>
>(({ className, ...props }, ref) => (
  <div className="relative w-full overflow-auto">
    <table
      ref={ref}
      className={cn("w-full caption-bottom text-sm", className)}
      {...props}
    />
  </div>
));
Table.displayName = "Table";

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead ref={ref} className={cn("[&_tr]:border-b", className)} {...props} />
));
TableHeader.displayName = "TableHeader";

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={cn("[&_tr:last-child]:border-0", className)}
    {...props}
  />
));
TableBody.displayName = "TableBody";

const TableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>(({ className, ...props }, ref) => (
  <tr
    ref={ref}
    className={cn(
      "border-b transition-colors hover:bg-gray-50 data-[state=selected]:bg-gray-100",
      className
    )}
    {...props}
  />
));
TableRow.displayName = "TableRow";

const TableHead = React.forwardRef<
  HTMLTableCellElement,
  React.ThHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <th
    ref={ref}
    className={cn(
      "h-10 px-4 text-left align-middle font-medium text-gray-500 [&:has([role=checkbox])]:pr-0",
      className
    )}
    {...props}
  />
));
TableHead.displayName = "TableHead";

const TableCell = React.forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...props }, ref) => (
  <td
    ref={ref}
    className={cn("px-4 py-3 align-middle [&:has([role=checkbox])]:pr-0", className)}
    {...props}
  />
));
TableCell.displayName = "TableCell";

export { Table, TableHeader, TableBody, TableRow, TableHead, TableCell };
```

- [ ] **Step 4: Create `frontend/src/components/ui/tabs.tsx`**

```tsx
import * as React from "react";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500",
      className
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm",
      className
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ComponentRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
```

- [ ] **Step 5: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git -C E:\chatbi add frontend/src/components/ui/dialog.tsx frontend/src/components/ui/table.tsx frontend/src/components/ui/tabs.tsx frontend/package.json frontend/package-lock.json
git -C E:\chatbi commit -m "feat: add Dialog, Table, Tabs shadcn UI components"
```

---

## Task 2: Datasources + Users Admin Pages

**Files:**
- Create: `frontend/src/pages/Admin/DatasourcesPage.tsx`
- Create: `frontend/src/pages/Admin/UsersPage.tsx`

- [ ] **Step 1: Create `frontend/src/pages/Admin/DatasourcesPage.tsx`**

```tsx
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
                    onClick={() => deleteMutation.mutate(ds.id)}
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
```

- [ ] **Step 2: Create `frontend/src/pages/Admin/UsersPage.tsx`**

```tsx
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
import { Plus } from "lucide-react";

interface UserItem {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

export default function UsersPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", role: "viewer" });

  const { data: users, isLoading } = useQuery<UserItem[]>({
    queryKey: ["users"],
    queryFn: async () => (await api.get("/api/v1/users")).data,
  });

  const createMutation = useMutation({
    mutationFn: (body: typeof form) => api.post("/api/v1/users", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setOpen(false);
      setForm({ email: "", password: "", role: "viewer" });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...body }: { id: number; role?: string; is_active?: boolean }) =>
      api.patch(`/api/v1/users/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Users</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus size={16} className="mr-1" /> Add User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add User</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate(form);
              }}
              className="space-y-3"
            >
              <div className="space-y-1">
                <Label>Email</Label>
                <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>
              <div className="space-y-1">
                <Label>Password</Label>
                <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
              </div>
              <div className="space-y-1">
                <Label>Role</Label>
                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">Viewer</SelectItem>
                    <SelectItem value="analyst">Analyst</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="superadmin">Superadmin</SelectItem>
                  </SelectContent>
                </Select>
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
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users?.map((u) => (
              <TableRow key={u.id}>
                <TableCell className="font-medium">{u.email}</TableCell>
                <TableCell>
                  <Select
                    value={u.role}
                    onValueChange={(v) => updateMutation.mutate({ id: u.id, role: v })}
                  >
                    <SelectTrigger className="w-32 h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="viewer">Viewer</SelectItem>
                      <SelectItem value="analyst">Analyst</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="superadmin">Superadmin</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Badge variant={u.is_active ? "secondary" : "destructive"}>
                    {u.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      updateMutation.mutate({ id: u.id, is_active: !u.is_active })
                    }
                  >
                    {u.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git -C E:\chatbi add frontend/src/pages/Admin/DatasourcesPage.tsx frontend/src/pages/Admin/UsersPage.tsx
git -C E:\chatbi commit -m "feat: add Datasources and Users admin pages"
```

---

## Task 3: Schema + Knowledge Admin Pages

**Files:**
- Create: `frontend/src/pages/Admin/SchemaPage.tsx`
- Create: `frontend/src/pages/Admin/KnowledgePage.tsx`

- [ ] **Step 1: Create `frontend/src/pages/Admin/SchemaPage.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `frontend/src/pages/Admin/KnowledgePage.tsx`**

```tsx
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
```

- [ ] **Step 3: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git -C E:\chatbi add frontend/src/pages/Admin/SchemaPage.tsx frontend/src/pages/Admin/KnowledgePage.tsx
git -C E:\chatbi commit -m "feat: add Schema and Knowledge admin pages"
```

---

## Task 4: Workflows + Audit Pages

**Files:**
- Create: `frontend/src/pages/Admin/WorkflowsPage.tsx`
- Create: `frontend/src/pages/Admin/AuditPage.tsx`

- [ ] **Step 1: Create `frontend/src/pages/Admin/WorkflowsPage.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `frontend/src/pages/Admin/AuditPage.tsx`**

This page needs a backend endpoint for query logs. Since we don't have a dedicated list endpoint yet, we'll create a simple page that shows "Coming soon" with a placeholder. If there IS a query_logs list endpoint, we'd use it here.

```tsx
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
```

- [ ] **Step 3: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git -C E:\chatbi add frontend/src/pages/Admin/WorkflowsPage.tsx frontend/src/pages/Admin/AuditPage.tsx
git -C E:\chatbi commit -m "feat: add Workflows and Audit admin pages"
```

---

## Task 5: Wire Admin Routes into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update `frontend/src/App.tsx`**

Replace with:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "@/lib/auth";
import MainLayout from "@/components/Layout/MainLayout";
import LoginPage from "@/pages/Login";
import ChatPage from "@/pages/Chat";
import DatasourcesPage from "@/pages/Admin/DatasourcesPage";
import SchemaPage from "@/pages/Admin/SchemaPage";
import KnowledgePage from "@/pages/Admin/KnowledgePage";
import WorkflowsPage from "@/pages/Admin/WorkflowsPage";
import UsersPage from "@/pages/Admin/UsersPage";
import AuditPage from "@/pages/Admin/AuditPage";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin" && user.role !== "superadmin") {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<ChatPage />} />
            <Route
              path="admin/datasources"
              element={<AdminRoute><DatasourcesPage /></AdminRoute>}
            />
            <Route
              path="admin/schema"
              element={<AdminRoute><SchemaPage /></AdminRoute>}
            />
            <Route
              path="admin/knowledge"
              element={<AdminRoute><KnowledgePage /></AdminRoute>}
            />
            <Route
              path="admin/workflows"
              element={<AdminRoute><WorkflowsPage /></AdminRoute>}
            />
            <Route
              path="admin/users"
              element={<AdminRoute><UsersPage /></AdminRoute>}
            />
            <Route
              path="admin/audit"
              element={<AdminRoute><AuditPage /></AdminRoute>}
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Run production build**

```bash
cd E:\chatbi\frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git -C E:\chatbi add frontend/src/App.tsx
git -C E:\chatbi commit -m "feat: Plan 8 complete — wire admin routes into App"
```

---

## Self-Review

**Spec coverage check:**

- ✅ Datasources page — list, create (dialog form), delete
- ✅ Schema page — datasource selector, table list with expand-to-columns, inline edit description/examples/notes, sync button, toggle active
- ✅ Knowledge page — datasource selector, list items by type, create (rule/fewshot/glossary), delete
- ✅ Workflows page — datasource selector, list with keywords badges, create (multi-step form), toggle active, delete
- ✅ Users page — list, create (email/password/role), inline role change, activate/deactivate
- ✅ Audit page — placeholder (backend endpoint needed)
- ✅ Admin route protection — `AdminRoute` component checks role
- ✅ All sidebar links (`/admin/datasources`, `/admin/schema`, etc.) wired to pages
- ✅ Shared UI: Dialog, Table, Tabs components

**Placeholder scan:** Only the Audit page is a deliberate placeholder (backend endpoint missing). No TBD/TODO in code.

**Type consistency:** All TypeScript interfaces match backend Pydantic response schemas. API paths match backend router prefixes.

**Intentionally deferred:**
- Audit log list endpoint (backend) — needed for full AuditPage
- Knowledge item inline edit — only create/delete, no PATCH UI (backend supports it)
- Workflow edit dialog — only create/toggle/delete, no full edit dialog
- Pagination — all list pages fetch full result sets
- Datasource connection test before save
- Search/filter on admin tables
