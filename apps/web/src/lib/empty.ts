import { Case, Institution, InstitutionRisk, User } from '@/lib/types';

export const emptyUser: User = {
  id: '', name: '', email: '', role: 'officer', bureau: '', region: '', active: false,
};

export const emptyCase: Case = {
  id: '', case_no: '—', institution_id: '', raw_institution: '—',
  source_bureau: '', assigned_bureau: '', complainant_type: 'other',
  category: '—', text_original: '', text_english: '', language: '',
  status: 'Received', received_at: new Date(0).toISOString(),
  expected_disposal: new Date(0).toISOString(), criticality: 'C4',
  emotion_label: 'neutral', emotion_intensity: 0, safety_flag: false,
  priority_score: 0,
  priority_reasons: {
    priority_score: 0,
    components: { criticality: 0, emotion: 0, time: 0, risk: 0, overlap: 0 },
    reasons: [],
  },
  ai_summary: '',
};

export const emptyInstitution: Institution = {
  id: '', name: '—', name_normalized: '', city: '', state: '', region: '',
  created_at: new Date(0).toISOString(),
};

export const emptyRisk: InstitutionRisk = {
  institution_id: '', complaint_load: 0, repeat_offender: 0, web_reputation: 0,
  overlap_density: 0, risk_index: 0, computed_at: new Date(0).toISOString(),
};
