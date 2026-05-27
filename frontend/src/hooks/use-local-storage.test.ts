import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { useLocalStorage } from '@/hooks/use-local-storage';
import { createElement, useState, useEffect } from 'react';

// Test component for useLocalStorage hook
function TestComponent({ storageKey, initialValue }: { storageKey: string; initialValue: unknown }) {
  const [value, setValue] = useLocalStorage(storageKey, initialValue);
  const [renderCount, setRenderCount] = useState(0);

  useEffect(() => {
    setRenderCount(c => c + 1);
  }, [value]);

  return (
    createElement('div', null,
      createElement('span', { 'data-testid': 'value' }, JSON.stringify(value)),
      createElement('span', { 'data-testid': 'render-count' }, renderCount),
      createElement('button', { onClick: () => setValue('new-value') }, 'Update'),
      createElement('button', { onClick: () => setValue(v => typeof v === 'string' ? v + '-appended' : v) }, 'Append')
    )
  );
}

describe('useLocalStorage Hook', () => {
  const storageKey = 'test-storage-key';

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('returns initial value when no stored value exists', () => {
    const { getByTestId } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    expect(getByTestId('value').textContent).toBe('"initial"');
  });

  it('returns stored value when exists in localStorage', () => {
    localStorage.setItem(storageKey, JSON.stringify('stored-value'));

    const { getByTestId } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    expect(getByTestId('value').textContent).toBe('"stored-value"');
  });

  it('updates localStorage when value changes', async () => {
    const { getByText } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    const updateButton = getByText('Update');
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(localStorage.getItem(storageKey)).toBe('"new-value"');
    });
  });

  it('handles functional updates correctly', async () => {
    const { getByText } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    const appendButton = getByText('Append');
    fireEvent.click(appendButton);

    await waitFor(() => {
      expect(localStorage.getItem(storageKey)).toBe('"initial-appended"');
    });
  });

  it('works with complex objects', () => {
    const complexValue = { nested: { data: [1, 2, 3] }, string: 'test' };
    localStorage.setItem(storageKey, JSON.stringify(complexValue));

    const { getByTestId } = render(
      createElement(TestComponent, { storageKey, initialValue: {} })
    );

    expect(getByTestId('value').textContent).toBe(JSON.stringify(complexValue));
  });

  it('handles null stored value gracefully', () => {
    localStorage.setItem(storageKey, 'null');

    const { getByTestId } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    // Should use initial value when stored value is null
    expect(getByTestId('value').textContent).toBe('"initial"');
  });

  it('triggers re-render on value change', async () => {
    const { getByTestId, getByText } = render(
      createElement(TestComponent, { storageKey, initialValue: 'initial' })
    );

    const initialRenderCount = parseInt(getByTestId('render-count').textContent || '0');

    const updateButton = getByText('Update');
    fireEvent.click(updateButton);

    await waitFor(() => {
      const newRenderCount = parseInt(getByTestId('render-count').textContent || '0');
      expect(newRenderCount).toBeGreaterThan(initialRenderCount);
    });
  });
});
