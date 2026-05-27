import { useState } from 'react';
import { TemplateGrid } from './template-grid';

interface Template { id: string; name: string; category: string; }
interface Props { templates: Template[]; onSelect: (id: string) => void; }

export function TemplateSelector({ templates, onSelect }: Props) {
  const [category, setCategory] = useState('all');
  const filtered = category === 'all' ? templates : templates.filter((t) => t.category === category);
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button onClick={() => setCategory('all')} className="px-3 py-1 rounded-md text-sm bg-primary text-primary-foreground">全部</button>
        <button onClick={() => setCategory('诉讼')} className="px-3 py-1 rounded-md text-sm border">诉讼</button>
        <button onClick={() => setCategory('非诉')} className="px-3 py-1 rounded-md text-sm border">非诉</button>
      </div>
      <TemplateGrid templates={filtered} onSelect={onSelect} />
    </div>
  );
}
