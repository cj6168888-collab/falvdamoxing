// Use a relative path so Vite can proxy API calls to the backend.
export const API_BASE_URL = '';

// Timeout policy:
// - Regular APIs default to 5 minutes, enough for most requests.
// - Analysis and generation APIs can override this with a larger env value.
// - Streaming APIs manage their own session timeout separately.
export const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT ?? 300000);

// Disable frontend automatic retries by default.
// LLM analysis requests can be expensive, and backend async tasks already have
// their own retry mechanism when needed.
export const API_RETRY_COUNT = Number(import.meta.env.VITE_API_RETRY_COUNT ?? 0);

export const API_RETRY_DELAY_MS = Number(import.meta.env.VITE_API_RETRY_DELAY ?? 1000);

export const TOKEN_STORAGE_KEY = 'auth_token';

export const STREAMING_CONFIG = {
  // Max wait between chunks while streaming output.
  chunkTimeout: 30000,
  // Max duration for a complete streaming session.
  sessionTimeout: 1800000,
  // 0 means unlimited evidence count for full-case analysis.
  maxEvidencePerAnalysis: 0,
  // Number of evidence items per chunk when chunked analysis is enabled.
  evidenceChunkSize: 20,
  // Automatically split large cases for analysis.
  enableChunkedAnalysis: true,
};
