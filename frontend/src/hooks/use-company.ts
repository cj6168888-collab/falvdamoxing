import { useQuery } from '@tanstack/react-query';
import { useCompanyInfo, searchCompany } from '@/api/company.api';

export function useCompanySearch(companyName: string) {
  return useCompanyInfo(companyName);
}

export function useCompanySearchList(keyword: string) {
  return useQuery({
    queryKey: ['company-search', keyword],
    queryFn: () => searchCompany(keyword),
    enabled: !!keyword && keyword.length >= 2,
  });
}
