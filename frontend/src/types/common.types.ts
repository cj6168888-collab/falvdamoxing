// 通用类型

export type Theme = 'light' | 'dark' | 'system';

export interface SelectOption {
  label: string;
  value: string;
}

export interface ActionItem {
  label: string;
  icon?: string;
  onClick: () => void;
  variant?: 'default' | 'destructive' | 'outline';
  disabled?: boolean;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ElementType;
  count?: number;
}

export interface ConfirmationOptions {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
}
