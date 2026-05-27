import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import {
  fillFromTemplate,
  generateDeadlinesFromTemplate,
  useCaseTemplates,
  useCreateCaseFromTemplate,
  validateTemplateFields,
} from '@/hooks/use-case-template';
import type { CaseTemplate } from '@/types/case-template.types';

// Mock fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('useCaseTemplates', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.stubGlobal('fetch', mockFetch);
  });

  it('should return templates from local source', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    const { result } = renderHook(() => useCaseTemplates(), { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

describe('useCreateCaseFromTemplate', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.stubGlobal('fetch', mockFetch);
  });

  it('should create case with template data', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'case-1', title: '测试案件' }),
    });

    const { result } = renderHook(() => useCreateCaseFromTemplate(), { wrapper: createWrapper() });
    
    let response: { id: string } | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({
        templateId: 'template-debt',
        formData: {
          plaintiff: '张三',
          defendant: '李四',
          amount: 100000,
        },
      });
    });

    expect(response?.id).toBe('case-1');
  });

  it('should throw error for invalid template', async () => {
    const { result } = renderHook(() => useCreateCaseFromTemplate(), { wrapper: createWrapper() });
    
    await expect(
      result.current.mutateAsync({
        templateId: 'invalid-template',
        formData: {},
      })
    ).rejects.toThrow('模板不存在');
  });
});

describe('fillFromTemplate', () => {
  it('should auto-fill title', () => {
    const template = {
      id: 'template-1',
      name: '民间借贷纠纷',
      type: 'debt_dispute',
      autoFillFields: ['title'],
    } as unknown as CaseTemplate;

    const data = {
      plaintiff: '张三',
      defendant: '李四',
    };

    const filled = fillFromTemplate(template, data);
    
    expect(filled.title).toContain('张三');
    expect(filled.title).toContain('李四');
  });
});

describe('validateTemplateFields', () => {
  it('should return error for missing required fields', () => {
    const template = {
      fields: [
        { key: 'plaintiff', label: '原告', required: true },
        { key: 'defendant', label: '被告', required: true },
      ],
    } as unknown as CaseTemplate;

    const data = {
      plaintiff: '张三',
      // missing defendant
    };

    const result = validateTemplateFields(template, data);
    
    expect(result.valid).toBe(false);
    expect(result.errors.defendant).toBe('被告不能为空');
  });

  it('should validate number fields', () => {
    const template = {
      fields: [
        { key: 'amount', label: '金额', required: true, type: 'number', validation: { min: 0 } },
      ],
    } as unknown as CaseTemplate;

    const data = { amount: -100 };

    const result = validateTemplateFields(template, data);
    
    expect(result.valid).toBe(false);
    expect(result.errors.amount).toContain('不能小于');
  });

  it('should pass for valid data', () => {
    const template = {
      fields: [
        { key: 'plaintiff', label: '原告', required: true },
        { key: 'defendant', label: '被告', required: true },
      ],
    } as unknown as CaseTemplate;

    const data = {
      plaintiff: '张三',
      defendant: '李四',
    };

    const result = validateTemplateFields(template, data);
    
    expect(result.valid).toBe(true);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });
});

describe('generateDeadlinesFromTemplate', () => {
  it('should generate deadlines based on start date', () => {
    const template = {
      deadlines: [
        { id: 'd1', name: '立案', type: 'filing', daysFromStart: 0, isCritical: true },
        { id: 'd2', name: '举证期限', type: 'response', daysFromStart: 15, isCritical: false },
      ],
    } as unknown as CaseTemplate;

    const startDate = new Date('2026-04-01');
    const deadlines = generateDeadlinesFromTemplate(template, startDate);

    expect(deadlines).toHaveLength(2);
    expect(deadlines[0].name).toBe('立案');
    expect(deadlines[0].dueDate.toISOString().split('T')[0]).toBe('2026-04-01');
    expect(deadlines[1].name).toBe('举证期限');
    expect(deadlines[1].dueDate.toISOString().split('T')[0]).toBe('2026-04-16');
  });
});
