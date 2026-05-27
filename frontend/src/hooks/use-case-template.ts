import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { CaseTemplate, CaseTemplateCategory } from '@/types/case-template.types';
import { CASE_TEMPLATES, CASE_TEMPLATE_CATEGORIES, getTemplate, generateCaseTitle } from '@/types/case-template.types';

type CaseFormValue = string | number | boolean | string[] | null | undefined;
type CaseFormData = Record<string, CaseFormValue>;

// 获取所有模板
export function useCaseTemplates() {
  return useQuery({
    queryKey: ['case-templates'],
    queryFn: async (): Promise<CaseTemplate[]> => {
      return CASE_TEMPLATES;
    },
    staleTime: 5 * 60 * 1000,
  });
}

// 获取单个模板（别名）
export const useCaseTemplate = useCaseTemplates;

// 获取模板分类
export function useTemplateCategories() {
  return useQuery({
    queryKey: ['template-categories'],
    queryFn: async (): Promise<CaseTemplateCategory[]> => {
      // TODO: 替换为实际API调用
      return CASE_TEMPLATE_CATEGORIES;
    },
    staleTime: 5 * 60 * 1000,
  });
}

// 获取单个模板
export function useTemplate(id: string) {
  return useQuery({
    queryKey: ['case-template', id],
    queryFn: async (): Promise<CaseTemplate | null> => {
      // TODO: 替换为实际API调用
      const template = getTemplate(id);
      return template || null;
    },
    enabled: !!id,
  });
}

// 获取推荐模板
export function useRecommendedTemplates(caseType?: string) {
  return useQuery({
    queryKey: ['recommended-templates', caseType],
    queryFn: async (): Promise<CaseTemplate[]> => {
      // TODO: 替换为实际API调用
      if (caseType) {
        return CASE_TEMPLATES.filter(t => 
          t.type === caseType || t.category === caseType
        );
      }
      return CASE_TEMPLATES.slice(0, 3); // 返回前3个作为推荐
    },
  });
}

// 创建案件时使用模板
export function useCreateCaseFromTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      templateId,
      formData,
    }: {
      templateId: string;
      formData: CaseFormData;
    }) => {
      // TODO: 替换为实际API调用
      const template = getTemplate(templateId);
      if (!template) {
        throw new Error('模板不存在');
      }

      // 自动填充
      const caseData = {
        ...formData,
        templateId,
        type: template.type,
        // 生成标题
        title: generateCaseTitle(template, {
          plaintiff: valueToString(formData.plaintiff),
          defendant: valueToString(formData.defendant),
        }),
        // 添加推荐证据
        recommendedEvidence: template.recommendedEvidence,
        // 添加推荐文书
        recommendedDocuments: template.recommendedDocuments,
        // 添加相关法条
        relatedLaws: template.relatedLaws,
      };

      // 调用创建案件API
      const response = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseData),
      });

      if (!response.ok) {
        throw new Error('创建案件失败');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });
}

// 填充模板字段
export function fillFromTemplate(
  template: CaseTemplate,
  data: CaseFormData
): CaseFormData {
  const filled: CaseFormData = { ...data };

  // 自动填充标题
  if (!filled.title && template.autoFillFields.includes('title')) {
    filled.title = generateCaseTitle(template, {
      plaintiff: valueToString(filled.plaintiff),
      defendant: valueToString(filled.defendant),
    });
  }

  // 自动填充类型
  if (template.autoFillFields.includes('type')) {
    filled.type = template.type;
  }

  // 自动填充描述
  if (template.autoFillFields.includes('description') && !filled.description) {
    const parties = filled.plaintiff && filled.defendant
      ? `${filled.plaintiff}诉${filled.defendant}`
      : '';
    filled.description = `${parties}${template.name}案`;
  }

  return filled;
}

// 验证模板必填字段
export function validateTemplateFields(
  template: CaseTemplate,
  data: CaseFormData
): { valid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};

  for (const field of template.fields) {
    if (field.required && !data[field.key]) {
      errors[field.key] = `${field.label}不能为空`;
    }

    // 类型验证
    if (data[field.key]) {
      switch (field.type) {
        case 'number':
          if (isNaN(Number(data[field.key]))) {
            errors[field.key] = `${field.label}必须是数字`;
          }
          if (field.validation?.min !== undefined && Number(data[field.key]) < field.validation.min) {
            errors[field.key] = `${field.label}不能小于${field.validation.min}`;
          }
          if (field.validation?.max !== undefined && Number(data[field.key]) > field.validation.max) {
            errors[field.key] = `${field.label}不能大于${field.validation.max}`;
          }
          break;

        case 'date': {
          const date = new Date(valueToString(data[field.key]) || '');
          if (isNaN(date.getTime())) {
            errors[field.key] = `${field.label}日期格式不正确`;
          }
          break;
        }
      }
    }
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
}

function valueToString(value: unknown): string | undefined {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return undefined;
}

// 从模板生成deadline
export function generateDeadlinesFromTemplate(
  template: CaseTemplate,
  startDate: Date
): Array<{
  name: string;
  type: string;
  dueDate: Date;
  description: string;
  isCritical: boolean;
}> {
  return template.deadlines.map(deadline => ({
    name: deadline.name,
    type: deadline.type,
    dueDate: new Date(startDate.getTime() + deadline.daysFromStart * 24 * 60 * 60 * 1000),
    description: deadline.description,
    isCritical: deadline.isCritical,
  }));
}
