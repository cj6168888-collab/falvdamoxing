import type { CaseTemplate } from '@/types/case-template.types';

interface CaseTemplateSelectorProps {
  templates: CaseTemplate[];
  onSelect: (template: CaseTemplate) => void;
  isLoading?: boolean;
}

export function CaseTemplateSelector({ templates, onSelect, isLoading }: CaseTemplateSelectorProps) {
  if (isLoading) return <div>加载中...</div>;
  return (
    <div className="grid grid-cols-2 gap-4">
      {templates.map(template => (
        <div 
          key={template.id}
          className="p-4 border rounded-lg cursor-pointer hover:border-primary"
          onClick={() => onSelect(template)}
        >
          <div className="font-medium">{template.name}</div>
          <div className="text-sm text-muted-foreground">{template.description}</div>
        </div>
      ))}
    </div>
  );
}
