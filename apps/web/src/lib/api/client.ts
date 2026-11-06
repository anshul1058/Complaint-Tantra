import {
  Alert,
  Case,
  CaseAction,
  CaseLink,
  BureauWorkload,
  Institution,
  InstitutionRisk,
  WebFinding,
  OverlapDecision,
  PriorityReasons,
} from '@/lib/types';
import type { components } from './schema';

type DashboardSummaryApi = components['schemas']['DashboardSummaryOut'];
type HeatmapRowApi = components['schemas']['HeatmapRow'];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const EMPTY_PRIORITY_COMPONENTS = { criticality: 0, emotion: 0, time: 0, risk: 0, overlap: 0 };

function normalizeCase(c: Case): Case {
  const score = c.priority_score ?? 0;
  const reasons: PriorityReasons = c.priority_reasons
    ? {
        priority_score: c.priority_reasons.priority_score ?? score,
        components: { ...EMPTY_PRIORITY_COMPONENTS, ...c.priority_reasons.components },
        reasons: Array.isArray(c.priority_reasons.reasons) ? c.priority_reasons.reasons : [],
      }
    : { priority_score: score, components: EMPTY_PRIORITY_COMPONENTS, reasons: [] };
  return {
    ...c,
    priority_score: score,
    emotion_intensity: c.emotion_intensity ?? 0,
    priority_reasons: reasons,
  };
}

export interface PublicComplaintPayload {
  complainant_name: string;
  complainant_email: string;
  complainant_phone?: string;
  complainant_type: string;
  college_name: string;
  college_permanent_id?: string;
  college_affiliation?: string;
  college_address?: string;
  college_city?: string;
  college_state?: string;
  college_pincode?: string;
  category: string;
  subcategory?: string;
  subject: string;
  description: string;
  incident_date?: string;
  relief_sought?: string;
  language: string;
  supporting_details?: string;
}

export interface PublicComplaintResult {
  case_id: string;
  case_no: string;
  status: string;
  assigned_bureau: string;
  message: string;
}

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('complaint_tantra_jwt');
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) throw new Error('Unauthorized');
  if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`);
  if (res.status === 204) return undefined as T;
  return await res.json();
}

export function registerPublicComplaint(
  payload: PublicComplaintPayload
): Promise<PublicComplaintResult> {
  return request<PublicComplaintResult>('/public/complaints', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getDashboardSummary(): Promise<DashboardSummaryApi> {
  return request<DashboardSummaryApi>('/dashboard/summary');
}

export async function getBureauWorkload(): Promise<BureauWorkload[]> {
  return request<BureauWorkload[]>('/dashboard/workload');
}

export async function getRegionHeatmap(): Promise<HeatmapRowApi[]> {
  return request<HeatmapRowApi[]>('/dashboard/heatmap');
}

export async function getPriorityQueue(): Promise<Case[]> {
  const cases = await request<Case[]>('/cases?sort=priority&limit=50');
  return cases.map(normalizeCase);
}

export async function getCases(filters?: {
  bureau?: string;
  status?: string;
  category?: string;
  search?: string;
  permanent_id?: string;
  institution?: string;
}): Promise<Case[]> {
  const params = new URLSearchParams();
  if (filters?.bureau) params.set('bureau', filters.bureau);
  if (filters?.status) params.set('status', filters.status);
  if (filters?.category) params.set('category', filters.category);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.permanent_id) params.set('permanent_id', filters.permanent_id);
  if (filters?.institution) params.set('institution', filters.institution);
  const cases = await request<Case[]>(`/cases?${params.toString()}`);
  return cases.map(normalizeCase);
}

export async function getCase(id: string): Promise<Case> {
  return normalizeCase(await request<Case>(`/cases/${id}`));
}

export async function getCaseActions(caseId: string): Promise<CaseAction[]> {
  return request<CaseAction[]>(`/cases/${caseId}/actions`);
}

export async function getCaseOverlaps(caseId: string): Promise<CaseLink[]> {
  return request<CaseLink[]>(`/cases/${caseId}/overlaps`);
}

export async function getAllOverlaps(): Promise<CaseLink[]> {
  return request<CaseLink[]>('/overlaps');
}

export async function postOverlapDecision(
  linkId: string,
  decision: OverlapDecision
): Promise<{ success: boolean }> {
  return request<{ success: boolean }>(`/overlaps/${linkId}/decision`, {
    method: 'POST',
    body: JSON.stringify({ decision }),
  });
}

export async function postCaseAction(
  caseId: string,
  payload: { action: string; remarks: string; to_state?: string }
): Promise<Case> {
  return normalizeCase(
    await request<Case>(`/cases/${caseId}/actions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  );
}

export async function getInstitution(id: string): Promise<Institution> {
  return request<Institution>(`/institutions/${id}`);
}

export async function getInstitutionRisk(id: string): Promise<InstitutionRisk> {
  return request<InstitutionRisk>(`/institutions/${id}/risk`);
}

export async function getInstitutionIntel(id: string): Promise<WebFinding[]> {
  return request<WebFinding[]>(`/institutions/${id}/intel`);
}

export async function refreshInstitutionIntel(id: string): Promise<{ findings_created: number; detail?: string }> {
  return request(`/institutions/${id}/intel/refresh?force=true`, { method: 'POST' });
}

export async function dismissInstitutionFinding(institutionId: string, findingId: string): Promise<void> {
  await request(`/institutions/${institutionId}/intel/${findingId}/dismiss`, { method: 'POST' });
}

export async function getAlerts(): Promise<Alert[]> {
  return request<Alert[]>('/alerts');
}

export async function acknowledgeAlert(id: string): Promise<Alert> {
  return request<Alert>(`/alerts/${id}/acknowledge`, { method: 'POST' });
}

export async function snoozeAlert(id: string, hours = 24): Promise<Alert> {
  return request<Alert>(`/alerts/${id}/snooze`, {
    method: 'POST',
    body: JSON.stringify({ hours }),
  });
}

export async function getDigest(): Promise<Record<string, unknown>> {
  return request('/alerts/digest');
}

export type ReportType =
  | 'bureau'
  | 'institution'
  | 'region'
  | 'ageing'
  | 'disposal'
  | 'status'
  | 'duplicates'
  | 'performance'
  | 'monthly';

export async function getReport(type: ReportType): Promise<Record<string, unknown>[]> {
  return request<Record<string, unknown>[]>(`/reports/${type}`);
}

export async function downloadReport(type: ReportType, format: 'csv' | 'pdf'): Promise<void> {
  const token = getStoredToken();
  const res = await fetch(`${API_BASE}/reports/${type}?format=${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${type}.${format}`;
  link.click();
  URL.revokeObjectURL(url);
}

export function eventsUrl(token: string): string {
  return `${API_BASE.replace(/^http/, 'ws')}/ws/events?token=${encodeURIComponent(token)}`;
}
