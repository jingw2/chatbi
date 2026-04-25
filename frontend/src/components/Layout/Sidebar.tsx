import {
  MessageSquare,
  Zap,
  Database,
  Table,
  BookOpen,
  Users,
  ScrollText,
  Settings,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

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

  return (
    <aside className="w-64 h-screen flex flex-col border-r bg-white shrink-0">
      {/* New Chat */}
      <div className="p-3 border-b">
        <Link
          to="/"
          className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-100 text-sm font-medium"
        >
          <MessageSquare size={16} />
          New Chat
        </Link>
      </div>

      {/* History placeholder */}
      <div className="flex-1 overflow-y-auto p-3">
        <p className="text-xs font-medium text-gray-400 px-3 py-2 uppercase tracking-wider">
          History
        </p>
        {/* Populated in Plan 8 */}
      </div>

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
