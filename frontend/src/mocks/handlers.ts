import { http, HttpResponse } from 'msw';

const mockCases = [
  {
    id: 'case-1',
    name: '张三诉李四借款纠纷案',
    caseNumber: '(2024)京0105民初1234号',
    type: 'civil',
    status: 'active',
    clientName: '张三',
    opposingParty: '李四',
    amount: 500000,
    filingDate: '2024-01-15',
    nextHearingDate: '2024-06-20',
    assignedLawyer: '王律师',
    createdAt: '2024-01-10T10:00:00Z',
    updatedAt: '2024-03-15T14:30:00Z',
  },
  {
    id: 'case-2',
    name: '某公司劳动合同纠纷案',
    caseNumber: '(2024)京0105民初5678号',
    type: 'labor',
    status: 'active',
    clientName: '某公司',
    opposingParty: '赵六',
    amount: 120000,
    filingDate: '2024-02-01',
    nextHearingDate: '2024-07-10',
    assignedLawyer: '刘律师',
    createdAt: '2024-01-28T09:00:00Z',
    updatedAt: '2024-03-20T11:00:00Z',
  },
];

const mockEvidence = [
  {
    id: 'ev-1',
    caseId: 'case-1',
    name: '借款合同原件',
    type: 'document',
    category: '书证',
    source: '原告提供',
    uploadDate: '2024-01-20',
    status: 'verified',
    fileSize: 2048000,
    mimeType: 'application/pdf',
  },
  {
    id: 'ev-2',
    caseId: 'case-1',
    name: '银行转账记录',
    type: 'document',
    category: '书证',
    source: '银行调取',
    uploadDate: '2024-01-25',
    status: 'pending',
    fileSize: 1024000,
    mimeType: 'application/pdf',
  },
];

const mockDocuments = [
  {
    id: 'doc-1',
    caseId: 'case-1',
    name: '起诉状',
    type: 'complaint',
    status: 'completed',
    version: 3,
    createdAt: '2024-01-12T10:00:00Z',
    updatedAt: '2024-01-18T16:00:00Z',
  },
];

const mockDeadlines = [
  {
    id: 'dl-1',
    caseId: 'case-1',
    title: '举证期限',
    type: 'evidence',
    dueDate: '2024-04-15',
    status: 'upcoming',
    priority: 'high',
    reminderDays: 7,
  },
  {
    id: 'dl-2',
    caseId: 'case-1',
    title: '开庭日期',
    type: 'hearing',
    dueDate: '2024-06-20',
    status: 'upcoming',
    priority: 'critical',
    reminderDays: 14,
  },
];

const mockAppeals = [
  { id: 'appeal-1', caseId: 'case-1', reason: 'New evidence found', status: 'pending' },
];

const mockAppealArguments = [
  { id: 'arg-1', caseId: 'case-1', content: 'Legal argument content' },
];

const mockLetters = [
  { id: 'letter-1', caseId: 'case-1', recipient: 'Court', content: 'Letter content', status: 'draft' },
];

const mockThreads = [
  { id: 'thread-1', caseId: 'case-1', title: 'Thread 1', content: 'Thread content' },
];

const mockCounterClaims = [
  { id: 'cc-1', caseId: 'case-1', title: 'Counter Claim', amount: 50000 },
];

const mockHearings = [
  { id: 'hearing-1', caseId: 'case-1', date: '2024-06-20', type: 'trial' },
  { id: 'hearing-2', caseId: 'case-1', date: '2024-07-01', type: 'pretrial' },
];

const mockParties = [
  { id: 'party-1', caseId: 'case-1', name: 'John Doe', role: 'plaintiff' },
  { id: 'party-2', caseId: 'case-1', name: 'Jane Smith', role: 'defendant' },
];

const mockReminders = [
  { id: 'reminder-1', caseId: 'case-1', message: 'Upcoming deadline', isRead: false },
  { id: 'reminder-2', caseId: 'case-1', message: 'Court hearing tomorrow', isRead: false },
];

const mockReports = [
  { id: 'report-1', caseId: 'case-1', type: 'summary', status: 'completed' },
];

const mockExecution = { caseId: 'case-1', status: 'pending', amount: 100000 };

const mockFinance = { caseId: 'case-1', totalAmount: 500000, paid: 200000, outstanding: 300000 };

const mockMeeting = { caseId: 'case-1', date: '2024-05-01', participants: ['Lawyer A', 'Client B'] };

const mockProfile = { id: 'case-1', name: 'Case Profile', summary: 'Case summary' };

const mockSeniorAnalysis = { caseId: 'case-1', depth: 'standard', analysis: 'Analysis result' };

const mockTimeline = [
  { id: 'tl-1', caseId: 'case-1', date: '2024-01-15', event: 'Case filed' },
  { id: 'tl-2', caseId: 'case-1', date: '2024-06-20', event: 'Hearing scheduled' },
];

const mockCompanyInfo = { name: 'Test Company', registrationNumber: '123456', status: 'active' };

const mockCompanySearch = [
  { name: 'Test Company', id: 'comp-1' },
  { name: 'Test Corp', id: 'comp-2' },
];

