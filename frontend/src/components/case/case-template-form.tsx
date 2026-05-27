import * as React from 'react';
import type { CaseTemplate } from '@/types/case-template.types';
import { Button } from '@/components/ui/button';

export type TemplateFormValue = string | number | boolean | string[] | null | undefined;
export type TemplateFormData = Record<string, TemplateFormValue>;

interface CaseTemplateFormProps {
  template: CaseTemplate;
  initialData: TemplateFormData;
  onSubmit: (data: TemplateFormData) => void;
  onAutoFill?: () => void;
  useAutoFill?: boolean;
}

export function CaseTemplateForm({ template, initialData, onSubmit, onAutoFill }: CaseTemplateFormProps) {
  const [formData, setFormData] = React.useState(initialData);

  const handleChange = (key: string, value: TemplateFormValue) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <div className="space-y-4">
      {template.fields?.map(field => (
        <div key={field.key}>
          <label className="block text-sm font-medium mb-1">{field.label}</label>
          <input
            type="text"
            className="w-full p-2 border rounded"
            value={String(formData[field.key] || '')}
            onChange={e => handleChange(field.key, e.target.value)}
          />
        </div>
      ))}
      <div className="flex gap-2">
        <Button onClick={handleSubmit}>提交</Button>
        {onAutoFill && <Button variant="outline" onClick={onAutoFill}>自动填充</Button>}
      </div>
    </div>
  );
}
