import { formatCurrency, formatNumber, formatPercentage, truncate, capitalize, getStatusColor } from '@/lib/format';

describe('formatCurrency', () => {
  it('formats positive amounts correctly', () => {
    expect(formatCurrency(500000)).toBe('¥500,000.00');
  });

  it('formats zero correctly', () => {
    expect(formatCurrency(0)).toBe('¥0.00');
  });

  it('formats negative amounts correctly', () => {
    expect(formatCurrency(-1000)).toBe('-¥1,000.00');
  });
});

describe('formatNumber', () => {
  it('formats integers correctly', () => {
    expect(formatNumber(1234567)).toBe('1,234,567');
  });

  it('formats zero correctly', () => {
    expect(formatNumber(0)).toBe('0');
  });
});

describe('formatPercentage', () => {
  it('formats decimal to percentage', () => {
    expect(formatPercentage(0.75)).toBe('75%');
  });

  it('formats zero correctly', () => {
    expect(formatPercentage(0)).toBe('0%');
  });

  it('formats one correctly', () => {
    expect(formatPercentage(1)).toBe('100%');
  });
});

describe('truncate', () => {
  it('truncates long strings', () => {
    expect(truncate('这是一段很长的文字', 5)).toBe('这是一段很...');
  });

  it('does not truncate short strings', () => {
    expect(truncate('短文字', 10)).toBe('短文字');
  });

  it('handles empty strings', () => {
    expect(truncate('', 5)).toBe('');
  });
});

describe('capitalize', () => {
  it('capitalizes first letter', () => {
    expect(capitalize('hello')).toBe('Hello');
  });

  it('handles empty strings', () => {
    expect(capitalize('')).toBe('');
  });

  it('handles single character', () => {
    expect(capitalize('a')).toBe('A');
  });
});

describe('getStatusColor', () => {
  it('returns green for completed', () => {
    expect(getStatusColor('completed')).toBe('green');
  });

  it('returns blue for in-progress', () => {
    expect(getStatusColor('in-progress')).toBe('blue');
  });

  it('returns red for urgent', () => {
    expect(getStatusColor('urgent')).toBe('red');
  });

  it('returns amber for warning', () => {
    expect(getStatusColor('warning')).toBe('amber');
  });

  it('returns gray for draft', () => {
    expect(getStatusColor('draft')).toBe('gray');
  });

  it('returns gray for closed', () => {
    expect(getStatusColor('closed')).toBe('gray');
  });

  it('returns gray for unknown status', () => {
    expect(getStatusColor('unknown')).toBe('gray');
  });
});
