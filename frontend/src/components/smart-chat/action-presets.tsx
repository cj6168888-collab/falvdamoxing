import {
  Calculator,
  ChevronUp,
  FileDown,
  FileText,
  RotateCcw,
  ThumbsUp,
  Trash2,
} from 'lucide-react';

export const PRESET_ACTIONS = {
  expand: (onClick: () => void) => ({
    id: 'expand',
    icon: <ChevronUp className="h-3.5 w-3.5" />,
    label: '展开/折叠',
    onClick,
  }),
  approve: (onClick: () => void, disabled?: boolean) => ({
    id: 'approve',
    icon: <ThumbsUp className="h-3.5 w-3.5" />,
    label: '认可',
    onClick,
    variant: 'ghost' as const,
    className: 'text-green-600' as const,
    disabled,
  }),
  retry: (onClick: () => void) => ({
    id: 'retry',
    icon: <RotateCcw className="h-3.5 w-3.5" />,
    label: '重新回答',
    onClick,
    variant: 'ghost' as const,
    className: 'text-amber-600' as const,
  }),
  delete: (onClick: () => void, disabled?: boolean) => ({
    id: 'delete',
    icon: <Trash2 className="h-3.5 w-3.5" />,
    label: '删除',
    onClick,
    variant: 'ghost' as const,
    className: 'text-red-500' as const,
    disabled,
  }),
  exportPdf: (onClick: () => void) => ({
    id: 'export-pdf',
    icon: <FileDown className="h-3.5 w-3.5" />,
    label: '导出 PDF',
    onClick,
  }),
  exportWord: (onClick: () => void) => ({
    id: 'export-word',
    icon: <FileText className="h-3.5 w-3.5" />,
    label: '导出 Word',
    onClick,
  }),
  calculator: (onClick: () => void) => ({
    id: 'calculator',
    icon: <Calculator className="h-3.5 w-3.5" />,
    label: '金额计算器',
    onClick,
  }),
};
