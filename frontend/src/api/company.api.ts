import { useQuery } from '@tanstack/react-query';
import axiosInstance, { ServerError } from '@/api/client';

const COMPANY_INFO_UNCONFIGURED_MESSAGE = '企业工商信息服务未配置，请先在 API Key 设置中配置企业信息服务';

export class CompanyInfoUnavailableError extends Error {
  constructor(message = COMPANY_INFO_UNCONFIGURED_MESSAGE) {
    super(message);
    this.name = 'CompanyInfoUnavailableError';
  }
}

export function isCompanyInfoUnavailableError(error: unknown): error is CompanyInfoUnavailableError {
  return error instanceof CompanyInfoUnavailableError;
}

function normalizeCompanyInfoError(error: unknown): never {
  if (
    error instanceof ServerError &&
    error.status === 503 &&
    typeof error.message === 'string' &&
    error.message.includes('COMPANY_INFO_API')
  ) {
    throw new CompanyInfoUnavailableError();
  }

  throw error;
}

async function getCompanyInfo(companyName: string) {
  try {
    const response = await axiosInstance.get(`/api/company-info/${encodeURIComponent(companyName)}`);
    return response.data;
  } catch (error) {
    normalizeCompanyInfoError(error);
  }
}

export function useCompanyInfo(companyName: string) {
  return useQuery({
    queryKey: ['company-info', companyName],
    queryFn: () => getCompanyInfo(companyName),
    enabled: !!companyName,
  });
}

export async function searchCompany(keyword: string) {
  try {
    const response = await axiosInstance.get('/api/company-info/search', { params: { keyword } });
    return response.data;
  } catch (error) {
    normalizeCompanyInfoError(error);
  }
}
