'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { registerPublicComplaint, PublicComplaintPayload } from '@/lib/api/client';
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  FileText,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  UserRound,
} from 'lucide-react';

type Tab = 'login' | 'complaint';

const initialComplaint: PublicComplaintPayload = {
  complainant_name: '', complainant_email: '', complainant_phone: '', complainant_type: 'student',
  college_name: '', college_permanent_id: '', college_affiliation: '', college_address: '',
  college_city: '', college_state: '', college_pincode: '', category: 'Other', subcategory: '',
  subject: '', description: '', incident_date: '', relief_sought: '', language: 'English',
  supporting_details: '',
};

const inputClass = 'w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent font-medium';

function Field({ label, name, value, onChange, required = false, type = 'text' }: {
  label: string; name: keyof PublicComplaintPayload; value: string;
  onChange: (name: keyof PublicComplaintPayload, value: string) => void;
  required?: boolean; type?: string;
}) {
  return (
    <label className="block">
      <span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">
        {label}{required && <span className="text-red-600"> *</span>}
      </span>
      <input type={type} required={required} value={value} onChange={(e) => onChange(name, e.target.value)} className={inputClass} />
    </label>
  );
}

function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('asha@rb.gov.in');
  const [password, setPassword] = useState('demo123');
  const [selectedRoleKey, setSelectedRoleKey] = useState('officer');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setIsLoading(true); setError('');
    const ok = await login(email, selectedRoleKey, password);
    setIsLoading(false);
    if (!ok) { setError('Login failed. Check your credentials or contact the portal administrator.'); return; }
    router.push('/');
  };

  const handleRolePreset = (key: string) => {
    setSelectedRoleKey(key);
    const emails: Record<string, string> = {
      officer: 'asha@rb.gov.in', pgrcOfficer: 'ravi@pgrc.gov.in', regional: 'meera@rb.gov.in',
      senior: 'sharma@hq.gov.in', authority: 'nair@hq.gov.in', admin: 'admin@hq.gov.in',
    };
    if (emails[key]) { setEmail(emails[key]); setPassword('demo123'); }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-4">
      <div><label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Official Email ID</label><div className="relative"><Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" /><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={`${inputClass} pl-9`} /></div></div>
      <div><label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Password</label><div className="relative"><Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" /><input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className={`${inputClass} pl-9`} /></div></div>
      <div className="pt-2 border-t border-slate-200"><label className="block text-[11px] font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-1"><Sparkles className="w-3.5 h-3.5 text-amber-600" /> SIH Evaluator Demo Roles</label><div className="grid grid-cols-2 gap-1.5 text-xs">
        {[['officer', 'RB Officer'], ['pgrcOfficer', 'PGRC Officer'], ['regional', 'Regional Officer'], ['senior', 'Senior Mgmt'], ['authority', 'Chairman AICTE'], ['admin', 'Admin']].map(([key, label]) => <button type="button" key={key} onClick={() => handleRolePreset(key)} className={`p-2 rounded border text-left transition cursor-pointer ${selectedRoleKey === key ? 'border-[#1E3A8A] bg-indigo-50 font-bold text-[#1E3A8A]' : 'border-slate-200 hover:bg-slate-50 text-slate-700'}`}>{label}</button>)}
      </div></div>
      {error && <p className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>}
      <button type="submit" disabled={isLoading} className="w-full py-2.5 px-4 bg-[#1E3A8A] hover:bg-[#1e40af] text-white font-bold rounded-md text-sm transition shadow-md flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"><ShieldCheck className="w-4 h-4 text-amber-400" />{isLoading ? 'Authenticating...' : 'Sign In to Portal'}<ArrowRight className="w-4 h-4" /></button>
      <p className="text-[10px] text-slate-500 text-center">Authorized access only. All activities are monitored and cryptographically audited.</p>
    </form>
  );
}

