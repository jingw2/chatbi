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
import ModelSettingsPage from "@/pages/Admin/ModelSettingsPage";

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
            <Route
              path="admin/model-settings"
              element={<AdminRoute><ModelSettingsPage /></AdminRoute>}
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
