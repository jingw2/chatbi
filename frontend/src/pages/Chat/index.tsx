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
