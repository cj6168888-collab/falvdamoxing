import type { CaseTemplate } from '@/types/case-template.types';
import type { TemplateFormData } from './case-template-form';

interface CaseTemplatePreviewProps {
  template: CaseTemplate;
  formData: TemplateFormData;
  onEdit?: () => void;
}

export function CaseTemplatePreview({ template, formData, onEdit }: CaseTemplatePreviewProps) {
  return (
    <div className="space-y-4">
      <div className="p-4 border rounded">
        <h4 className="font-medium">{template.name}</h4>
        <p className="text-sm text-muted-foreground">{template.description}</p>
      </div>
      <div className="space-y-2">
        {Object.entries(formData).map(([key, value]) => (
          <div key={key} className="flex justify-between p-2 border-b">
            <span className="text-muted-foreground">{key}:</span>
            <span>{String(value)}</span>
          </div>
        ))}
      </div>
      {onEdit && (
        <button onClick={onEdit} className="text-primary hover:underline">
          编辑
        </button>
      )}
    </div>
  );
}
