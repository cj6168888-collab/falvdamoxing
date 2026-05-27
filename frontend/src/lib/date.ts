import { format, formatDistanceToNow, formatRelative, differenceInDays, isToday, isTomorrow, isYesterday, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function formatDate(date: string | Date, formatStr: string): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr, { locale: zhCN });
}

export function formatRelativeToNow(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true, locale: zhCN });
}

export function formatRelativeDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatRelative(dateObj, new Date(), { locale: zhCN });
}

export function daysUntil(date: string | Date): number {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return differenceInDays(dateObj, new Date());
}

export function isDateToday(date: string | Date): boolean {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return isToday(dateObj);
}

export function isDateTomorrow(date: string | Date): boolean {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return isTomorrow(dateObj);
}

export function isDateYesterday(date: string | Date): boolean {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return isYesterday(dateObj);
}

export function formatChineseDate(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'yyyy 年 M 月 d 日', { locale: zhCN });
}

export function formatChineseDateTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'yyyy 年 M 月 d 日 HH:mm', { locale: zhCN });
}

export function formatChineseWeekday(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'EEEE', { locale: zhCN });
}