function ComplaintForm() {
  const [form, setForm] = useState<PublicComplaintPayload>(initialComplaint);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [success, setSuccess] = useState('');
  const update = (name: keyof PublicComplaintPayload, value: string) => setForm((current) => ({ ...current, [name]: value }));
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setSuccess('');
    try { const result = await registerPublicComplaint(form); setSuccess(`Complaint ${result.case_no} registered. It has been sent to the PGRC officer queue for AI-assisted triage.`); setForm(initialComplaint); }
    catch { setError('We could not register your complaint. Please check your details and try again.'); }
    finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="p-6 space-y-5">
      <div className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-900">Submit a complete complaint. AI intake will classify it, assess urgency and sentiment, score priority, resolve the institution, and detect possible overlaps for officer review.</div>
      <section><h3 className="flex items-center gap-2 text-sm font-extrabold text-[#1E3A8A] mb-3"><UserRound className="w-4 h-4" /> Complainant details</h3><div className="grid grid-cols-1 sm:grid-cols-2 gap-3"><Field label="Full name" name="complainant_name" value={form.complainant_name} onChange={update} required /><Field label="Email" name="complainant_email" value={form.complainant_email} onChange={update} required type="email" /><Field label="Phone" name="complainant_phone" value={form.complainant_phone || ''} onChange={update} type="tel" /><label className="block"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Complainant type *</span><select required value={form.complainant_type} onChange={(e) => update('complainant_type', e.target.value)} className={inputClass}><option value="student">Student</option><option value="faculty">Faculty / Staff</option><option value="parent">Parent / Guardian</option><option value="other">Other</option></select></label></div></section>
      <section className="border-t border-slate-200 pt-4"><h3 className="flex items-center gap-2 text-sm font-extrabold text-[#1E3A8A] mb-3"><Building2 className="w-4 h-4" /> College / institution details</h3><div className="grid grid-cols-1 sm:grid-cols-2 gap-3"><div className="sm:col-span-2"><Field label="College / institution name" name="college_name" value={form.college_name} onChange={update} required /></div><Field label="AICTE permanent ID" name="college_permanent_id" value={form.college_permanent_id || ''} onChange={update} /><Field label="University / affiliation" name="college_affiliation" value={form.college_affiliation || ''} onChange={update} /><div className="sm:col-span-2"><Field label="Full college address" name="college_address" value={form.college_address || ''} onChange={update} required /></div><Field label="City" name="college_city" value={form.college_city || ''} onChange={update} required /><Field label="State" name="college_state" value={form.college_state || ''} onChange={update} required /><Field label="PIN code" name="college_pincode" value={form.college_pincode || ''} onChange={update} /></div></section>
      <section className="border-t border-slate-200 pt-4"><h3 className="flex items-center gap-2 text-sm font-extrabold text-[#1E3A8A] mb-3"><FileText className="w-4 h-4" /> Complaint details</h3><div className="grid grid-cols-1 sm:grid-cols-2 gap-3"><label className="block"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Category *</span><select required value={form.category} onChange={(e) => update('category', e.target.value)} className={inputClass}><option>Other</option><option>Fees</option><option>Safety</option><option>Faculty</option><option>Examination</option><option>Placement</option><option>Infrastructure</option><option>Fraud</option><option>Certificate</option></select></label><Field label="Subcategory" name="subcategory" value={form.subcategory || ''} onChange={update} /><div className="sm:col-span-2"><Field label="Complaint subject" name="subject" value={form.subject} onChange={update} required /></div><label className="block sm:col-span-2"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Detailed complaint *</span><textarea required rows={5} value={form.description} onChange={(e) => update('description', e.target.value)} className={`${inputClass} resize-y`} placeholder="Include dates, people involved, notices, amounts, and prior action taken." /></label><Field label="Incident date" name="incident_date" value={form.incident_date || ''} onChange={update} type="date" /><label className="block"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Language</span><select value={form.language} onChange={(e) => update('language', e.target.value)} className={inputClass}><option>English</option><option>Hindi</option><option>Marathi</option><option>Other</option></select></label><label className="block sm:col-span-2"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Relief / action requested</span><textarea rows={3} value={form.relief_sought || ''} onChange={(e) => update('relief_sought', e.target.value)} className={`${inputClass} resize-y`} /></label><label className="block sm:col-span-2"><span className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1">Supporting evidence details</span><textarea rows={3} value={form.supporting_details || ''} onChange={(e) => update('supporting_details', e.target.value)} className={`${inputClass} resize-y`} placeholder="Documents, notices, receipts, URLs, or other evidence." /></label></div></section>
      {error && <p className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>}{success && <p className="flex items-start gap-2 text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-3 py-2"><CheckCircle2 className="w-4 h-4 shrink-0" />{success}</p>}
      <button type="submit" disabled={busy} className="w-full py-2.5 px-4 bg-[#1E3A8A] hover:bg-[#1e40af] text-white font-bold rounded-md text-sm transition shadow-md flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"><FileText className="w-4 h-4 text-amber-400" />{busy ? 'Registering and running AI intake...' : 'Register Complaint'}<ArrowRight className="w-4 h-4" /></button><p className="text-[10px] text-slate-500 text-center">Public complaints are routed to the PGRC intake queue for human officer review.</p>
    </form>
  );
}

