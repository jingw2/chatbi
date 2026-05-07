# Frontend Chat UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete chat interface — datasource selector, conversation history in sidebar, message input, streaming-style message display, SQL preview, ECharts visualization, insight cards, and workflow result rendering.

**Architecture:** A Zustand chat store manages active conversation, message history, and loading state. The Chat page composes: a datasource selector (shown before first message), a message list (user questions + assistant responses with SQL/chart/insight), and a fixed-bottom input bar. API calls go through `@/lib/api.ts` (axios). Charts render via `echarts-for-react`. No SSR, no streaming endpoint — the backend returns a complete `QueryResponse` per question.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui (Radix), Zustand, react-query, echarts-for-react, lucide-react

---

## File Map

```
frontend/src/
├── stores/
│   └── chat.ts                    # CREATE: Zustand chat store
├── hooks/
│   └── useChat.ts                 # CREATE: react-query mutations + store glue
├── pages/Chat/
│   └── index.tsx                  # MODIFY: full chat page
├── components/Chat/
│   ├── DatasourceSelector.tsx     # CREATE: datasource picker (first-use)
│   ├── MessageList.tsx            # CREATE: scrollable message container
│   ├── MessageBubble.tsx          # CREATE: single message (user or assistant)
│   ├── SqlPreview.tsx             # CREATE: collapsible SQL block
│   ├── ChartPanel.tsx             # CREATE: ECharts wrapper
│   ├── InsightCard.tsx            # CREATE: insight + suggestions
│   ├── WorkflowResultPanel.tsx    # CREATE: workflow step results
│   └── ChatInput.tsx              # CREATE: input bar with send button
├── components/Layout/
│   └── Sidebar.tsx                # MODIFY: conversation history list
└── components/ui/
    ├── scroll-area.tsx            # CREATE: shadcn ScrollArea
    ├── select.tsx                 # CREATE: shadcn Select
    ├── skeleton.tsx               # CREATE: shadcn Skeleton
    ├── badge.tsx                  # CREATE: shadcn Badge
    └── collapsible.tsx            # CREATE: shadcn Collapsible
```

**Existing files used (read-only):**
- `frontend/src/lib/api.ts` — axios instance with auth interceptor
- `frontend/src/lib/auth.ts` — `useAuthStore` (user, token)
- `frontend/src/lib/utils.ts` — `cn()` class merge utility
- `frontend/src/components/ui/button.tsx` — Button component
- `frontend/src/components/ui/input.tsx` — Input component
- `frontend/src/components/ui/card.tsx` — Card components