const mockEvidenceGuide = { caseId: 'case-1', questions: [{ index: 0, text: 'What is the dispute about?' }] };

const mockQuickActions = [{ id: 'action-1', label: 'Generate Report' }, { id: 'action-2', label: 'Review Evidence' }];

const mockChatResponse = { data: { content: 'AI response to your question' } };

const mockAdversarialAnalysis = { caseId: 'case-1', analysis: 'Adversarial analysis result' };

const mockEvidenceMatrix = { caseId: 'case-1', matrix: [[1, 0], [0, 1]] };

const mockScenarioPrediction = { caseId: 'case-1', scenarios: ['Scenario A', 'Scenario B'] };

const mockOpponentAnalysis = { caseId: 'case-1', opponent: 'Defendant', weaknesses: ['Weak point 1'] };

const mockEvidenceGraph = { caseId: 'case-1', nodes: [], edges: [] };

const mockEvidenceCompleteness = { caseId: 'case-1', score: 75, missing: ['Document A'] };

const mockEvidenceRisk = { caseId: 'case-1', riskLevel: 'medium', risks: ['Risk 1'] };

export const handlers = [
  http.get('/api/cases', () => {
    return HttpResponse.json({ data: mockCases, total: mockCases.length, page: 1, pageSize: 20 });
  }),

  http.get('/api/cases/:id', ({ params }) => {
    const caseItem = mockCases.find(c => c.id === params.id);
    if (!caseItem) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(caseItem);
  }),

  http.post('/api/cases', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    const newCase = {
      id: `case-${Date.now()}`,
      ...body,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return HttpResponse.json(newCase, { status: 201 });
  }),

  http.put('/api/cases/:id', async () => {
    return HttpResponse.json(mockCases[0]);
  }),

  http.delete('/api/cases/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(/\/api\/document-management\/case\/[^/]+\/generated/, () => {
    return HttpResponse.json(mockDocuments);
  }),

  http.get('/api/documents/templates/list', () => {
    return HttpResponse.json([{ id: 'template-1', name: 'Complaint Template' }]);
  }),

  http.post('/api/documents/generate/enhanced', async () => {
    return HttpResponse.json({ id: `doc-${Date.now()}`, status: 'generating' });
  }),

  http.get(/\/api\/document-management\/case\/[^/]+\/suggestions/, () => {
    return HttpResponse.json([{ type: 'complaint', reason: 'Based on case type' }]);
  }),

  http.get('/api/cases/:caseId/threads', () => {
    return HttpResponse.json(mockThreads);
  }),

  http.post('/api/cases/:caseId/threads', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `thread-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/threads/:threadId', async () => {
    return HttpResponse.json(mockThreads[0]);
  }),

  http.get('/api/cases/:caseId/counter-claims', () => {
    return HttpResponse.json(mockCounterClaims);
  }),

  http.post('/api/cases/:caseId/counter-claims', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `cc-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put('/api/cases/:caseId/counter-claims/:claimId', async () => {
    return HttpResponse.json(mockCounterClaims[0]);
  }),

  http.get('/api/cases/:caseId/parties', () => {
    return HttpResponse.json(mockParties);
  }),

  http.post('/api/cases/:caseId/parties', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `party-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put('/api/cases/parties/:partyId', async () => {
    return HttpResponse.json(mockParties[0]);
  }),

  http.delete('/api/cases/parties/:partyId', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get('/api/cases/:caseId/execution', () => {
    return HttpResponse.json(mockExecution);
  }),

  http.put('/api/cases/:caseId/execution', async () => {
    return HttpResponse.json(mockExecution);
  }),

  http.post('/api/cases/:caseId/execution/record', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `rec-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.get('/api/cases/:caseId/finance', () => {
    return HttpResponse.json(mockFinance);
  }),

  http.put('/api/cases/:caseId/finance', async () => {
    return HttpResponse.json(mockFinance);
  }),

  http.get('/api/v2/evidence-graph/evidence/list', () => {
    return HttpResponse.json(mockEvidence);
  }),

  http.post('/api/documents/upload/:caseId', async () => {
    return HttpResponse.json({ id: `ev-${Date.now()}`, name: 'Uploaded file' }, { status: 201 });
  }),

  http.put('/api/v2/evidence-graph/evidence/update', async () => {
    return HttpResponse.json(mockEvidence[0]);
  }),

  http.delete('/api/evidence/:evidenceId', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.post('/api/evidence/check-completeness', async () => {
    return HttpResponse.json(mockEvidenceCompleteness);
  }),

  http.post('/api/evidence/risk-analyze/:caseId', async () => {
    return HttpResponse.json(mockEvidenceRisk);
  }),

  http.post('/api/v2/evidence-graph/evidence/correct', async () => {
    return HttpResponse.json({ corrected: true });
  }),

  http.get('/api/v2/evidence-graph/graph/data', () => {
    return HttpResponse.json(mockEvidenceGraph);
  }),

  http.get(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*deadlines/, () => {
    return HttpResponse.json(mockDeadlines);
  }),

  http.post(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*deadlines/, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `dl-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*deadlines/, async () => {
    return HttpResponse.json(mockDeadlines[0]);
  }),

  http.post(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*generate-milestones/, async () => {
    return HttpResponse.json([{ id: 'ms-1', title: 'Milestone 1' }]);
  }),

  http.get(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*timeline/, () => {
    return HttpResponse.json(mockTimeline);
  }),

  http.get(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*letters/, () => {
    return HttpResponse.json(mockLetters);
  }),

  http.post(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*letters/, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `letter-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*letters/, async () => {
    return HttpResponse.json(mockLetters[0]);
  }),

  http.post(/.*%E6%97%B6%E9%97%B4%E6%8A%8A%E6%8E%A7.*generate-reply/, async () => {
    return HttpResponse.json({ reply: 'Generated reply content' });
  }),

  http.get('/api/appeal/case/:caseId/appeals', () => {
    return HttpResponse.json(mockAppeals);
  }),

  http.get('/api/appeal/case/:caseId/arguments', () => {
    return HttpResponse.json(mockAppealArguments);
  }),

  http.post('/api/appeal/case/:caseId/appeals', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `appeal-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.post('/api/appeal/case/:caseId/arguments', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `arg-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.put('/api/appeal/argument/:argumentId', async () => {
    return HttpResponse.json(mockAppealArguments[0]);
  }),

  http.get('/api/hearings/case/:caseId/hearings', () => {
    return HttpResponse.json(mockHearings);
  }),

  http.post('/api/hearings/case/:caseId/hearings', async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ id: `hearing-${Date.now()}`, ...body }, { status: 201 });
  }),

  http.post('/api/hearings/detect-trap', async () => {
    return HttpResponse.json({ traps: ['Detected trap 1'] });
  }),

  http.post('/api/hearings/realtime-analysis', async () => {
    return HttpResponse.json({ analysis: 'Realtime analysis result' });
  }),

  http.post('/api/hearings/hearing/:hearingId/statement', async () => {
    return HttpResponse.json({ statement: 'Recorded statement' });
  }),

  http.get('/api/meetings/case/:caseId', () => {
    return HttpResponse.json(mockMeeting);
  }),

  http.get('/api/reminders', () => {
    return HttpResponse.json(mockReminders);
  }),

  http.put('/api/reminders/:reminderId', async () => {
    return HttpResponse.json({ success: true });
  }),

  http.put('/api/reminders/mark-all-read', async () => {
    return HttpResponse.json({ success: true });
  }),

  http.get('/api/reports/status/:caseId', () => {
    return HttpResponse.json(mockReports);
  }),

  http.post('/api/reports/generate/:caseId', async () => {
    return HttpResponse.json({ id: `report-${Date.now()}`, status: 'generating' });
  }),

  http.post('/api/reports/cancel/:caseId', async () => {
    return HttpResponse.json({ cancelled: true });
  }),

  http.get('/api/company-info/:name', () => {
    return HttpResponse.json(mockCompanyInfo);
  }),

  http.get('/api/company-info/search', () => {
    return HttpResponse.json(mockCompanySearch);
  }),

  http.get('/api/v2/profile/summary/:caseId', () => {
    return HttpResponse.json(mockProfile);
  }),

  http.post('/api/v2/senior-analysis/analyze', async () => {
    return HttpResponse.json(mockSeniorAnalysis);
  }),

  http.post('/api/v2/evidence-guide/diagnose', async () => {
    return HttpResponse.json(mockEvidenceGuide);
  }),

  http.post('/api/v2/evidence-guide/question/answer', async () => {
    return HttpResponse.json({ answered: true });
  }),

  http.post('/api/v2/assistant/chat', async () => {
    return HttpResponse.json(mockChatResponse);
  }),

  http.get('/api/v2/assistant/quick-actions/:caseId', () => {
    return HttpResponse.json(mockQuickActions);
  }),

  http.post(/.*%E5%AF%B9%E6%8A%97%E6%80%A7%E5%88%86%E6%9E%90.*analysis/, async () => {
    return HttpResponse.json(mockAdversarialAnalysis);
  }),

  http.post(/.*%E5%AF%B9%E6%8A%97%E6%80%A7%E5%88%86%E6%9E%90.*evidence-matrix/, async () => {
    return HttpResponse.json(mockEvidenceMatrix);
  }),

  http.post(/.*%E5%AF%B9%E6%8A%97%E6%80%A7%E5%88%86%E6%9E%90.*scenario-prediction/, async () => {
    return HttpResponse.json(mockScenarioPrediction);
  }),

  http.post(/.*%E5%AF%B9%E6%8A%97%E6%80%A7%E5%88%86%E6%9E%90.*opponent-analysis/, async () => {
    return HttpResponse.json(mockOpponentAnalysis);
  }),

  http.post('/api/export', async () => {
    return new HttpResponse(new Blob(['export data']), { status: 200 });
  }),

  http.post('/api/auth/login', async () => {
    return HttpResponse.json({
      data: {
        token: 'mock-jwt-token',
        user: {
          id: 'user-1',
          username: 'admin',
          name: '管理员',
          role: 'admin',
        },
      },
    });
  }),
];
