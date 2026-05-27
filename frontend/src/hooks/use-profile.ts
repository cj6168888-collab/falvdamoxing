import { useProfile } from '@/api/profile.api';

export function useCaseProfile(caseId: string) {
  const { data, isLoading, isError } = useProfile(caseId);

  return { profile: data, isLoading, isError };
}
