import type { Rule, RuleCreate, ChangelogEntry, ConflictInfo } from "../types/rule";

const API_BASE = "/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export const ruleApi = {
  list: (params?: { rule_type?: string; status?: string }) => {
    const search = new URLSearchParams();
    if (params?.rule_type) search.set("rule_type", params.rule_type);
    if (params?.status) search.set("status", params.status);
    const qs = search.toString();
    return fetchJson<Rule[]>(`/rules${qs ? `?${qs}` : ""}`);
  },

  get: (id: number) => fetchJson<Rule>(`/rules/${id}`),

  create: (rule: RuleCreate) =>
    fetchJson<Rule | { status: string; conflicts: ConflictInfo[] }>("/rules", {
      method: "POST",
      body: JSON.stringify(rule),
    }),

  forceCreate: (rule: RuleCreate) =>
    fetchJson<Rule>("/rules/force", {
      method: "POST",
      body: JSON.stringify(rule),
    }),

  update: (id: number, data: Record<string, unknown>) =>
    fetchJson<Rule>(`/rules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    fetchJson<{ ok: boolean }>(`/rules/${id}`, { method: "DELETE" }),

  conflictCheck: (rule: RuleCreate) =>
    fetchJson<{ has_conflict: boolean; conflicts: ConflictInfo[] }>(
      "/rules/conflict-check",
      { method: "POST", body: JSON.stringify(rule) }
    ),

  getChangelog: (id: number) =>
    fetchJson<ChangelogEntry[]>(`/rules/${id}/changelog`),

  getAllChangelog: () =>
    fetchJson<ChangelogEntry[]>("/changelog"),
};
