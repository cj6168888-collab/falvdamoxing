import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PanelLayout } from '@/components/layout/panel-layout';
import { VersionHistory, VersionDiff } from '@/components/document/version-diff';
import { useDocumentList } from '@/hooks/use-document';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { DocumentGenerator } from '@/components/document/document-generator';
import { DocumentEditor } from '@/components/document/document-editor';
import {
  Plus,
  FileText,
  History,
  Edit3,
  Download,
  MoreVertical,
  Trash2,
  Copy,
  ExternalLink
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { Document as CaseDocument } from '@/types/document.types';

interface DocumentVersion {
  version: number;
  content: string;
  timestamp: string;
  author?: string;
  status?: 'draft' | 'review' | 'final';
}

type DocumentListSource = CaseDocument & {
  versions?: DocumentVersion[];
};

type DocumentWithVersions = CaseDocument & {
  versions: DocumentVersion[];
};

interface Props {
  caseId: string;
}

export function DocumentList({ caseId }: Props) {
  const { data: documents, isLoading } = useDocumentList(caseId);
  const [selectedDocument, setSelectedDocument] = useState<DocumentWithVersions | null>(null);
  const [showGenerator, setShowGenerator] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'detail'>('list');
  const [compareVersions, setCompareVersions] = useState<{
    v1: DocumentVersion;
    v2: DocumentVersion;
  } | null>(null);

  if (isLoading) return <PageSkeleton />;

  if (!documents?.length && !showGenerator) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <EmptyState
          title="暂无文书"
          description="生成第一份文书，开始使用AI辅助撰写法律文书"
          actionLabel="生成文书"
          onAction={() => setShowGenerator(true)}
        />
      </div>
    );
  }

  const docs: DocumentWithVersions[] = ((documents || []) as DocumentListSource[]).map((d) => ({
    ...d,
    versions: d.versions || [{ version: d.version || 1, content: d.content || '', timestamp: d.updatedAt || d.createdAt || '', status: d.status }],
  }));

  const handleSelectDocument = (doc: DocumentWithVersions) => {
    setSelectedDocument(doc);
    setViewMode('detail');
  };

  const handleCompare = (v1: number, v2: number) => {
    if (!selectedDocument) return;
    const version1 = selectedDocument.versions.find(v => v.version === v1);
    const version2 = selectedDocument.versions.find(v => v.version === v2);
    if (version1 && version2) {
      setCompareVersions({ v1: version1, v2: version2 });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <Badge variant="outline" className="text-yellow-600 border-yellow-600">草稿</Badge>;
      case 'review':
        return <Badge variant="secondary" className="text-blue-600">审核中</Badge>;
      case 'final':
        return <Badge className="bg-green-600">定稿</Badge>;
      default:
        return null;
    }
  };

  // List view
  if (viewMode === 'list') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold">文书列表 ({docs.length})</h2>
            <Badge variant="secondary">{docs.reduce((acc, d) => acc + d.versions.length, 0)} 个版本</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setShowGenerator(true)}>
              <Plus className="mr-2 h-4 w-4" />
              新建文书
            </Button>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => (
            <Card key={doc.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleSelectDocument(doc as DocumentWithVersions)}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    <CardTitle className="text-base">{doc.title}</CardTitle>
                  </div>
                  {getStatusBadge(doc.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">{doc.type}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>v{doc.version} · {doc.versions.length} 个版本</span>
                    <span>{new Date(doc.updatedAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {showGenerator && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-background rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-auto">
              <DocumentGenerator
                caseId={caseId}
                onClose={() => setShowGenerator(false)}
                onGenerated={(doc) => {
                  setShowGenerator(false);
                  handleSelectDocument(doc as DocumentWithVersions);
                }}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  // Detail view with PanelLayout
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => setViewMode('list')}>
          返回列表
        </Button>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            导出
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Copy className="mr-2 h-4 w-4" />
                复制内容
              </DropdownMenuItem>
              <DropdownMenuItem>
                <ExternalLink className="mr-2 h-4 w-4" />
                导出Word
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600">
                <Trash2 className="mr-2 h-4 w-4" />
                删除文书
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {selectedDocument && (
        <PanelLayout
          left={
            <div className="p-4 space-y-4">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  {selectedDocument.title}
                  {getStatusBadge(selectedDocument.status)}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedDocument.type} · v{selectedDocument.version}
                </p>
              </div>
              <Tabs defaultValue="content">
                <TabsList>
                  <TabsTrigger value="content">
                    <Edit3 className="h-4 w-4 mr-1" />
                    内容
                  </TabsTrigger>
                  <TabsTrigger value="history">
                    <History className="h-4 w-4 mr-1" />
                    历史 ({selectedDocument.versions.length})
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="content" className="mt-4">
                  <DocumentEditor content={selectedDocument.content} onSave={(c) => console.log('Save:', c)} />
                </TabsContent>
                <TabsContent value="history" className="mt-4">
                  <VersionHistory
                    versions={selectedDocument.versions}
                    currentVersion={selectedDocument.version}
                    onSelect={(v) => console.log('Select version:', v)}
                    onCompare={handleCompare}
                  />
                </TabsContent>
              </Tabs>
            </div>
          }
          right={
            <div className="p-4">
              <VersionHistory
                versions={selectedDocument.versions}
                currentVersion={selectedDocument.version}
                onSelect={(v) => console.log('Select version:', v)}
                onCompare={handleCompare}
              />
            </div>
          }
          storageKey={`doc-layout-${selectedDocument.id}`}
        />
      )}

      {/* Version Diff Modal */}
      {compareVersions && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-8">
          <div className="bg-background rounded-lg shadow-lg w-full max-w-6xl h-[90vh] overflow-hidden">
            <VersionDiff
              oldVersion={compareVersions.v1}
              newVersion={compareVersions.v2}
              onClose={() => setCompareVersions(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
