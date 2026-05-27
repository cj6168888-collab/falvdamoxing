import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import {
  mockCases,
  mockEvidenceList,
  mockDeadlines,
  mockParties,
  createMockDocument,
  createMockThread,
  createMockLetter,
  createMockTimelineEvent,
  createMockHearing,
} from './fixtures';

const mockDocuments = [
  createMockDocument({ id: 'doc-1', title: 'Complaint', status: 'draft' }),
  createMockDocument({ id: 'doc-2', title: 'Evidence List', status: 'draft' }),
  createMockDocument({ id: 'doc-3', title: 'Representation Letter', status: 'draft' }),
];

const mockThreads = [
  createMockThread({ id: 'thread-1', title: 'Loan Fact Dispute' }),
  createMockThread({ id: 'thread-2', title: 'Interest Calculation Dispute' }),
];

const mockLetters = [
  createMockLetter({ id: 1, title: 'Lawyer Letter', mail_status: 'sent' }),
  createMockLetter({ id: 2, title: 'Demand Letter', mail_status: 'draft' }),
];

const mockTimelineEvents = [
  createMockTimelineEvent({ id: 'tl-1', title: 'Case Filed', date: '2024-01-15' }),
  createMockTimelineEvent({ id: 'tl-2', title: 'Evidence Submitted', date: '2024-02-01' }),
  createMockTimelineEvent({ id: 'tl-3', title: 'Hearing', date: '2024-06-20' }),
];

const mockHearings = [
  createMockHearing({ id: 'hearing-1', date: '2024-06-20', status: 'scheduled' }),
];

