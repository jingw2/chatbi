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
