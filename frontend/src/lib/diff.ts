import { diffChars, diffWords, diffLines } from 'diff';

export interface DiffResult {
  value: string;
  added?: boolean;
  removed?: boolean;
}

export function getDiffText(oldText: string, newText: string, mode: 'chars' | 'words' | 'lines' = 'words'): DiffResult[] {
  switch (mode) {
    case 'chars':
      return diffChars(oldText, newText);
    case 'lines':
      return diffLines(oldText, newText);
    default:
      return diffWords(oldText, newText);
  }
}

export function hasDiff(oldText: string, newText: string): boolean {
  return oldText.trim() !== newText.trim();
}
