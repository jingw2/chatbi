import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  MessageSquare,
  Zap,
  Database,
  Table,
  BookOpen,
  Users,
  ScrollText,
  Settings,
  SlidersHorizontal,
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
  { icon: SlidersHorizontal, label: "Models", href: "/admin/model-settings" },
  { icon: Users, label: "Users", href: "/admin/users" },
  { icon: ScrollText, label: "Audit", href: "/admin/audit" },
];

export default function Sidebar() {
  const location = useLocation();
  const qc = useQueryClient();
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
    try {
      await api.delete(`/api/v1/conversations/${convId}`);
      qc.invalidateQueries({ queryKey: ["conversations"] });
      if (conversationId === convId) reset();
    } catch {
      // Silently ignore — conversation stays visible on failure
    }
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