function LoginContent() {
  const [tab, setTab] = useState<Tab>('login');
  return <div className="min-h-screen bg-[#f4f6fa] flex flex-col justify-between"><div className="w-full h-1.5 flex"><div className="w-1/3 h-full bg-[#FF9933]" /><div className="w-1/3 h-full bg-white" /><div className="w-1/3 h-full bg-[#138808]" /></div><div className="bg-[#0b132b] text-slate-300 text-xs px-6 py-2 flex items-center justify-between"><span className="text-amber-400 font-bold">GOVERNMENT OF INDIA</span><span className="text-amber-300 font-semibold">Viksit Bharat @2047</span></div><div className="flex-1 flex items-center justify-center p-4"><div className={`w-full ${tab === 'complaint' ? 'max-w-3xl' : 'max-w-md'} bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden`}><div className="bg-gradient-to-r from-[#0f172a] via-[#1E3A8A] to-[#0f172a] text-white p-6 text-center"><div className="w-14 h-14 mx-auto mb-3 rounded-full bg-gradient-to-tr from-amber-500 to-amber-300 p-0.5 shadow-md flex items-center justify-center"><div className="w-full h-full bg-[#1E3A8A] rounded-full flex items-center justify-center"><Building2 className="w-7 h-7 text-amber-300" /></div></div><h2 className="text-xl font-bold font-serif tracking-wide">Complaint-Tantra</h2><p className="text-xs text-amber-300 font-bold uppercase tracking-wider mt-0.5">Grievance Portal</p><p className="text-[11px] text-slate-200 mt-1">All India Council for Technical Education (AICTE)</p><p className="text-[10px] text-slate-300">Integrated Complaint Monitoring & Inter-Bureau Overlap Tracking</p></div><div className="grid grid-cols-2 border-b border-slate-200"><button type="button" onClick={() => setTab('login')} className={`py-3 text-xs font-bold cursor-pointer ${tab === 'login' ? 'text-[#1E3A8A] border-b-2 border-[#1E3A8A] bg-indigo-50' : 'text-slate-500 hover:bg-slate-50'}`}><Lock className="inline w-3.5 h-3.5 mr-1" />Officer Login</button><button type="button" onClick={() => setTab('complaint')} className={`py-3 text-xs font-bold cursor-pointer ${tab === 'complaint' ? 'text-[#1E3A8A] border-b-2 border-[#1E3A8A] bg-indigo-50' : 'text-slate-500 hover:bg-slate-50'}`}><FileText className="inline w-3.5 h-3.5 mr-1" />Register Complaint</button></div>{tab === 'login' ? <LoginForm /> : <ComplaintForm />}</div></div><footer className="bg-[#0b132b] text-slate-400 text-xs py-3 px-6 text-center border-t border-slate-800">All India Council for Technical Education • Nelson Mandela Marg, Vasant Kunj, New Delhi-110070</footer></div>;
}

export default function LoginPage() { return <LoginContent />; }
