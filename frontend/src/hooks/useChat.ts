import { useCallback, useRef } from "react";
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

  // Use a ref to guard against double-sends — immune to stale closures
  const queryingRef = useRef(false);

  const sendQuestion = useCallback(
    async (question: string) => {
      if (queryingRef.current) return;
      if (!datasourceId) return;

      // Add user message immediately
      const userMsg = {
        id: `user-${Date.now()}`,
        role: "user" as const,
        content: question,
        timestamp: Date.now(),
      };
      addMessage(userMsg);
      queryingRef.current = true;
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
            workflow_result: null,
          },
          timestamp: Date.now(),
        });
      } finally {
        queryingRef.current = false;
        setIsQuerying(false);
      }
    },
    [
      conversationId,
      datasourceId,
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
