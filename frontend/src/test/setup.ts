import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import type { SetupServerApi } from 'msw/node';
import axiosInstance from '@/api/client';

// Set test baseURL for axios
axiosInstance.defaults.baseURL = 'http://localhost:3000';

// Mock localStorage for zustand persist
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  value: true,
  writable: true,
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock IntersectionObserver
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | Document | null = null;
  readonly rootMargin = '0px';
  readonly thresholds: ReadonlyArray<number> = [];
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() { return []; }
  unobserve() {}
}
global.IntersectionObserver = MockIntersectionObserver;

// Mock ResizeObserver
class MockResizeObserver implements ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}
global.ResizeObserver = MockResizeObserver;

let server: SetupServerApi;

// MSW server setup
beforeAll(async () => {
  ({ server } = await import('./msw-server'));
  server.listen({
    onUnhandledRequest: (req) => {
      console.warn(`[MSW] Warning: intercepted unhandled request: ${req.method} ${req.url}`);
    },
  });
});
afterEach(() => {
  server?.resetHandlers();
  localStorage.clear();
});
afterAll(() => server?.close());
