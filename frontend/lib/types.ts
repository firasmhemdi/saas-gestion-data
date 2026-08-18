export type Role = "admin" | "responsable_environnement" | "consultant" | "lecture_seule";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  email_verified: boolean;
  email_verified_at: string | null;
  otp_enabled: boolean;
  company_id: number;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface OtpChallenge {
  requires_otp: boolean;
  otp_token: string;
  delivery_hint?: string;
}

export interface EmailVerificationChallenge {
  requires_email_verification: boolean;
  verification_token: string;
  delivery_hint?: string;
  email: string;
}

export type LoginResult = TokenResponse | OtpChallenge | EmailVerificationChallenge;
export type RegisterResult = TokenResponse | EmailVerificationChallenge;

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
  company_name: string;
}

export interface UserCreatePayload {
  email: string;
  full_name: string;
  password: string;
  role: Role;
}

export interface UserUpdatePayload {
  full_name?: string;
  role?: Role;
  password?: string;
}

export type AuditAction =
  | "register"
  | "login"
  | "login_failed"
  | "logout"
  | "refresh"
  | "password_change"
  | "user_role_change"
  | "otp_sent"
  | "otp_verify_failed"
  | "otp_enabled"
  | "otp_disabled"
  | "site_created"
  | "site_updated"
  | "site_deleted"
  | "data_source_created"
  | "data_source_updated"
  | "data_source_deleted"
  | "indicator_created"
  | "data_created"
  | "data_updated"
  | "data_validated"
  | "import_previewed"
  | "import_committed"
  | "mapping_saved"
  | "sync_scheduled"
  | "sync_run"
  | "document_extracted"
  | "document_validated";

export interface AuditLog {
  id: number;
  action: AuditAction;
  user_id: number | null;
  company_id: number | null;
  ip_address: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export type SourceType = "excel" | "api" | "sql" | "erp" | "iot";
export type IndicatorCategory = "energie" | "eau" | "dechets" | "emissions" | "matieres";
export type DataEntrySource = "manuel" | "excel" | "api" | "sql" | "erp" | "iot";
export type DataEntryStatus = "brouillon" | "valide";

export interface Site {
  id: number;
  company_id: number;
  name: string;
  code: string | null;
  location: string | null;
  created_at: string;
}

export interface SitePayload {
  name: string;
  code?: string;
  location?: string;
}

export interface DataSource {
  id: number;
  company_id: number;
  site_id: number | null;
  name: string;
  source_type: SourceType;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataSourcePayload {
  name: string;
  source_type: SourceType;
  site_id?: number | null;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export interface Indicator {
  id: number;
  company_id: number;
  code: string;
  name: string;
  unit: string;
  category: IndicatorCategory;
  description: string | null;
  created_at: string;
}

export interface IndicatorPayload {
  code: string;
  name: string;
  unit: string;
  category: IndicatorCategory;
  description?: string;
}

export interface Emission {
  id: number;
  company_id: number;
  code: string;
  name: string;
  scope: "1" | "2" | "3";
  source: string | null;
  factor: number;
  unit: string;
  year: number;
  created_at: string;
}

export interface EmissionPayload {
  code: string;
  name: string;
  scope: "1" | "2" | "3";
  source?: string;
  factor: number;
  unit: string;
  year: number;
}

export interface EnvironmentalData {
  id: number;
  company_id: number;
  site_id: number | null;
  indicator_id: number | null;
  entry_date: string;
  value: number;
  unit: string;
  source: DataEntrySource;
  status: DataEntryStatus;
  entered_by: number | null;
  created_at: string;
}

export interface EnvironmentalDataPayload {
  site_id?: number | null;
  indicator_id?: number | null;
  entry_date: string;
  value: number;
  unit: string;
  source?: DataEntrySource;
}

export type ImportStatus = "preview" | "pending" | "running" | "success" | "failed";
export type SyncStatus = "idle" | "success" | "failed";
export type DocumentStatus = "uploaded" | "extracted" | "validated" | "rejected";
export type DocumentType = "facture_energie" | "bordereau_dechets" | "contrat" | "attestation" | "autre";

export interface ImportJob {
  id: number;
  company_id: number;
  source_id: number | null;
  site_id: number | null;
  filename: string;
  source_type: string;
  status: ImportStatus;
  row_count: number;
  imported_count: number;
  duration_ms: number;
  mapping: Record<string, string> | null;
  preview_rows: Array<Record<string, unknown>>;
  error_message: string | null;
  created_by: number | null;
  created_at: string;
}

export interface DataMapping {
  id: number;
  company_id: number;
  source_id: number | null;
  name: string;
  target_model: string;
  rules: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface SyncSchedule {
  id: number;
  company_id: number;
  source_id: number;
  frequency: string;
  window_start: string | null;
  window_end: string | null;
  is_active: boolean;
  last_status: SyncStatus;
  last_run_at: string | null;
  last_message: string | null;
  created_at: string;
}

export interface ExtractedData {
  id: number;
  company_id: number;
  document_id: number;
  fields: Record<string, unknown>;
  confidence: number;
  created_at: string;
  validated_at: string | null;
  validated_by: number | null;
}

export interface DocumentRecord {
  id: number;
  company_id: number;
  site_id: number | null;
  filename: string;
  document_type: DocumentType;
  status: DocumentStatus;
  raw_text: string;
  extracted_data: ExtractedData | null;
  created_by: number | null;
  created_at: string;
}

export type QualitySeverity = "info" | "warning" | "critical";
export type QualityIssueType = "missing_reference" | "negative_value" | "unit_mismatch" | "duplicate" | "outlier";

export interface QualityAlert {
  id: string;
  data_id: number;
  issue_type: QualityIssueType;
  severity: QualitySeverity;
  title: string;
  message: string;
  recommendation: string;
  entry_date: string;
  site_id: number | null;
  indicator_id: number | null;
}

export interface QualitySummary {
  total_entries: number;
  draft_entries: number;
  valid_entries: number;
  alerts: QualityAlert[];
  quality_score: number;
}

export interface NormalizedEntry {
  data_id: number;
  original_value: number;
  original_unit: string;
  normalized_value: number;
  normalized_unit: string;
  changed: boolean;
}

export interface AnalyticsMetric {
  key: string;
  label: string;
  value: number;
  unit: string;
  trend: number;
}

export interface CategoryTotal {
  category: string;
  label: string;
  value: number;
  unit: string;
}

export interface SitePerformance {
  site_id: number | null;
  site_name: string;
  energy_kwh: number;
  water_m3: number;
  waste_tonnes: number;
  emissions_kgco2e: number;
}

export interface ScopeEmission {
  scope: "1" | "2" | "3";
  value: number;
  unit: string;
}

export interface AnalyticsSummary {
  metrics: AnalyticsMetric[];
  categories: CategoryTotal[];
  site_performance: SitePerformance[];
  emissions_by_scope: ScopeEmission[];
}

export interface AssistantSource {
  type: string;
  data_id?: number;
  site?: string;
  indicator?: string | null;
  period?: string;
}

export interface AssistantAnswer {
  id: number;
  question: string;
  answer: string;
  sources: AssistantSource[];
  created_at: string;
}
