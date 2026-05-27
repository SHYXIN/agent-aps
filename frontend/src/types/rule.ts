export interface Rule {
  id: number;
  name: string;
  description: string | null;
  rule_type: "data_cleaning" | "scheduling";
  condition_json: string;
  action_json: string;
  free_text: string | null;
  status: "active" | "disabled";
  source: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface RuleCreate {
  name: string;
  description?: string;
  rule_type: "data_cleaning" | "scheduling";
  condition: { field: string; operator: string; value: string | number | string[] | null };
  action: { field: string; operator: string; value: string | number | string[] | null };
  free_text?: string;
  notes?: string;
}

export interface ChangelogEntry {
  id: number;
  rule_id: number;
  action: string;
  before_value: Record<string, unknown> | null;
  after_value: Record<string, unknown> | null;
  created_at: string | null;
}

export interface ConflictInfo {
  existing_rule: string;
  reason: string;
}

export interface User {
  user_id: number;
  username: string;
  role: string;
}
