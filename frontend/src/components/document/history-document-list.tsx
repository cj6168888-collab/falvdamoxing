import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  FileText, Search, Calendar, 
  Download, Eye, Trash2, MoreVertical, History,
  ArrowUpDown, CheckCircle2, FilePlus
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { EmptyState } from '@/components/common/empty-state';

export interface HistoryDocument {
  id: string;
  title: string;
  document_type: string;
  content: string;
  status: 'draft' | 'approved' | 'sent' | 'archived';
  version: number;
  created_at: string;
  updated_at: string;
  based_on_adversarial?: boolean;
  based_on_ai_analysis?: boolean;
  generation_context?: string;
  referenced_evidence?: unknown;
  modification_history?: Array<{
    feedback: string;
    timestamp: string;
    version: number;
    change_summary?: string;
  }>;
}

interface Props {
  documents: HistoryDocument[];
  onViewDocument: (doc: HistoryDocument) => void;
  onDownloadDocx: (docId: string) => void;
  onDownloadPdf: (docId: string) => void;
  onDeleteDocument: (docId: string) => void;
  isLoading?: boolean;
}

export function HistoryDocumentList({
  documents,
  onViewDocument,
  onDownloadDocx,
  onDownloadPdf,
  onDeleteDocument,
  isLoading = false,
}: Props) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  // 获取所有文书类型
  const documentTypes = [...new Set(documents.map(d => d.document_type))];

  // 筛选文档
  const filteredDocuments = documents.filter(doc => {
    // 搜索筛选
    const matchesSearch = 
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.document_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.generation_context || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    // 状态筛选
    const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
    
    // 类型筛选
    const matchesType = typeFilter === 'all' || doc.document_type === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // 排序文档
  const sortedDocuments = [...filteredDocuments].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
  });

  // 状态统计
  const statusCounts = {
    all: documents.length,
    draft: documents.filter(d => d.status === 'draft').length,
    approved: documents.filter(d => d.status === 'approved').length,
    sent: documents.filter(d => d.status === 'sent').length,
    archived: documents.filter(d => d.status === 'archived').length,
  };

  // 获取状态徽章
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <Badge variant="outline" className="text-amber-600 border-amber-600 bg-amber-50">草稿</Badge>;
      case 'approved':
        return <Badge className="bg-blue-500">已审批</Badge>;
      case 'sent':
        return <Badge className="bg-green-500">已发送</Badge>;
      case 'archived':
        return <Badge variant="secondary">已归档</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 获取文档图标颜色
  const getDocTypeColor = (type: string) => {
    if (type.includes('起诉') || type.includes('上诉')) return 'text-red-500';
    if (type.includes('答辩')) return 'text-blue-500';
    if (type.includes('函') || type.includes('律师')) return 'text-orange-500';
    if (type.includes('合同') || type.includes('协议')) return 'text-green-500';
    if (type.includes('证据')) return 'text-purple-500';
    return 'text-primary';
  };

  if (documents.length === 0 && !isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <History className="h-5 w-5" />
            历史生成文书
          </h3>
          <Badge variant="secondary">0 份</Badge>
        </div>
        <EmptyState
          title="暂无历史文书"
          description="生成第一份文书后，它将显示在这里供您查看和管理"
          icon={FilePlus}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <History className="h-5 w-5" />
          历史生成文书
        </h3>
        <Badge variant="secondary">{documents.length} 份</Badge>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-2">
        <Card 
          className={`cursor-pointer transition-all hover:shadow-md ${statusFilter === 'all' ? 'ring-2 ring-primary' : ''}`}
          onClick={() => setStatusFilter('all')}
        >
          <CardContent className="p-3">
            <div className="text-2xl font-bold">{statusCounts.all}</div>
            <div className="text-xs text-muted-foreground">全部文书</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all hover:shadow-md ${statusFilter === 'draft' ? 'ring-2 ring-amber-500' : ''}`}
          onClick={() => setStatusFilter('draft')}
        >
          <CardContent className="p-3">
            <div className="text-2xl font-bold text-amber-600">{statusCounts.draft}</div>
            <div className="text-xs text-muted-foreground">草稿</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all hover:shadow-md ${statusFilter === 'approved' ? 'ring-2 ring-blue-500' : ''}`}
          onClick={() => setStatusFilter('approved')}
        >
          <CardContent className="p-3">
            <div className="text-2xl font-bold text-blue-600">{statusCounts.approved}</div>
            <div className="text-xs text-muted-foreground">已审批</div>
          </CardContent>
        </Card>
        <Card 
          className={`cursor-pointer transition-all hover:shadow-md ${statusFilter === 'sent' ? 'ring-2 ring-green-500' : ''}`}
          onClick={() => setStatusFilter('sent')}
        >
          <CardContent className="p-3">
            <div className="text-2xl font-bold text-green-600">{statusCounts.sent}</div>
            <div className="text-xs text-muted-foreground">已发送</div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="搜索文书标题或内容..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="h-10 px-3 rounded-md border border-input bg-background text-sm"
        >
          <option value="all">全部类型</option>
          {documentTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
        >
          <ArrowUpDown className="h-4 w-4 mr-1" />
          {sortOrder === 'desc' ? '最新优先' : '最早优先'}
        </Button>
      </div>

      {/* 文档列表 */}
      <div className="space-y-2">
        {sortedDocuments.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">未找到匹配的文书</p>
            </CardContent>
          </Card>
        ) : (
          sortedDocuments.map((doc) => (
            <Card 
              key={doc.id} 
              className="hover:shadow-md transition-all cursor-pointer group"
              onClick={() => onViewDocument(doc)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className={`mt-0.5 rounded-lg bg-primary/10 p-2 ${getDocTypeColor(doc.document_type)}`}>
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium truncate">{doc.title}</h4>
                        {getStatusBadge(doc.status)}
                        {doc.version > 1 && (
                          <Badge variant="outline" className="text-xs">
                            v{doc.version}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {doc.document_type}
                      </p>
                      {doc.generation_context && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {doc.generation_context}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(doc.created_at)}
                        </span>
                        {doc.based_on_adversarial && (
                          <span className="flex items-center gap-1 text-purple-600">
                            <CheckCircle2 className="h-3 w-3" />
                            对抗分析
                          </span>
                        )}
                        {doc.based_on_ai_analysis && (
                          <span className="flex items-center gap-1 text-blue-600">
                            <CheckCircle2 className="h-3 w-3" />
                            AI分析
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => onViewDocument(doc)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onDownloadDocx(doc.id)}>
                          <Download className="h-4 w-4 mr-2" />
                          下载 Word
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onDownloadPdf(doc.id)}>
                          <FileText className="h-4 w-4 mr-2" />
                          下载 PDF
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          className="text-red-600"
                          onClick={() => onDeleteDocument(doc.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
