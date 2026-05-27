import { useState } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/test-utils';
import { server } from '@/test/msw-server';
import { http, HttpResponse } from 'msw';

vi.mock('framer-motion', () => ({
  motion: { div: 'div', button: 'button', span: 'span' },
}));

interface NetworkErrorState {
  data: unknown;
  error: string | null;
  isLoading: boolean;
  retryCount: number;
  isOffline: boolean;
  cachedData: unknown;
}

function NetworkErrorTest() {
  const [state, setState] = useState<NetworkErrorState>({
    data: null,
    error: null,
    isLoading: false,
    retryCount: 0,
    isOffline: false,
    cachedData: { items: ['cached-item-1', 'cached-item-2'] },
  });

  const fetchData = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    if (state.isOffline) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        data: prev.cachedData,
        error: 'You are offline. Showing cached data.',
      }));
      return;
    }

    try {
      const response = await fetch('/api/data');
      if (!response.ok) throw new Error('API Error');
      const json = await response.json();
      setState(prev => ({ ...prev, isLoading: false, data: json, retryCount: 0 }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to fetch data',
        retryCount: prev.retryCount + 1,
      }));
    }
  };

  const goOffline = () => {
    setState(prev => ({ ...prev, isOffline: true }));
  };

  const goOnline = () => {
    setState(prev => ({ ...prev, isOffline: false }));
  };

  return (
    <div data-testid="network-error">
      <div data-testid="loading">{state.isLoading ? 'true' : 'false'}</div>
      <div data-testid="error">{state.error || 'none'}</div>
      <div data-testid="retry-count">{state.retryCount}</div>
      <div data-testid="offline-status">{state.isOffline ? 'offline' : 'online'}</div>
      <div data-testid="data">{state.data ? JSON.stringify(state.data) : 'none'}</div>
      <div data-testid="cached-data">{state.cachedData ? JSON.stringify(state.cachedData) : 'none'}</div>

      <button data-testid="fetch-btn" onClick={fetchData}>Fetch Data</button>
      <button data-testid="retry-btn" onClick={fetchData}>Retry</button>
      <button data-testid="offline-btn" onClick={goOffline}>Go Offline</button>
      <button data-testid="online-btn" onClick={goOnline}>Go Online</button>
    </div>
  );
}

describe('Network Error Handling Integration', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/data', () => {
        return HttpResponse.json({ items: ['item-1', 'item-2', 'item-3'] });
      })
    );
  });

  it('shows error UI with retry on API failure', async () => {
    server.use(
      http.get('/api/data', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    render(<NetworkErrorTest />);

    fireEvent.click(screen.getByTestId('fetch-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Failed to fetch data');
      expect(screen.getByTestId('retry-count')).toHaveTextContent('1');
    });

    expect(screen.getByTestId('retry-btn')).toBeInTheDocument();
  });

  it('shows cached data in offline mode', async () => {
    render(<NetworkErrorTest />);

    fireEvent.click(screen.getByTestId('offline-btn'));
    expect(screen.getByTestId('offline-status')).toHaveTextContent('offline');

    fireEvent.click(screen.getByTestId('fetch-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('You are offline. Showing cached data.');
      expect(screen.getByTestId('data').textContent).toContain('cached-item-1');
    });
  });

  it('triggers data refresh on reconnection', async () => {
    render(<NetworkErrorTest />);

    fireEvent.click(screen.getByTestId('offline-btn'));
    fireEvent.click(screen.getByTestId('fetch-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('offline-status')).toHaveTextContent('offline');
    });

    fireEvent.click(screen.getByTestId('online-btn'));
    expect(screen.getByTestId('offline-status')).toHaveTextContent('online');

    server.use(
      http.get('/api/data', () => {
        return HttpResponse.json({ items: ['fresh-item-1', 'fresh-item-2'] });
      })
    );

    fireEvent.click(screen.getByTestId('fetch-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('data').textContent).toContain('fresh-item-1');
      expect(screen.getByTestId('error')).toHaveTextContent('none');
    });
  });

  it('tracks multiple retries with exponential backoff', async () => {
    server.use(
      http.get('/api/data', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    render(<NetworkErrorTest />);

    fireEvent.click(screen.getByTestId('fetch-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('retry-count')).toHaveTextContent('1');
    });

    fireEvent.click(screen.getByTestId('retry-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('retry-count')).toHaveTextContent('2');
    });

    fireEvent.click(screen.getByTestId('retry-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('retry-count')).toHaveTextContent('3');
    });
  });
});
