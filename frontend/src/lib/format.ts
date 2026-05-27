export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(amount);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat('zh-CN').format(num);
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    completed: 'green',
    'in-progress': 'blue',
    urgent: 'red',
    warning: 'amber',
    draft: 'gray',
    closed: 'gray',
  };
  return colors[status] || 'gray';
}