export const handlers = [
  http.get('/api/cases', ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const type = url.searchParams.get('type');
    let filtered = Object.values(mockCases);
    if (status) filtered = filtered.filter(c => c.status === status);
    if (type) filtered = filtered.filter(c => c.type === type);
    return HttpResponse.json(filtered);
  }),

  http.get('/api/cases/:id', ({ params }) => {
    const caseItem = Object.values(mockCases).find(c => c.id === params.id);
    if (!caseItem) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(caseItem);
  }),

  http.post('/api/cases', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockCases.preparing, ...body, id: 'case-new' }, { status: 201 });
  }),

  http.put('/api/cases/:id', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockCases.preparing, ...body });
  }),

  http.delete('/api/cases/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get('/api/cases/:caseId/evidence', () => HttpResponse.json(mockEvidenceList)),

  http.get('/api/cases/:caseId/evidence/:evidenceId', ({ params }) => {
    const evidence = mockEvidenceList.find(e => e.id === params.evidenceId);
    if (!evidence) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(evidence);
  }),

  http.post('/api/cases/:caseId/evidence', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockEvidenceList[0], ...body, id: 'ev-new' }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/evidence/:evidenceId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockEvidenceList[0], ...body });
  }),

  http.delete('/api/cases/:caseId/evidence/:evidenceId', () => new HttpResponse(null, { status: 204 })),

  http.get('/api/cases/:caseId/documents', () => HttpResponse.json(mockDocuments)),

  http.post('/api/cases/:caseId/documents', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockDocuments[0], ...body, id: 'doc-new' }, { status: 201 });
  }),

  http.get('/api/cases/:caseId/deadlines', () => HttpResponse.json(mockDeadlines)),

  http.post('/api/cases/:caseId/deadlines', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockDeadlines[0], ...body, id: 'dl-new' }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/deadlines/:deadlineId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockDeadlines[0], ...body });
  }),

  http.get('/api/cases/:caseId/parties', () => HttpResponse.json(mockParties)),

  http.post('/api/cases/:caseId/parties', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockParties[0], ...body, id: 'party-new' }, { status: 201 });
  }),

  http.put('/api/cases/parties/:partyId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockParties[0], ...body });
  }),

  http.delete('/api/cases/parties/:partyId', () => new HttpResponse(null, { status: 204 })),

  http.get('/api/cases/:caseId/threads', () => HttpResponse.json(mockThreads)),

  http.post('/api/cases/:caseId/threads', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockThreads[0], ...body, id: 'thread-new' }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/threads/:threadId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockThreads[0], ...body });
  }),

  http.get('/api/cases/:caseId/counter-claims', () => HttpResponse.json([])),

  http.post('/api/cases/:caseId/counter-claims', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: 'cc-new', ...body }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/counter-claims/:claimId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: 'cc-1', ...body });
  }),

  http.get('/api/cases/:caseId/letters', () => HttpResponse.json(mockLetters)),

  http.post('/api/cases/:caseId/letters', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockLetters[0], ...body, id: 'letter-new' }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/letters/:letterId', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockLetters[0], ...body });
  }),

  http.get('/api/cases/:caseId/timeline', () => HttpResponse.json(mockTimelineEvents)),

  http.get('/api/cases/:caseId/hearings', () => HttpResponse.json(mockHearings)),

  http.post('/api/cases/:caseId/hearings', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...mockHearings[0], ...body, id: 'hearing-new' }, { status: 201 });
  }),

  http.get('/api/statistics/overview', () => HttpResponse.json({
    totalCases: Object.values(mockCases).length,
    inProgress: Object.values(mockCases).filter(c => c.status !== 'closed').length,
  })),

  http.post('/api/auth/login', () => HttpResponse.json({
    token: 'mock-jwt-token',
    user: { id: 'user-1', username: 'admin', name: 'Admin', role: 'admin' },
  })),

  http.post('/api/auth/logout', () => HttpResponse.json(null)),

  http.get('/api/auth/me', () => HttpResponse.json({ id: 'user-1', username: 'admin', name: 'Admin', role: 'admin' })),

  http.get('/api/v2/evidence-graph/evidence/list', ({ request }) => {
    const url = new URL(request.url);
    const caseId = url.searchParams.get('caseId');
    const evidence = caseId ? mockEvidenceList.filter(e => e.caseId === caseId) : mockEvidenceList;
    return HttpResponse.json(evidence);
  }),

  http.post('/api/documents/upload/:id', () => HttpResponse.json({ ...mockEvidenceList[0], id: 'ev-new' }, { status: 201 })),

  http.put('/api/v2/evidence-graph/evidence/update', () => HttpResponse.json(mockEvidenceList[0])),

  http.delete('/api/evidence/:evidenceId', () => new HttpResponse(null, { status: 204 })),

  http.post('/api/evidence/check-completeness', () => HttpResponse.json({ score: 85, gaps: [] })),

  http.post('/api/evidence/risk-analyze/:id', () => HttpResponse.json({ risks: [] })),

  http.post('/api/v2/evidence-graph/evidence/correct', () => HttpResponse.json({ corrected: true })),

  http.get('/api/v2/evidence-graph/graph/data', () => HttpResponse.json({ nodes: [], edges: [] })),

  http.get('/api/documents/templates/list', () => HttpResponse.json([])),

  http.get('/api/document-management/case/:caseId/generated', () => HttpResponse.json(mockDocuments)),

  http.get('/api/document-management/case/:caseId/suggestions', () => HttpResponse.json([])),

  http.post('/api/documents/generate/enhanced', () => HttpResponse.json(mockDocuments[0], { status: 201 })),

  http.get('/api/时间把控/case/:caseId/deadlines', () => HttpResponse.json(mockDeadlines)),

  http.post('/api/时间把控/case/:caseId/deadlines', () => HttpResponse.json(mockDeadlines[0], { status: 201 })),

  http.put('/api/时间把控/deadlines/:deadlineId', () => HttpResponse.json(mockDeadlines[0])),

  http.post('/api/时间把控/case/:caseId/generate-milestones', () => HttpResponse.json({ milestones: [] })),

  http.get('/api/时间把控/case/:caseId/letters', () => HttpResponse.json(mockLetters)),

  http.post('/api/时间把控/case/:caseId/letters', () => HttpResponse.json(mockLetters[0], { status: 201 })),

  http.put('/api/时间把控/letters/:letterId', () => HttpResponse.json(mockLetters[0])),

  http.post('/api/时间把控/letters/:letterId/generate-reply', () => HttpResponse.json({ reply: 'Reply content' })),

  http.get('/api/time-control/case/:caseId/letters', () => HttpResponse.json(mockLetters)),

  http.post('/api/time-control/case/:caseId/letters', () => HttpResponse.json(mockLetters[0], { status: 201 })),

  http.put('/api/time-control/letters/:letterId', () => HttpResponse.json(mockLetters[0])),

  http.delete('/api/time-control/letters/:letterId', () => new HttpResponse(null, { status: 204 })),

  http.post('/api/time-control/letters/:letterId/generate-reply', () => HttpResponse.json({ reply: 'Reply content' })),

  http.post('/api/hearings/case/:caseId/hearings', () => HttpResponse.json(mockHearings[0], { status: 201 })),

  http.get('/api/hearings/case/:caseId/hearings', () => HttpResponse.json(mockHearings)),

  http.post('/api/hearings/detect-trap', () => HttpResponse.json({ traps: [] })),

  http.post('/api/hearings/realtime-analysis', () => HttpResponse.json({ analysis: {} })),

  http.post('/api/hearings/hearing/:hearingId/statement', () => HttpResponse.json({ statement: 'Recorded' })),

  http.get('/api/reminders', () => HttpResponse.json([])),

  http.put('/api/reminders/:reminderId', () => HttpResponse.json({ id: 'rem-1', isRead: true })),

  http.put('/api/reminders/mark-all-read', () => HttpResponse.json({ marked: 0 })),

  http.get('/api/cases/:caseId/execution', () => HttpResponse.json({ status: 'pending', records: [] })),

  http.put('/api/cases/:caseId/execution', () => HttpResponse.json({ status: 'updated' })),

  http.post('/api/cases/:caseId/execution/record', () => HttpResponse.json({ id: 'rec-new' }, { status: 201 })),

  http.get('/api/timeline/case/:caseId/deadlines', () => HttpResponse.json(mockDeadlines)),

  http.post('/api/timeline/case/:caseId/deadlines', () => HttpResponse.json(mockDeadlines[0], { status: 201 })),

  http.put('/api/timeline/deadlines/:deadlineId', () => HttpResponse.json(mockDeadlines[0])),

  http.post('/api/timeline/case/:caseId/generate-milestones', () => HttpResponse.json({ milestones: [] })),

  http.get('/api/execution/case/:caseId', () => HttpResponse.json({ status: 'pending', records: [] })),

  http.put('/api/execution/case/:caseId', () => HttpResponse.json({ status: 'updated' })),

  http.post('/api/execution/case/:caseId/records', () => HttpResponse.json({ id: 'rec-new' }, { status: 201 })),

  http.get('/api/reports/status/:reportId', () => HttpResponse.json([])),

  http.get('/api/reports/list/:caseId', () => HttpResponse.json({ reports: [], total: 0 })),

  http.get('/api/reports/detail/:reportId', () => HttpResponse.json({ id: 'report-1', sections: [] })),

  http.post('/api/reports/generate/:reportId', () => HttpResponse.json({ id: 'report-new', status: 'generating' }, { status: 201 })),

  http.post('/api/reports/cancel/:reportId', () => HttpResponse.json({ cancelled: true })),

  http.post('/api/v2/assistant/chat', () => HttpResponse.json({ message: 'AI response' })),

  http.get('/api/v2/assistant/quick-actions/:actionId', () => HttpResponse.json([])),

  http.post('/api/对抗性分析/case/:caseId/analysis', () => HttpResponse.json({ id: 'analysis-new' }, { status: 201 })),

  http.post('/api/对抗性分析/case/:caseId/evidence-matrix', ({ request }) => {
    const url = new URL(request.url);
    const caseId = url.pathname.split('/').pop() || 'case-1';
    return HttpResponse.json({ matrix: [], caseId });
  }),

  http.post('/api/对抗性分析/case/:caseId/scenario-prediction', ({ request }) => {
    const url = new URL(request.url);
    const caseId = url.pathname.split('/').pop() || 'case-1';
    return HttpResponse.json({ scenarios: [], caseId });
  }),

  http.post('/api/v2/senior-analysis/analyze', () => HttpResponse.json({ analysis: {}, depth: 'standard' })),

  http.get('/api/v2/profile/case/:caseId', () => HttpResponse.json({ caseId: 'case-1', summary: 'Profile summary' })),

  http.get('/api/v2/profile/summary/:caseId', () => HttpResponse.json({ case_id: 'case-1', summary: 'Profile summary' })),

  http.get('/api/v2/profile/knowledge-graph/:graphId', () => HttpResponse.json({ nodes: [], edges: [] })),

  http.post('/api/v2/evidence-guide/diagnose', () => HttpResponse.json({ score: 80, questions: [] })),

  http.post('/api/v2/evidence-guide/question/answer', () => HttpResponse.json({ answered: true })),

  http.get('/api/company-info/:name', ({ params }) => {
    const name = decodeURIComponent(String(params.name || ''));
    return HttpResponse.json({
      id: 'comp-1',
      name,
      status: 'active',
      legalRepresentative: 'Test Representative',
    });
  }),

  http.get('/api/company-info/search', ({ request }) => {
    const url = new URL(request.url);
    const keyword = url.searchParams.get('keyword');
    if (keyword && keyword.length >= 2) return HttpResponse.json([{ name: keyword, id: 'comp-1' }]);
    return HttpResponse.json([]);
  }),

  http.get('/api/cases/:caseId/finance', () => HttpResponse.json({ amount: 0, records: [] })),

  http.get('/api/appeal/case/:caseId/appeals', () => HttpResponse.json([])),

  http.get('/api/appeal/case/:caseId/arguments', () => HttpResponse.json([])),

  http.post('/api/appeal/case/:caseId/appeals', () => HttpResponse.json({ id: 'appeal-new' }, { status: 201 })),

  http.post('/api/appeal/case/:caseId/arguments', () => HttpResponse.json({ id: 'arg-new' }, { status: 201 })),

  http.put('/api/appeal/argument/:argumentId', () => HttpResponse.json({ id: 'arg-1' })),

  http.post('/api/export', () => new HttpResponse(new Blob(['export data']), { headers: { 'Content-Type': 'application/pdf' } })),

  http.get('/api/meetings/case/:caseId', () => HttpResponse.json({ meetings: [] })),

  http.get('/api/时间把控/case/:caseId/timeline', () => HttpResponse.json([])),

  http.get(/\/api\/%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7\/case\/[^/]+\/timeline$/, () => HttpResponse.json([])),
];

export const server = setupServer(...handlers);
