import { Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { AppShell } from './components/layout/app-shell';
import LoginPage from './pages/login';
import RegisterPage from './pages/register';
import ForgotPasswordPage from './pages/forgot-password';
import { CaseProvider } from './contexts/CaseContext';
import { useAuthStore } from './stores/auth.store';

const Dashboard = lazy(() => import('./pages/dashboard'));
const CasesList = lazy(() => import('./pages/cases'));
const CaseNew = lazy(() => import('./pages/cases/new'));
const CaseDetail = lazy(() => import('./pages/cases/[id]'));
const EvidenceGraph = lazy(() => import('./pages/evidence-graph/[caseId]'));
const EvidenceGuide = lazy(() => import('./pages/evidence-guide/[caseId]'));
const Timeline = lazy(() => import('./pages/timeline/[caseId]'));
const Documents = lazy(() => import('./pages/documents/[caseId]'));
const Adversarial = lazy(() => import('./pages/adversarial/[caseId]'));
const SeniorAnalysis = lazy(() => import('./pages/senior-analysis/[caseId]'));
const Hearing = lazy(() => import('./pages/hearing/[caseId]'));
const Progress = lazy(() => import('./pages/progress/[caseId]'));
const Execution = lazy(() => import('./pages/execution/[caseId]'));
const Appeal = lazy(() => import('./pages/appeal/[caseId]'));
const QA = lazy(() => import('./pages/qa/[caseId]'));
const Meeting = lazy(() => import('./pages/meeting/[caseId]'));
const Reminders = lazy(() => import('./pages/reminders'));
const AnalysisHistory = lazy(() => import('./pages/analysis-history/[caseId]'));
const SmartChat = lazy(() => import('./pages/smart-chat/[caseId]'));
const Insight = lazy(() => import('./pages/insight/[caseId]'));
const ApiKeyConfig = lazy(() => import('./pages/api-key-config'));
const TenantPage = lazy(() => import('./pages/tenant'));

function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        <p className="text-gray-500 dark:text-gray-400">加载中...</p>
      </div>
    </div>
  );
}

function AuthInitializer() {
  const initialize = useAuthStore((s) => s.initialize);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  useEffect(() => {
    if (!isInitialized) {
      initialize();
    }
  }, [initialize, isInitialized]);

  return null;
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);
  const accessToken = useAuthStore((s) => s.accessToken);

  if (!isInitialized) {
    return <LoadingFallback />;
  }

  if (!isAuthenticated && !accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <>
      <AuthInitializer />
      <CaseProvider>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="cases" element={<CasesList />} />
              <Route path="cases/new" element={<CaseNew />} />
              <Route path="cases/:id" element={<CaseDetail />} />
              <Route path="cases/:id/overview" element={<CaseDetail />} />
              <Route path="cases/:id/parties" element={<CaseDetail />} />
              <Route path="cases/:id/chat" element={<CaseDetail />} />
              <Route path="cases/:id/evidence" element={<CaseDetail />} />
              <Route path="cases/:id/documents" element={<CaseDetail />} />
              <Route path="cases/:id/analysis" element={<CaseDetail />} />
              <Route path="cases/:id/letters" element={<CaseDetail />} />
              <Route path="cases/:id/profile" element={<CaseDetail />} />
              <Route path="cases/:id/reports" element={<CaseDetail />} />
              <Route path="cases/:id/folder" element={<CaseDetail />} />
              <Route path="cases/:id/timeline" element={<CaseDetail />} />
              <Route path="cases/:id/execution" element={<CaseDetail />} />
              <Route path="cases/:id/appeal" element={<CaseDetail />} />
              <Route path="evidence-graph/:caseId" element={<EvidenceGraph />} />
              <Route path="evidence-guide/:caseId" element={<EvidenceGuide />} />
              <Route path="timeline/:caseId" element={<Timeline />} />
              <Route path="documents/:caseId" element={<Documents />} />
              <Route path="adversarial/:caseId" element={<Adversarial />} />
              <Route path="senior-analysis/:caseId" element={<SeniorAnalysis />} />
              <Route path="hearing/:caseId" element={<Hearing />} />
              <Route path="progress/:caseId" element={<Progress />} />
              <Route path="execution/:caseId" element={<Execution />} />
              <Route path="appeal/:caseId" element={<Appeal />} />
              <Route path="qa/:caseId" element={<QA />} />
              <Route path="meeting/:caseId" element={<Meeting />} />
              <Route path="reminders" element={<Reminders />} />
              <Route path="settings/api-keys" element={<ApiKeyConfig />} />
              <Route path="settings/tenant" element={<TenantPage />} />
              <Route path="analysis-history/:caseId" element={<AnalysisHistory />} />
              <Route path="smart-chat/:caseId" element={<SmartChat />} />
              <Route path="insight/:caseId" element={<Insight />} />
            </Route>
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Suspense>
      </CaseProvider>
    </>
  );
}

export default App;
