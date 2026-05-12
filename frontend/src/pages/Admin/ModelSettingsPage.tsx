import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { CheckCircle2, KeyRound, RotateCcw, Save, TestTube2, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type ModelRole = "intent" | "text_to_sql" | "base";
type ModelProvider =
  | "openai"
  | "anthropic"
  | "deepseek"
  | "qwen"
  | "kimi"
  | "glm"
  | "minimax"
  | "gemini"
  | "openai_compatible";

interface ModelSetting {
  role: ModelRole;
  provider: ModelProvider;
  model_name: string;
  base_url: string | null;
  has_api_key: boolean;
  source: "env" | "database";
  updated_at: string | null;
}

interface ModelForm {
  provider: ModelProvider;
  model_name: string;
  base_url: string;
  api_key: string;
}

const roleLabels: Record<ModelRole, { title: string; detail: string }> = {
  intent: {
    title: "Intent Model",
    detail: "Classifies user questions before SQL generation.",
  },
  text_to_sql: {
    title: "Text-to-SQL Model",
    detail: "Generates SQL from the selected datasource schema.",
  },
  base: {
    title: "Insight Model",
    detail: "Writes summaries and follow-up analysis.",
  },
};

const providerLabels: Record<ModelProvider, string> = {
  openai:            "OpenAI",
  anthropic:         "Anthropic (Claude)",
  deepseek:          "DeepSeek",
  qwen:              "Qwen (Alibaba)",
  kimi:              "Kimi (Moonshot)",
  glm:               "GLM (Zhipu)",
  minimax:           "MiniMax / MiMo",
  gemini:            "Gemini (Google)",
  openai_compatible: "OpenAI Compatible / vLLM",
};

const PROVIDER_DEFAULT_BASE_URLS: Partial<Record<ModelProvider, string>> = {
  deepseek: "https://api.deepseek.com/v1",
  qwen:     "https://dashscope.aliyuncs.com/compatible-mode/v1",
  kimi:     "https://api.moonshot.cn/v1",
  glm:      "https://open.bigmodel.cn/api/paas/v4",
  minimax:  "https://api.minimax.chat/v1",
  gemini:   "https://generativelanguage.googleapis.com/v1beta/openai/",
};

const PROVIDER_MODEL_PLACEHOLDER: Partial<Record<ModelProvider, string>> = {
  openai:            "gpt-4o-mini",
  anthropic:         "claude-sonnet-4-6",
  deepseek:          "deepseek-chat",
  qwen:              "qwen-plus",
  kimi:              "moonshot-v1-8k",
  glm:               "glm-4-flash",
  minimax:           "MiniMax-Text-01",
  gemini:            "gemini-1.5-flash",
  openai_compatible: "your-model-name",
};

function toForm(setting: ModelSetting): ModelForm {
  return {
    provider: setting.provider,
    model_name: setting.model_name,
    base_url: setting.base_url ?? "",
    api_key: "",
  };
}

function normalizePayload(form: ModelForm) {
  return {
    provider: form.provider,
    model_name: form.model_name.trim(),
    base_url: form.base_url.trim() || null,
    ...(form.api_key ? { api_key: form.api_key } : {}),
  };
}

export default function ModelSettingsPage() {
  const qc = useQueryClient();
  const [forms, setForms] = useState<Partial<Record<ModelRole, ModelForm>>>({});
  const [results, setResults] = useState<Record<ModelRole, { ok: boolean; message: string } | undefined>>({
    intent: undefined,
    text_to_sql: undefined,
    base: undefined,
  });

  const { data: settings, isLoading } = useQuery<ModelSetting[]>({
    queryKey: ["model-settings"],
    queryFn: async () => (await api.get("/api/v1/model-settings")).data,
  });

  const settingsByRole = useMemo(() => {
    return new Map((settings ?? []).map((setting) => [setting.role, setting]));
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: ({ role, form }: { role: ModelRole; form: ModelForm }) =>
      api.put(`/api/v1/model-settings/${role}`, normalizePayload(form)),
    onSuccess: (_, { role }) => {
      setForms((current) => ({
        ...current,
        [role]: { ...current[role]!, api_key: "" },
      }));
      qc.invalidateQueries({ queryKey: ["model-settings"] });
      setResults((current) => ({
        ...current,
        [role]: { ok: true, message: "Saved" },
      }));
    },
    onError: (error: AxiosError<{ detail?: string }>, { role }) => {
      setResults((current) => ({
        ...current,
        [role]: {
          ok: false,
          message: error.response?.data?.detail ?? "Save failed",
        },
      }));
    },
  });

  const testMutation = useMutation({
    mutationFn: ({ role, form }: { role: ModelRole; form: ModelForm }) =>
      api.post("/api/v1/model-settings/test", normalizePayload(form)).then((res) => ({
        role,
        data: res.data as { ok: boolean; message: string },
      })),
    onSuccess: ({ role, data }) => {
      setResults((current) => ({
        ...current,
        [role]: { ok: data.ok, message: data.message },
      }));
    },
    onError: (error: AxiosError<{ detail?: string }>, { role }) => {
      setResults((current) => ({
        ...current,
        [role]: {
          ok: false,
          message: error.response?.data?.detail ?? "Connection test failed",
        },
      }));
    },
  });

  const updateForm = (role: ModelRole, patch: Partial<ModelForm>) => {
    const setting = settingsByRole.get(role);
    if (!setting) return;
    const current = forms[role] ?? toForm(setting);
    const next = { ...current, ...patch };
    // Auto-fill base URL when provider changes (only if user hasn't typed a custom one)
    if (patch.provider && patch.provider !== current.provider) {
      next.base_url = PROVIDER_DEFAULT_BASE_URLS[patch.provider] ?? "";
    }
    setForms((prev) => ({ ...prev, [role]: next }));
    setResults((prev) => ({ ...prev, [role]: undefined }));
  };

  const resetForm = (role: ModelRole) => {
    const setting = settingsByRole.get(role);
    if (!setting) return;
    setForms((current) => ({ ...current, [role]: toForm(setting) }));
    setResults((current) => ({ ...current, [role]: undefined }));
  };

  return (
    <div className="p-6 space-y-5 max-w-6xl">
      <div>
        <h1 className="text-xl font-semibold">Model Settings</h1>
        <p className="text-sm text-gray-500 mt-1">
          Configure hosted APIs or local OpenAI-compatible endpoints.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : (
        <div className="space-y-4">
          {(["intent", "text_to_sql", "base"] as ModelRole[]).map((role) => {
            const setting = settingsByRole.get(role);
            if (!setting) return null;
            const form = forms[role] ?? toForm(setting);
            const result = results[role];

            const isSaving = saveMutation.isPending && saveMutation.variables?.role === role;
            const isTesting = testMutation.isPending && testMutation.variables?.role === role;

            return (
              <section key={role} className="rounded-md border bg-white p-4 space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-medium">{roleLabels[role].title}</h2>
                      <Badge variant={setting.source === "database" ? "default" : "secondary"}>
                        {setting.source === "database" ? "Configured" : "ENV"}
                      </Badge>
                      {setting.has_api_key && (
                        <Badge variant="outline" className="gap-1">
                          <KeyRound size={12} />
                          Key saved
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{roleLabels[role].detail}</p>
                  </div>
                  {setting.updated_at && (
                    <span className="text-xs text-gray-400">
                      Updated {new Date(setting.updated_at).toLocaleString()}
                    </span>
                  )}
                </div>

                <div className="grid gap-3 lg:grid-cols-[220px_minmax(180px,1fr)_minmax(220px,1.4fr)_minmax(180px,1fr)]">
                  <div className="space-y-1">
                    <Label>Provider</Label>
                    <Select
                      value={form.provider}
                      onValueChange={(value) => updateForm(role, { provider: value as ModelProvider })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(Object.keys(providerLabels) as ModelProvider[]).map((p) => (
                          <SelectItem key={p} value={p}>{providerLabels[p]}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-1">
                    <Label>Model</Label>
                    <Input
                      value={form.model_name}
                      onChange={(event) => updateForm(role, { model_name: event.target.value })}
                      placeholder={PROVIDER_MODEL_PLACEHOLDER[form.provider] ?? "model-name"}
                    />
                  </div>

                  <div className="space-y-1">
                    <Label>Base URL</Label>
                    <Input
                      value={form.base_url}
                      onChange={(event) => updateForm(role, { base_url: event.target.value })}
                      placeholder="http://127.0.0.1:8001/v1"
                    />
                  </div>

                  <div className="space-y-1">
                    <Label>API Key</Label>
                    <Input
                      type="password"
                      value={form.api_key}
                      onChange={(event) => updateForm(role, { api_key: event.target.value })}
                      placeholder={setting.has_api_key ? "Keep existing" : "sk-..."}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-h-5 text-sm">
                    {result && (
                      <span
                        className={
                          result.ok
                            ? "inline-flex items-center gap-1 text-green-700"
                            : "inline-flex items-center gap-1 text-red-600"
                        }
                      >
                        {result.ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
                        {result.message}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button type="button" variant="ghost" size="sm" onClick={() => resetForm(role)}>
                      <RotateCcw size={15} />
                      Reset
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={!form.model_name.trim() || isTesting}
                      onClick={() => testMutation.mutate({ role, form })}
                    >
                      <TestTube2 size={15} />
                      {isTesting ? "Testing..." : "Test"}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      disabled={!form.model_name.trim() || isSaving}
                      onClick={() => saveMutation.mutate({ role, form })}
                    >
                      <Save size={15} />
                      {isSaving ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
