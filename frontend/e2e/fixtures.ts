import { test as base, expect, type Page } from '@playwright/test';

export interface TestFixtures {
  authenticatedPage: Page;
}

export const test = base.extend<TestFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await mockApi(page);
    await page.goto('/');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);
    await use(page);
  },
});

export { expect } from '@playwright/test';

const testUser = {
  id: 'user-1',
  username: 'admin',
  email: 'admin@example.com',
  full_name: 'Admin User',
  role: 'admin',
  tenant_id: 'tenant-1',
  is_active: true,
  is_email_verified: true,
  last_login_at: null,
  created_at: '2026-01-01T00:00:00Z',
};

const testTenant = {
  id: 'tenant-1',
  name: '测试律所',
  tenant_type: 'law_firm',
  slug: 'test-law-firm',
  logo_url: null,
  plan: 'pro',
  subscription_status: 'active',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const testCase = {
  id: 'case-1',
  title: '借款合同纠纷',
  case_type: 'civil',
  status: 'litigating',
  description: '测试案件描述',
  claim_amount: 100000,
  plaintiff: '测试客户',
  defendant: '对方当事人',
  evidence_count: 2,
  document_count: 1,
  deadline_count: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
};

const testEvidence = [
  {
    id: 'evidence-1',
    case_id: 1,
    display_name: '借款合同.pdf',
    original_filename: 'loan-contract.pdf',
    evidence_type: '书证',
    summary: '双方借款合同扫描件',
    extracted_content: '合同载明借款金额、还款期限和违约责任。',
    raw_content: '',
    proves_facts: ['双方存在借款合同关系'],
    credibility_score: 92,
    status: 'processed',
    source_party: 'own',
    created_at: '2026-01-03T00:00:00Z',
    file_path: '/mock/loan-contract.pdf',
    entity_tags: [],
  },
];

const documentTemplates = [
  { type: 'complaint', name: '起诉状', description: '用于向法院提起诉讼' },
  { type: 'lawyer_letter', name: '律师函', description: '用于正式催告或沟通' },
];

const generatedDocuments = [
  {
    id: 'doc-1',
    title: '借款合同纠纷起诉状',
    document_type: '起诉状',
    content: '原告测试客户诉被告对方当事人借款合同纠纷一案。',
    version: 1,
    status: 'draft',
    created_at: '2026-01-04T00:00:00Z',
    updated_at: '2026-01-04T00:00:00Z',
  },
];

const testLetters = [
  {
    id: 1,
    case_id: 1,
    direction: 'outgoing',
    letter_type: 'lawyer_letter',
    title: '还款催告律师函',
    reference_number: '函-2026-001',
    sender: '测试律所',
    recipient: '对方当事人',
    letter_date: '2026-01-05',
    deadline: '2026-01-20',
    reply_required: 'required',
    urgent_level: 'medium',
    is_overdue: false,
    days_until_deadline: 15,
    content_summary: '要求对方当事人按借款合同约定履行还款义务。',
    key_demands: '归还借款本金及逾期利息',
    is_replied: false,
    mail_status: 'draft',
    has_reply: false,
    created_at: '2026-01-05T00:00:00Z',
    updated_at: '2026-01-05T00:00:00Z',
  },
];

const timelineNodes = [
  {
    title: '第一次开庭',
    node_type: 'hearing',
    date: '2026-02-15',
    location: '北京市朝阳区人民法院',
    description: '围绕借款合同关系及还款事实进行举证质证。',
    related_evidence_ids: ['evidence-1'],
    hearing_notes: '重点确认借款合同、转账记录和催告函送达情况。',
  },
];

const parties = [
  {
    id: 'party-1',
    name: '测试客户',
    role: 'plaintiff',
    phone: '13800000000',
    email: 'plaintiff@example.com',
    address: '北京市朝阳区',
  },
  {
    id: 'party-2',
    name: '对方当事人',
    role: 'defendant',
    phone: '13900000000',
    email: 'defendant@example.com',
    address: '北京市海淀区',
  },
];

const profileSummary = {
  case_id: 1,
  summary: {
    case_id: 1,
    completeness: { score: 72, level: '详细' },
    knowledge_stats: { total: 2, by_type: { fact: 1, evidence: 1 } },
    conversation_count: 1,
    evidence_count: 1,
    unresolved_gaps: [],
    last_updated: '2026-01-05T00:00:00Z',
  },
  recent_conversations: [
    { turn_id: 'turn-1', turn_number: 1, user_input: '案情梳理', input_type: 'chat', created_at: '2026-01-05T00:00:00Z' },
  ],
  recent_knowledge: [
    {
      atom_id: 'k-1',
      content: '双方存在借款合同关系',
      type: 'fact',
      source: 'evidence',
      confidence: 0.92,
      verified: true,
      keywords: ['借款合同'],
      entity_tags: ['测试客户', '对方当事人'],
      extracted_at: '2026-01-05T00:00:00Z',
    },
  ],
  profile_tips: ['证据链较完整，可继续补充还款催告材料'],
  persisted: true,
};

export async function mockApi(page: Page): Promise<void> {
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const path = url.pathname;

    if (!path.startsWith('/api/')) {
      await route.continue();
      return;
    }

    if (path === '/api/auth/login' && method === 'POST') {
      const body = request.postDataJSON() as { username?: string; password?: string };
      if (body.username === 'admin' && body.password === 'password') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            user: testUser,
            tenant: testTenant,
            tokens: {
              access_token: 'e2e-access-token',
              refresh_token: 'e2e-refresh-token',
              token_type: 'Bearer',
              expires_in: 3600,
            },
          }),
        });
        return;
      }

      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: '用户名或密码错误', code: 'UNAUTHORIZED' }),
      });
      return;
    }

    if (path === '/api/auth/me') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ user: testUser }) });
      return;
    }

    if (path === '/api/auth/logout' || path === '/api/auth/refresh') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
      return;
    }

    if (path === '/api/dashboard') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          stats: { total_cases: 1, active_cases: 1, closed_cases: 0, execution_cases: 0 },
          urgent_items: [],
          upcoming_tasks: [],
        }),
      });
      return;
    }

    if (path === '/api/cases' && method === 'GET') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([testCase]) });
      return;
    }

    if (path === '/api/cases' && method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...testCase, id: 'case-new', title: '测试案件' }),
      });
      return;
    }

    if (/^\/api\/cases\/[^/]+$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(testCase) });
      return;
    }

    if (/^\/api\/cases\/[^/]+\/parties/.test(path)) {
      if (method === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(parties) });
        return;
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(parties[0]) });
      return;
    }

    if (path === '/api/documents/templates' || path === '/api/documents/templates/list') {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(documentTemplates) });
      return;
    }

    if (/^\/api\/document-management\/case\/[^/]+\/generated$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(generatedDocuments) });
      return;
    }

    if (/^\/api\/document-management\/case\/[^/]+\/suggestions$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      return;
    }

    if (/^\/api\/time-control\/case\/[^/]+\/letters$/.test(path)) {
      if (method === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(testLetters) });
        return;
      }
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(testLetters[0]) });
      return;
    }

    if (/^\/api\/time-control\/case\/[^/]+\/letters\/discovery-status$/.test(path)) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          correspondence_evidence: 1,
          folder_letter_files: 0,
          folder_total_files: 1,
          auto_discovered_letters: 0,
          manual_letters: 1,
          total_letters: 1,
          total_potential_letters: 1,
          has_pending_discovery: false,
        }),
      });
      return;
    }

    if (/^\/api\/time-control\/case\/[^/]+\/letters\/discover$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ discovered: 0, skipped: 1 }) });
      return;
    }

    if (/^\/api\/time-control\/letters\/[^/]+/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(testLetters[0]) });
      return;
    }

    if (/^\/api\/timeline\/case\/[^/]+$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(timelineNodes) });
      return;
    }

    if (path === '/api/documents/generate/enhanced' || path === '/api/smart-chat/generate-document') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          document_id: 101,
          content: '起诉状\n\n原告测试客户诉被告对方当事人借款合同纠纷。',
          evidence_count: 1,
        }),
      });
      return;
    }

    if (/^\/api\/v2\/profile\/summary\//.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(profileSummary) });
      return;
    }

    if (/^\/api\/v2\/profile\/knowledge-graph\//.test(path)) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          case_id: 1,
          nodes: [{ id: 'k-1', label: '借款合同关系', type: 'fact', color: '#3b82f6', verified: true, confidence: 0.92 }],
          edges: [],
          stats: { total_nodes: 1, total_edges: 0, by_type: { fact: 1 } },
        }),
      });
      return;
    }

    if (/^\/api\/v2\/profile\/gaps\//.test(path)) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ case_id: 1, unresolved_gaps: [], count: 0 }) });
      return;
    }

    if (path === '/api/v2/evidence-graph/evidence/list') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ evidence_list: testEvidence }),
      });
      return;
    }

    if (path === '/api/v2/evidence-graph/graph/data') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ nodes: [], edges: [] }),
      });
      return;
    }

    if (path.startsWith('/api/reminders')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ reminders: [], total: 0 }) });
      return;
    }

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });
}

