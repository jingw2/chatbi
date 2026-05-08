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
      </div>
    </div>
  );
}
