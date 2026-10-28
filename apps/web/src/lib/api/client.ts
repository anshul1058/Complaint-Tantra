import {
  Case,
  CaseAction,
  CaseLink,
  DashboardSummary,
  BureauWorkload,
  RegionHeatmapData,
  Institution,
  InstitutionRisk,
  WebFinding,
  Alert,
  OverlapDecision,
} from '@/lib/types';
import {
  mockDashboardSummary,
  mockBureauWorkload,
  mockRegionHeatmap,
  mockCases,
  mockCaseLinks,
  mockCaseActions,
  mockInstitutions,
  mockInstitutionRisks,
  mockWebFindings,
  mockAlerts,
} from '@/lib/mock/data';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('complaint_tantra_jwt');
        localStorage.removeItem('complaint_tantra_user');
        window.location.href = '/login';
      }
      throw new Error('Unauthorized');
    }

    if (!res.ok) {
      throw new Error(`API Error: ${res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    // Graceful fallback for mock mode if backend is not running
    // console.warn(`Fallback to mock for ${endpoint}:`, err);
    throw err;
  }
}

// ----------------- Typed API endpoints -----------------

export async function getDashboardSummary(): Promise<DashboardSummary> {
  try {
    return await request<DashboardSummary>('/dashboard/summary');
  } catch {
    return mockDashboardSummary;
  }
}

export async function getBureauWorkload(): Promise<BureauWorkload[]> {
  try {
    return await request<BureauWorkload[]>('/dashboard/workload');
  } catch {
    return mockBureauWorkload;
  }
}

export async function getRegionHeatmap(): Promise<RegionHeatmapData[]> {
  try {
    return await request<RegionHeatmapData[]>('/dashboard/heatmap');
  } catch {
    return mockRegionHeatmap;
  }
}

export async function getPriorityQueue(): Promise<Case[]> {
  try {
    return await request<Case[]>('/queue/priority');
  } catch {
    return [...mockCases].sort((a, b) => b.priority_score - a.priority_score);
  }
}

export async function getCases(filters?: {
  bureau?: string;
  status?: string;
  category?: string;
  search?: string;
}): Promise<Case[]> {
  try {
    const params = new URLSearchParams();
    if (filters?.bureau) params.set('bureau', filters.bureau);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.category) params.set('category', filters.category);
    if (filters?.search) params.set('search', filters.search);
    return await request<Case[]>(`/cases?${params.toString()}`);
  } catch {
    let result = [...mockCases];
    if (filters?.bureau && filters.bureau !== 'ALL') {
      result = result.filter((c) => c.assigned_bureau === filters.bureau);
    }
    if (filters?.status && filters.status !== 'ALL') {
      result = result.filter((c) => c.status === filters.status);
    }
    if (filters?.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (c) =>
          c.case_no.toLowerCase().includes(q) ||
          c.raw_institution.toLowerCase().includes(q) ||
          c.category.toLowerCase().includes(q) ||
          c.text_original.toLowerCase().includes(q)
      );
    }
    return result;
  }
}

export async function getCase(id: string): Promise<Case | undefined> {
  try {
    return await request<Case>(`/cases/${id}`);
  } catch {
    return mockCases.find((c) => c.id === id) || mockCases[0];
  }
}

export async function getCaseActions(caseId: string): Promise<CaseAction[]> {
  try {
    return await request<CaseAction[]>(`/cases/${caseId}/actions`);
  } catch {
    return mockCaseActions.filter((a) => a.case_id === caseId || a.case_id === 'case-001');
  }
}

export async function getCaseOverlaps(caseId: string): Promise<CaseLink[]> {
  try {
    return await request<CaseLink[]>(`/cases/${caseId}/overlaps`);
  } catch {
    return mockCaseLinks.filter((l) => l.case_a === caseId || l.case_b === caseId || l.case_a === 'case-001');
  }
}

export async function getAllOverlaps(): Promise<CaseLink[]> {
  try {
    return await request<CaseLink[]>('/overlaps');
  } catch {
    return mockCaseLinks;
  }
}

export async function postOverlapDecision(
  linkId: string,
  decision: OverlapDecision
): Promise<{ success: boolean }> {
  try {
    return await request<{ success: boolean }>(`/overlaps/${linkId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    });
  } catch {
    const link = mockCaseLinks.find((l) => l.id === linkId);
    if (link) {
      link.decision = decision;
    }
    return { success: true };
  }
}

export async function postCaseAction(
  caseId: string,
  payload: { action: string; remarks: string; to_state?: string }
): Promise<CaseAction> {
  try {
    return await request<CaseAction>(`/cases/${caseId}/actions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  } catch {
    const newAction: CaseAction = {
      id: Date.now(),
      case_id: caseId,
      actor_name: 'Current Officer',
      actor_type: 'user',
      action: payload.action as CaseAction['action'],
      to_state: payload.to_state,
      remarks: payload.remarks,
      created_at: new Date().toISOString(),
    };
    mockCaseActions.unshift(newAction);
    return newAction;
  }
}

export async function getInstitution(id: string): Promise<Institution | undefined> {
  try {
    return await request<Institution>(`/institutions/${id}`);
  } catch {
    return mockInstitutions.find((i) => i.id === id) || mockInstitutions[0];
  }
}

export async function getInstitutionRisk(id: string): Promise<InstitutionRisk | undefined> {
  try {
    return await request<InstitutionRisk>(`/institutions/${id}/risk`);
  } catch {
    return mockInstitutionRisks[id] || mockInstitutionRisks['inst-001'];
  }
}

export async function getInstitutionIntel(id: string): Promise<WebFinding[]> {
  try {
    return await request<WebFinding[]>(`/institutions/${id}/intel`);
  } catch {
    return mockWebFindings.filter((w) => w.institution_id === id || w.institution_id === 'inst-001');
  }
}

export async function getAlerts(): Promise<Alert[]> {
  try {
    return await request<Alert[]>('/alerts');
  } catch {
    return mockAlerts;
  }
}
