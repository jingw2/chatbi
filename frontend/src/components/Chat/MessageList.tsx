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
