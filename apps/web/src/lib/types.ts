export type UserRole = 'officer' | 'regional' | 'senior' | 'authority' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  bureau: string;
  region: string;
  active: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export type CaseStatus =
  | 'Received'
  | 'Under Process'
  | 'UnderProcess'
  | 'Transferred'
  | 'Escalated'
  | 'Disposed'
  | 'Reopened';

export type CriticalityCode = 'C1' | 'C2' | 'C3' | 'C4';

export type EmotionLabel =
  | 'distress'
  | 'fear'
  | 'anger'
  | 'frustration'
  | 'hopelessness'
  | 'neutral'
  | 'hopeful';

export interface PriorityComponents {
  criticality: number;
  emotion: number;
  time: number;
  risk: number;
  overlap: number;
}

export interface PriorityReasons {
  priority_score: number;
  components: PriorityComponents;
  reasons: string[];
}

export interface Case {
  id: string;
  case_no: string;
  institution_id: string;
  raw_institution: string;
  institution_name?: string;
  institution_city?: string;
  institution_state?: string;
  source_bureau: string;
  assigned_bureau: string;
  assigned_officer?: string;
  assigned_officer_name?: string;
  complainant_type: 'student' | 'faculty' | 'parent' | 'other' | 'suo-motu';
  category: string;
  subcategory?: string;
  text_original: string;
  text_english: string;
  language: string;
  status: CaseStatus;
  received_at: string;
  expected_disposal: string;
  last_action_at?: string;
  next_action?: string;
  criticality: CriticalityCode;
  criticality_reason?: string;
  emotion_label: EmotionLabel;
  emotion_intensity: number; // 0..1
  safety_flag: boolean;
  safety_flag_reason?: string;
  priority_score: number; // 0..100
  priority_reasons: PriorityReasons;
  ai_summary: string;
  ai_version?: string;
  overlap_count?: number;
}

export interface CaseAction {
  id: string | number;
  case_id: string;
  actor_id?: string;
  actor_name?: string;
  actor_type: 'user' | 'system' | 'agent';
  action:
    | 'created'
    | 'assigned'
    | 'transferred'
    | 'escalated'
    | 'remark'
    | 'status_change'
    | 'doc_added'
    | 'linked'
    | 'reopened'
    | 'disposed';
  from_state?: string;
  to_state?: string;
  remarks: string;
  payload?: Record<string, unknown>;
  created_at: string;
}

export type OverlapTier = 'T1' | 'T2' | 'T3';
export type OverlapDecision = 'pending' | 'confirmed' | 'rejected';

export interface CaseLinkEvidence {
  id_match?: boolean;
  name_score?: number;
  address_score?: number;
  text_sim?: number;
  category_relatedness?: number;
  time_overlap?: boolean;
  reasoning: string;
}

export interface CaseLink {
  id: string;
  case_a: string;
  case_b: string;
  case_a_details?: Case;
  case_b_details?: Case;
  tier: OverlapTier;
  confidence: number; // 0..1
  evidence: CaseLinkEvidence;
  detected_by: 'agent' | 'officer';
  decision: OverlapDecision;
  decided_by?: string;
  decided_at?: string;
}

export interface Institution {
  id: string;
  permanent_id?: string;
  name: string;
  name_normalized: string;
  address?: string;
  city: string;
  state: string;
  region: string;
  trust_or_society?: string;
  created_at: string;
}

export interface InstitutionRisk {
  institution_id: string;
  complaint_load: number;
  repeat_offender: number;
  web_reputation: number;
  overlap_density: number;
  risk_index: number; // 0..100
  computed_at: string;
}

export interface WebFinding {
  id: string;
  institution_id: string;
  url: string;
  title: string;
  source_name: string;
  published_at: string;
  retrieved_at: string;
  summary: string;
  topic: 'fees' | 'safety' | 'accreditation' | 'faculty' | 'fraud' | 'placement' | 'court' | 'other';
  sentiment: 'negative' | 'neutral' | 'positive';
  emotion_label?: string;
  severity: number; // 0..1
  match_confidence: number; // 0..1
}

export interface Alert {
  id: string;
  kind: 'overlap' | 'due_soon' | 'overdue' | 'stuck' | 'escalation' | 'safety' | 'reputation';
  case_id?: string;
  case_no?: string;
  institution_id?: string;
  institution_name?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  target_role?: string;
  target_user?: string;
  created_at: string;
  acknowledged_at?: string;
}

export interface DashboardSummary {
  total: number;
  pending: number;
  under_process: number;
  disposed: number;
  transferred: number;
  overdue: number;
  escalated: number;
  safety_flagged: number;
}

export interface BureauWorkload {
  bureau: string;
  pending: number;
  under_process: number;
  disposed: number;
  overdue: number;
  total: number;
}

export interface RegionHeatmapData {
  region: string;
  state: string;
  count: number;
  overdue: number;
  critical: number;
}
