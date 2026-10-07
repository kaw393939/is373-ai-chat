export type Role = "user" | "admin";
export type User = {
  id: string;
  email: string;
  role: Role;
  active: boolean;
  approved: boolean;
  email_verified: boolean;
  daily_requests: number | null;
  daily_units: number | null;
  max_concurrent: number | null;
};
export type Chat = { id: string; title: string };
export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};
export type GenerationStatus =
  | "streaming"
  | "complete"
  | "failed"
  | "cancelled"
  | "interrupted"
  | "incomplete"
  | "refused";
export type TerminalStatus = Exclude<GenerationStatus, "streaming">;
export type Run = {
  id: string;
  status: GenerationStatus;
  tokens: number | null;
};
export type Page<T> = { items: T[]; next_cursor: string | null };
export type Conversation = Chat & {
  messages: Message[];
  runs: Run[];
  messages_cursor: string | null;
  runs_cursor: string | null;
};
export type Model = {
  id: string;
  name: string;
  provider: string;
  enabled: boolean;
};
export type Budget = {
  role: Role;
  daily_requests: number;
  daily_units: number;
  max_concurrent: number;
  max_output: number;
  model_enabled: boolean;
};
export type HostSample = {
  at: number;
  cpu_percent: number;
  memory_used: number;
  memory_total: number;
  disk_used: number;
  disk_total: number;
  containers: { name: string; cpu: string; memory: string; status: string }[];
};
export type Overview = {
  totals: Record<string, number>;
  host: {
    samples?: HostSample[];
    backups?: {
      local: { status: "ok" | "stale" | "missing"; created_at: number | null };
      off_host: {
        status: "ok" | "stale" | "missing";
        created_at: number | null;
        received_at: number | null;
      };
    };
  } | null;
  audit: { action: string; at: number }[];
};
export type AuthOptions = {
  email_enabled: boolean;
  approval_required: boolean;
};
export type SignedIn = {
  access_token: string;
  user: User;
  recovery_codes?: string[];
};
export type MfaChallenge = {
  mfa_required: true;
  challenge: string;
  enrollment_required: boolean;
};
export type LoginResult = SignedIn | MfaChallenge;
export type MfaEnrollment = { secret: string; otpauth_url: string };
export type OwnedExportPage = {
  account: User;
  format: "firehose360-owned-v1";
  section: "conversations" | "messages" | "runs";
  items: Record<string, unknown>[];
  next_cursor: string | null;
};
export type StreamEvent =
  | { kind: "started"; run_id: string }
  | { kind: "delta"; text: string }
  | { kind: "error"; message: string }
  | { kind: "completed"; status: TerminalStatus; tokens: number | null };