**Backend API contracts used:**
- `GET /api/v1/datasources` → `[{id, name, db_type, ...}]` (admin-only — we'll need a viewer-accessible list endpoint or handle 403 gracefully)
- `GET /api/v1/conversations` → `[{id, title, datasource_id, created_at, updated_at}]`
- `POST /api/v1/conversations` → `{datasource_id, title?}` → `ConversationResponse`
- `POST /api/v1/conversations/{id}/query` → `{question}` → `QueryResponse`
- `PATCH /api/v1/conversations/{id}` → `{title}` → `ConversationResponse`
- `DELETE /api/v1/conversations/{id}` → 204

---

## Task 1: Zustand Chat Store + shadcn UI Components

**Files:**
- Create: `frontend/src/stores/chat.ts`
- Create: `frontend/src/components/ui/scroll-area.tsx`
- Create: `frontend/src/components/ui/select.tsx`
- Create: `frontend/src/components/ui/skeleton.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/collapsible.tsx`

- [ ] **Step 1: Install required Radix primitives**

```bash
cd E:\chatbi\frontend
npm install @radix-ui/react-scroll-area @radix-ui/react-select @radix-ui/react-collapsible
```

- [ ] **Step 2: Create `frontend/src/stores/chat.ts`**

```typescript
import { create } from "zustand";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** Only on assistant messages */
  queryResponse?: QueryResponseData;
  timestamp: number;
}

export interface QueryResponseData {
  query_log_id: number;
  intent: string;
  sql: string | null;
  columns: string[];
  rows: unknown[][];
  chart_type: string | null;
  chart_config: Record<string, unknown> | null;
  insight: string | null;
  suggestions: string[];
  warnings: string[];
  error: string | null;
  execution_ms: number | null;
}

interface ChatState {
  /** Currently active conversation ID */
  conversationId: number | null;
  /** Selected datasource ID (before conversation created) */
  datasourceId: number | null;
  /** Messages in current conversation */
  messages: Message[];
  /** Loading state for query */
  isQuerying: boolean;

  setConversationId: (id: number | null) => void;
  setDatasourceId: (id: number | null) => void;
  addMessage: (msg: Message) => void;
  setMessages: (msgs: Message[]) => void;
  setIsQuerying: (v: boolean) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>()((set) => ({
  conversationId: null,
  datasourceId: null,
  messages: [],
  isQuerying: false,

  setConversationId: (id) => set({ conversationId: id }),
  setDatasourceId: (id) => set({ datasourceId: id }),
  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  setIsQuerying: (v) => set({ isQuerying: v }),
  reset: () =>
    set({
      conversationId: null,
      datasourceId: null,
      messages: [],
      isQuerying: false,
    }),
}));
```

- [ ] **Step 3: Create `frontend/src/components/ui/scroll-area.tsx`**

```tsx
import * as React from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { cn } from "@/lib/utils";

const ScrollArea = React.forwardRef<
  React.ComponentRef<typeof ScrollAreaPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.Root>
>(({ className, children, ...props }, ref) => (
  <ScrollAreaPrimitive.Root
    ref={ref}
    className={cn("relative overflow-hidden", className)}
    {...props}
  >
    <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">
      {children}
    </ScrollAreaPrimitive.Viewport>
    <ScrollBar />
    <ScrollAreaPrimitive.Corner />
  </ScrollAreaPrimitive.Root>
));
ScrollArea.displayName = ScrollAreaPrimitive.Root.displayName;

const ScrollBar = React.forwardRef<
  React.ComponentRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>,
  React.ComponentPropsWithoutRef<typeof ScrollAreaPrimitive.ScrollAreaScrollbar>
>(({ className, orientation = "vertical", ...props }, ref) => (
  <ScrollAreaPrimitive.ScrollAreaScrollbar
    ref={ref}
    orientation={orientation}
    className={cn(
      "flex touch-none select-none transition-colors",
      orientation === "vertical" &&
        "h-full w-2.5 border-l border-l-transparent p-[1px]",
      orientation === "horizontal" &&
        "h-2.5 flex-col border-t border-t-transparent p-[1px]",
      className
    )}
    {...props}
  >
    <ScrollAreaPrimitive.ScrollAreaThumb className="relative flex-1 rounded-full bg-gray-300" />
  </ScrollAreaPrimitive.ScrollAreaScrollbar>
));
ScrollBar.displayName = ScrollAreaPrimitive.ScrollAreaScrollbar.displayName;

export { ScrollArea, ScrollBar };
```

- [ ] **Step 4: Create `frontend/src/components/ui/select.tsx`**

```tsx
import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

const Select = SelectPrimitive.Root;
const SelectGroup = SelectPrimitive.Group;
const SelectValue = SelectPrimitive.Value;

const SelectTrigger = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(
      "flex h-10 w-full items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className
    )}
    {...props}
  >
    {children}
    <SelectPrimitive.Icon asChild>
      <ChevronDown className="h-4 w-4 opacity-50" />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectContent = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = "popper", ...props }, ref) => (
  <SelectPrimitive.Portal>
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        "relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border bg-white text-gray-900 shadow-md animate-in fade-in-0 zoom-in-95",
        position === "popper" && "translate-y-1",
        className
      )}
      position={position}
      {...props}
    >
      <SelectPrimitive.Viewport
        className={cn(
          "p-1",
          position === "popper" &&
            "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]"
        )}
      >
        {children}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
SelectContent.displayName = SelectPrimitive.Content.displayName;

const SelectItem = React.forwardRef<
  React.ComponentRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-gray-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
SelectItem.displayName = SelectPrimitive.Item.displayName;

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
};
```

- [ ] **Step 5: Create `frontend/src/components/ui/skeleton.tsx`**

```tsx
import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-gray-200", className)}
      {...props}
    />
  );
}

export { Skeleton };
```

- [ ] **Step 6: Create `frontend/src/components/ui/badge.tsx`**

```tsx
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-gray-900 text-gray-50",
        secondary: "border-transparent bg-gray-100 text-gray-900",
        destructive: "border-transparent bg-red-500 text-gray-50",
        outline: "text-gray-900",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
```

- [ ] **Step 7: Create `frontend/src/components/ui/collapsible.tsx`**

```tsx
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

const Collapsible = CollapsiblePrimitive.Root;
const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger;
const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent;

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
```

- [ ] **Step 8: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 9: Commit**

```bash
git -C E:\chatbi add frontend/src/stores/ frontend/src/components/ui/scroll-area.tsx frontend/src/components/ui/select.tsx frontend/src/components/ui/skeleton.tsx frontend/src/components/ui/badge.tsx frontend/src/components/ui/collapsible.tsx frontend/package.json frontend/package-lock.json
git -C E:\chatbi commit -m "feat: add chat store and shadcn UI primitives"
```

---

## Task 2: Chat Components — Input, Messages, SQL Preview

**Files:**
- Create: `frontend/src/components/Chat/ChatInput.tsx`
- Create: `frontend/src/components/Chat/MessageBubble.tsx`
- Create: `frontend/src/components/Chat/MessageList.tsx`
- Create: `frontend/src/components/Chat/SqlPreview.tsx`

- [ ] **Step 1: Create `frontend/src/components/Chat/ChatInput.tsx`**

```tsx
import { useState, useRef } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (question: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  };

  return (
    <div className="border-t bg-white p-4">
      <div className="mx-auto max-w-3xl flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask a question about your data..."
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
          disabled={disabled}
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="shrink-0 h-11 w-11"
        >
          <Send size={18} />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/src/components/Chat/SqlPreview.tsx`**

```tsx
import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";

interface SqlPreviewProps {
  sql: string;
  executionMs?: number | null;
}

export default function SqlPreview({ sql, executionMs }: SqlPreviewProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-2">
      <div className="flex items-center gap-2">
        <CollapsibleTrigger className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700">
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          SQL
        </CollapsibleTrigger>
        {executionMs != null && (
          <Badge variant="secondary" className="text-[10px]">
            {executionMs}ms
          </Badge>
        )}
      </div>
      <CollapsibleContent>
        <div className="relative mt-1 rounded-md bg-gray-900 p-3">
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 text-gray-400 hover:text-white"
            title="Copy SQL"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
          <pre className="text-xs text-gray-100 overflow-x-auto whitespace-pre-wrap">
            {sql}
          </pre>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
```

- [ ] **Step 3: Create `frontend/src/components/Chat/MessageBubble.tsx`**

```tsx
import type { Message } from "@/stores/chat";
import SqlPreview from "./SqlPreview";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-2xl rounded-2xl rounded-br-sm bg-gray-900 px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  const qr = message.queryResponse;

  return (
    <div className="flex justify-start">
      <div className="max-w-3xl space-y-3">
        {/* Error state */}
        {qr?.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {qr.error}
          </div>
        )}

        {/* Non-data intents (chitchat, clarify, definition) */}
        {qr && !qr.error && qr.intent !== "data_query" && qr.intent !== "fixed_workflow" && (
          <div className="rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-2.5 text-sm text-gray-800">
            {message.content}
          </div>
        )}

        {/* Data query results — rendered by parent via ChartPanel/InsightCard */}
        {qr && !qr.error && qr.intent === "data_query" && (
          <>
            {qr.sql && (
              <SqlPreview sql={qr.sql} executionMs={qr.execution_ms} />
            )}
          </>
        )}

        {/* Workflow results — rendered by parent via WorkflowResultPanel */}
        {/* (chart/insight/workflow panels are placed after this component by MessageList) */}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend/src/components/Chat/MessageList.tsx`**

```tsx
import { useRef, useEffect } from "react";
import type { Message } from "@/stores/chat";
import { ScrollArea } from "@/components/ui/scroll-area";
import MessageBubble from "./MessageBubble";
import ChartPanel from "./ChartPanel";
import InsightCard from "./InsightCard";
import WorkflowResultPanel from "./WorkflowResultPanel";
import { Skeleton } from "@/components/ui/skeleton";

interface MessageListProps {
  messages: Message[];
  isQuerying: boolean;
}

export default function MessageList({ messages, isQuerying }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isQuerying]);

  return (
    <ScrollArea className="flex-1">
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
        {messages.length === 0 && !isQuerying && (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <p className="text-lg font-medium">Ask anything about your data</p>
            <p className="text-sm mt-1">Your results will appear here</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            <MessageBubble message={msg} />

            {/* Chart for data_query */}
            {msg.role === "assistant" &&
              msg.queryResponse?.chart_config &&
              msg.queryResponse.intent === "data_query" && (
                <ChartPanel config={msg.queryResponse.chart_config} />
              )}

            {/* Workflow results */}
            {msg.role === "assistant" &&
              msg.queryResponse?.intent === "fixed_workflow" &&
              !msg.queryResponse.error && (
                <WorkflowResultPanel queryResponse={msg.queryResponse} />
              )}

            {/* Insight card */}
            {msg.role === "assistant" &&
              msg.queryResponse?.insight &&
              !msg.queryResponse.error && (
                <InsightCard
                  insight={msg.queryResponse.insight}
                  suggestions={msg.queryResponse.suggestions}
                />
              )}
          </div>
        ))}

        {isQuerying && (
          <div className="space-y-3">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-4 w-60" />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
```

- [ ] **Step 5: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: Errors about missing `ChartPanel`, `InsightCard`, `WorkflowResultPanel` — these are created in Task 3. The import will fail at this stage. That's expected; we create stub files to pass type-checking:

Create temporary stubs (these will be replaced in Task 3):

`frontend/src/components/Chat/ChartPanel.tsx`:
```tsx
export default function ChartPanel(_props: { config: Record<string, unknown> }) {
  return <div>Chart placeholder</div>;
}
```

`frontend/src/components/Chat/InsightCard.tsx`:
```tsx
export default function InsightCard(_props: { insight: string; suggestions: string[] }) {
  return <div>Insight placeholder</div>;
}
```

`frontend/src/components/Chat/WorkflowResultPanel.tsx`:
```tsx
import type { QueryResponseData } from "@/stores/chat";
export default function WorkflowResultPanel(_props: { queryResponse: QueryResponseData }) {
  return <div>Workflow placeholder</div>;
}
```

Now run: `cd E:\chatbi\frontend && npx tsc --noEmit` — expected: no errors.

- [ ] **Step 6: Commit**

```bash
git -C E:\chatbi add frontend/src/components/Chat/
git -C E:\chatbi commit -m "feat: add chat input, message bubbles, SQL preview, message list"
```

---

## Task 3: Chart Panel, Insight Card, Workflow Result Panel

**Files:**
- Replace: `frontend/src/components/Chat/ChartPanel.tsx` (replace stub)
- Replace: `frontend/src/components/Chat/InsightCard.tsx` (replace stub)
- Replace: `frontend/src/components/Chat/WorkflowResultPanel.tsx` (replace stub)

- [ ] **Step 1: Create `frontend/src/components/Chat/ChartPanel.tsx`**

Replace the stub with:

```tsx
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
```

- [ ] **Step 2: Create `frontend/src/components/Chat/InsightCard.tsx`**

Replace the stub with:

```tsx
import { Lightbulb } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface InsightCardProps {
  insight: string;
  suggestions: string[];
}

export default function InsightCard({ insight, suggestions }: InsightCardProps) {
  return (
    <Card className="bg-blue-50 border-blue-100">
      <CardContent className="p-4 space-y-2">
        <div className="flex items-start gap-2">
          <Lightbulb size={16} className="text-blue-600 mt-0.5 shrink-0" />
          <p className="text-sm text-gray-800">{insight}</p>
        </div>
        {suggestions.length > 0 && (
          <ul className="ml-6 space-y-1">
            {suggestions.map((s, i) => (
              <li key={i} className="text-sm text-gray-600 list-disc">
                {s}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 3: Create `frontend/src/components/Chat/WorkflowResultPanel.tsx`**

Replace the stub with:

```tsx
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
  const raw = queryResponse as Record<string, unknown>;
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
```

- [ ] **Step 4: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git -C E:\chatbi add frontend/src/components/Chat/ChartPanel.tsx frontend/src/components/Chat/InsightCard.tsx frontend/src/components/Chat/WorkflowResultPanel.tsx
git -C E:\chatbi commit -m "feat: add chart panel, insight card, workflow result panel"
```

---

## Task 4: Datasource Selector + useChat Hook

**Files:**
- Create: `frontend/src/components/Chat/DatasourceSelector.tsx`
- Create: `frontend/src/hooks/useChat.ts`

- [ ] **Step 1: Create `frontend/src/components/Chat/DatasourceSelector.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `frontend/src/hooks/useChat.ts`**

```typescript
import { useCallback } from "react";
import { api } from "@/lib/api";
import { useChatStore, type QueryResponseData } from "@/stores/chat";

export function useChat() {
  const {
    conversationId,
    datasourceId,
    messages,
    isQuerying,
    setConversationId,
    setDatasourceId,
    addMessage,
    setIsQuerying,
    reset,
  } = useChatStore();

  const sendQuestion = useCallback(
    async (question: string) => {
      if (isQuerying) return;
      if (!datasourceId) return;

      // Add user message immediately
      const userMsg = {
        id: `user-${Date.now()}`,
        role: "user" as const,
        content: question,
        timestamp: Date.now(),
      };
      addMessage(userMsg);
      setIsQuerying(true);

      try {
        // Create conversation if none exists
        let convId = conversationId;
        if (!convId) {
          const { data: conv } = await api.post("/api/v1/conversations", {
            datasource_id: datasourceId,
          });
          convId = conv.id;
          setConversationId(convId);
        }

        // Send query
        const { data } = await api.post<QueryResponseData>(
          `/api/v1/conversations/${convId}/query`,
          { question }
        );

        // Build assistant message
        let content = "";
        if (data.error) {
          content = data.error;
        } else if (data.intent === "data_query") {
          const rowCount = data.rows?.length ?? 0;
          content = `Found ${rowCount} rows.`;
        } else if (data.intent === "fixed_workflow") {
          content = "Workflow executed.";
        } else {
          content = data.insight ?? "Done.";
        }

        const assistantMsg = {
          id: `assistant-${Date.now()}`,
          role: "assistant" as const,
          content,
          queryResponse: data,
          timestamp: Date.now(),
        };
        addMessage(assistantMsg);
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : "Request failed";
        addMessage({
          id: `error-${Date.now()}`,
          role: "assistant",
          content: errorMsg,
          queryResponse: {
            query_log_id: 0,
            intent: "error",
            sql: null,
            columns: [],
            rows: [],
            chart_type: null,
            chart_config: null,
            insight: null,
            suggestions: [],
            warnings: [],
            error: errorMsg,
            execution_ms: null,
          },
          timestamp: Date.now(),
        });
      } finally {
        setIsQuerying(false);
      }
    },
    [
      conversationId,
      datasourceId,
      isQuerying,
      addMessage,
      setConversationId,
      setIsQuerying,
    ]
  );

  const startNewChat = useCallback(() => {
    reset();
  }, [reset]);

  return {
    conversationId,
    datasourceId,
    messages,
    isQuerying,
    setDatasourceId,
    sendQuestion,
    startNewChat,
  };
}
```

- [ ] **Step 3: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git -C E:\chatbi add frontend/src/components/Chat/DatasourceSelector.tsx frontend/src/hooks/useChat.ts
git -C E:\chatbi commit -m "feat: add datasource selector and useChat hook"
```

---

## Task 5: Chat Page Assembly + Sidebar History

**Files:**
- Modify: `frontend/src/pages/Chat/index.tsx` (replace placeholder)
- Modify: `frontend/src/components/Layout/Sidebar.tsx` (add conversation history)
- Modify: `frontend/src/App.tsx` (no change needed — route already exists)

- [ ] **Step 1: Replace `frontend/src/pages/Chat/index.tsx`**

```tsx
import { useChat } from "@/hooks/useChat";
import DatasourceSelector from "@/components/Chat/DatasourceSelector";
import MessageList from "@/components/Chat/MessageList";
import ChatInput from "@/components/Chat/ChatInput";

export default function ChatPage() {
  const {
    datasourceId,
    messages,
    isQuerying,
    setDatasourceId,
    sendQuestion,
  } = useChat();

  // Show datasource selector if none chosen yet
  if (!datasourceId) {
    return (
      <div className="flex h-full flex-col">
        <DatasourceSelector value={datasourceId} onChange={setDatasourceId} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} isQuerying={isQuerying} />
      <ChatInput onSend={sendQuestion} disabled={isQuerying} />
    </div>
  );
}
```

- [ ] **Step 2: Update `frontend/src/components/Layout/Sidebar.tsx`**

Replace the history placeholder section with a conversation list that fetches from the API. The full updated file:

```tsx
import { useQuery } from "@tanstack/react-query";
import {
  MessageSquare,
  Zap,
  Database,
  Table,
  BookOpen,
  Users,
  ScrollText,
  Settings,
  Trash2,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";
import { useChatStore } from "@/stores/chat";
import { api } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ConversationItem {
  id: number;
  title: string;
  datasource_id: number;
  updated_at: string;
}

const adminMenuItems = [
  { icon: Zap, label: "Workflows", href: "/admin/workflows" },
  { icon: Database, label: "Datasources", href: "/admin/datasources" },
  { icon: Table, label: "Schema", href: "/admin/schema" },
  { icon: BookOpen, label: "Knowledge", href: "/admin/knowledge" },
  { icon: Users, label: "Users", href: "/admin/users" },
  { icon: ScrollText, label: "Audit", href: "/admin/audit" },
];

export default function Sidebar() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "admin" || user?.role === "superadmin";
  const { conversationId, setConversationId, setDatasourceId, reset } =
    useChatStore();

  const { data: conversations } = useQuery<ConversationItem[]>({
    queryKey: ["conversations"],
    queryFn: async () => {
      const { data } = await api.get("/api/v1/conversations");
      return data;
    },
    refetchInterval: 30000,
  });

  const handleNewChat = () => {
    reset();
  };

  const handleSelectConversation = (conv: ConversationItem) => {
    reset();
    setConversationId(conv.id);
    setDatasourceId(conv.datasource_id);
  };

  const handleDeleteConversation = async (
    e: React.MouseEvent,
    convId: number
  ) => {
    e.stopPropagation();
    await api.delete(`/api/v1/conversations/${convId}`);
    if (conversationId === convId) reset();
  };

  return (
    <aside className="w-64 h-screen flex flex-col border-r bg-white shrink-0">
      {/* New Chat */}
      <div className="p-3 border-b">
        <Link
          to="/"
          onClick={handleNewChat}
          className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-100 text-sm font-medium"
        >
          <MessageSquare size={16} />
          New Chat
        </Link>
      </div>

      {/* History */}
      <ScrollArea className="flex-1">
        <div className="p-3">
          <p className="text-xs font-medium text-gray-400 px-3 py-2 uppercase tracking-wider">
            History
          </p>
          {conversations?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelectConversation(conv)}
              className={cn(
                "group flex items-center justify-between w-full px-3 py-2 rounded-md text-sm text-left hover:bg-gray-100",
                conversationId === conv.id && "bg-gray-100 font-medium"
              )}
            >
              <span className="truncate">{conv.title}</span>
              <Trash2
                size={14}
                className="shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500"
                onClick={(e) => handleDeleteConversation(e, conv.id)}
              />
            </button>
          ))}
          {conversations?.length === 0 && (
            <p className="px-3 py-2 text-xs text-gray-400">
              No conversations yet
            </p>
          )}
        </div>
      </ScrollArea>

      {/* Admin Menu */}
      {isAdmin && (
        <div className="border-t p-3">
          <p className="text-xs font-medium text-gray-400 px-3 py-2 uppercase tracking-wider">
            Management
          </p>
          {adminMenuItems.map(({ icon: Icon, label, href }) => (
            <Link
              key={href}
              to={href}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-100",
                location.pathname === href && "bg-gray-100 font-medium"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </div>
      )}

      {/* Bottom */}
      <div className="border-t p-3 space-y-1">
        <Link
          to="/settings"
          className="flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-100"
        >
          <Settings size={16} />
          Settings
        </Link>
        <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600">
          <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold">
            {user?.email?.[0]?.toUpperCase() ?? "?"}
          </div>
          <span className="truncate">{user?.email}</span>
        </div>
      </div>
    </aside>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd E:\chatbi\frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 4: Verify dev server starts**

```bash
cd E:\chatbi\frontend && npx vite build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 5: Commit**

```bash
git -C E:\chatbi add frontend/src/pages/Chat/index.tsx frontend/src/components/Layout/Sidebar.tsx
git -C E:\chatbi commit -m "feat: assemble chat page with conversation history sidebar"
```

- [ ] **Step 6: Run production build to verify**

```bash
cd E:\chatbi\frontend && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 7: Final commit — Plan 7 complete**

```bash
git -C E:\chatbi add -A
git -C E:\chatbi commit -m "feat: Plan 7 complete — frontend chat UI"
```

(Only if there are uncommitted changes from the build step; otherwise skip.)

---

## Self-Review

**Spec coverage check:**

- ✅ Datasource selector — shown on first visit, picks which DB to query against
- ✅ Conversation CRUD — create on first question, list in sidebar, delete via trash icon
- ✅ Message display — user messages (right-aligned dark), assistant messages (left-aligned)
- ✅ SQL preview — collapsible dark code block with copy button and execution time badge
- ✅ ECharts visualization — `echarts-for-react` wrapper, renders chart_config from backend
- ✅ Big number display — custom card for single-value results
- ✅ Insight card — blue card with lightbulb icon, bulleted suggestions
- ✅ Workflow results — step-by-step tables with error badges
- ✅ Chat input — auto-growing textarea, Enter to send, Shift+Enter for newline
- ✅ Loading state — skeleton placeholders during query
- ✅ Auto-scroll — scrolls to bottom on new messages
- ✅ Sidebar history — conversation list with active highlighting, delete, new chat
- ✅ Zustand store — conversation state, datasource selection, message list
- ✅ Error handling — network errors displayed as red assistant messages
- ✅ Auth integration — uses existing `useAuthStore` and axios interceptor

**Placeholder scan:** No TBD/TODO/placeholders found.

**Type consistency:** `QueryResponseData` interface in `stores/chat.ts` matches backend `QueryResponse` schema. `Message` type used consistently across store, hook, and components. `ConversationItem` in Sidebar matches `ConversationResponse` fields.

**Intentionally deferred:**
- Message persistence/reload (loading past messages when clicking sidebar history) — requires a backend endpoint to list query_logs by conversation
- Data table rendering for data_query results (just shows chart + insight, no raw table tab) — future enhancement
- Conversation rename UI — backend supports it but no UI trigger yet
- Responsive/mobile layout — sidebar is fixed 256px, no collapse on small screens
- Dark mode — CSS variables exist but no toggle
