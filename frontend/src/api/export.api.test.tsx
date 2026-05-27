import axiosInstance from '@/api/client';
import {
  downloadExportFile,
  exportAdversarialAnalysis,
  exportCaseDocument,
} from './export.api';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('export api', () => {
  it('exports case documents and adversarial analyses', async () => {
    mockPost.mockResolvedValue({ data: { success: true, filename: 'export.md' } });

    await expect(
      exportCaseDocument(12, {
        document_type: 'Custom Claim',
        format: 'markdown',
        custom_content: '# claim',
      }),
    ).resolves.toEqual({ success: true, filename: 'export.md' });
    await expect(exportAdversarialAnalysis(34, 'markdown')).resolves.toEqual({
      success: true,
      filename: 'export.md',
    });
    await expect(exportAdversarialAnalysis(35, 'docx')).resolves.toEqual({
      success: true,
      filename: 'export.md',
    });
    await expect(exportAdversarialAnalysis(36, 'pdf')).resolves.toEqual({
      success: true,
      filename: 'export.md',
    });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/exports/document/12', {
      document_type: 'Custom Claim',
      format: 'markdown',
      custom_content: '# claim',
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/exports/adversarial-analysis/34?format=markdown');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/exports/adversarial-analysis/35?format=docx');
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/exports/adversarial-analysis/36?format=pdf');
  });

  it('downloads an exported file with the server filename', async () => {
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const createObjectURL = vi.fn(() => 'blob:export');
    const revokeObjectURL = vi.fn();

    Object.defineProperty(window.URL, 'createObjectURL', {
      configurable: true,
      value: createObjectURL,
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      configurable: true,
      value: revokeObjectURL,
    });
    mockGet.mockResolvedValue({ data: new Blob(['export']) });

    await downloadExportFile({
      success: true,
      download_url: '/api/exports/download/export.md',
      filename: 'export.md',
    });

    expect(mockGet).toHaveBeenCalledWith('/api/exports/download/export.md', { responseType: 'blob' });
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:export');
    expect(document.querySelector('a[download="export.md"]')).toBeNull();

    clickSpy.mockRestore();
  });

  it('rejects unsuccessful export payloads', async () => {
    await expect(downloadExportFile({ success: false, error: 'failed' })).rejects.toThrow('failed');
  });
});