export async function login(page: Page, username = 'admin', password = 'password'): Promise<void> {
  await mockApi(page);
  await page.goto('/');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/dashboard/);
}

export async function navigateToCase(page: Page, caseId: string): Promise<void> {
  await page.goto(`/cases/${caseId}`);
  await page.waitForLoadState('networkidle');
}

export async function navigateToPage(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}

export async function fillFormField(
  page: Page,
  fieldName: string,
  value: string
): Promise<void> {
  await page.fill(`[name="${fieldName}"]`, value);
}

export async function selectDropdownOption(
  page: Page,
  selectName: string,
  option: string
): Promise<void> {
  await page.selectOption(`[name="${selectName}"]`, option);
}

export async function clickElement(page: Page, selector: string): Promise<void> {
  await page.click(selector);
}

export async function waitForElement(page: Page, selector: string, timeout = 10000): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible', timeout });
}

export async function expectElementVisible(page: Page, selector: string): Promise<void> {
  await expect(page.locator(selector)).toBeVisible();
}

export async function expectElementNotVisible(page: Page, selector: string): Promise<void> {
  await expect(page.locator(selector)).not.toBeVisible();
}

export async function expectTextContains(page: Page, selector: string, text: string): Promise<void> {
  await expect(page.locator(selector)).toContainText(text);
}

export async function expectTextEquals(page: Page, selector: string, text: string): Promise<void> {
  await expect(page.locator(selector)).toHaveText(text);
}

export async function expectUrlContains(page: Page, text: string): Promise<void> {
  await expect(page).toHaveURL(new RegExp(text));
}

export async function expectUrlEquals(page: Page, url: string): Promise<void> {
  await expect(page).toHaveURL(url);
}

export async function screenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: `e2e/screens/${name}.png`, fullPage: true });
}
