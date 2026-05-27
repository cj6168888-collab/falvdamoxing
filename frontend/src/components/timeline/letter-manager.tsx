import { useState, useMemo, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { useLetterList, useDeleteLetter, useGenerateReply } from '@/hooks/use-letter';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus, Search, Filter, Trash2, Edit, Mail, Sparkles, AlertTriangle, X, ScanEye, Loader2 } from 'lucide-react';
import { LetterCard } from '@/components/common/letter-card';
import { LetterFormDialog } from '@/components/timeline/letter-form-dialog';
import type { Letter } from '@/types/letter.types';
import {
  LETTER_TYPE_OPTIONS,
  DIRECTION_OPTIONS,
  MAIL_STATUS_OPTIONS,
  URGENT_LEVEL_OPTIONS,
  REPLY_REQUIREMENT_OPTIONS,
} from '@/types/letter.types';
import { toast } from 'sonner';
import { discoverLetters, getDiscoveryStatus } from '@/api/letter.api';

const getLabel = (options: Array<{ value: string; label: string }>, value: string) => {
  return options.find(o => o.value === value)?.label || value;
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

interface Props {
  caseId: string;
}

export function LetterManager({ caseId }: Props) {
  const { data, isLoading, refetch } = useLetterList(caseId);
  const deleteMutation = useDeleteLetter();
  const generateReplyMutation = useGenerateReply();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterDirection, setFilterDirection] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterUrgency, setFilterUrgency] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  const [formOpen, setFormOpen] = useState(false);
  const [editingLetter, setEditingLetter] = useState<Letter | undefined>();
  const [detailLetter, setDetailLetter] = useState<Letter | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Letter | null>(null);
  const [replyDialog, setReplyDialog] = useState<Letter | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discoveryStatus, setDiscoveryStatus] = useState<{ correspondence_evidence: number; folder_letter_files: number; folder_total_files: number; auto_discovered_letters: number; manual_letters: number; total_letters: number; total_potential_letters: number; has_pending_discovery: boolean } | null>(null);

  useEffect(() => {
    if (caseId) {
      getDiscoveryStatus(caseId).then(setDiscoveryStatus).catch(() => {});
    }
  }, [caseId, data]);

  const filteredLetters = useMemo(() => {
    if (!data) return [];
    return data.filter((letter: Letter) => {
      if (searchTerm && !letter.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      if (filterDirection !== 'all' && letter.direction !== filterDirection) return false;
      if (filterType !== 'all' && letter.letter_type !== filterType) return false;
      if (filterStatus !== 'all' && letter.mail_status !== filterStatus) return false;
      if (filterUrgency !== 'all' && letter.urgent_level !== filterUrgency) return false;
      return true;
    });
  }, [data, searchTerm, filterDirection, filterType, filterStatus, filterUrgency]);

  const stats = useMemo(() => {
    if (!data) return { total: 0, incoming: 0, outgoing: 0, replied: 0, overdue: 0, pending: 0 };
    return {
      total: data.length,
      incoming: data.filter((l: Letter) => l.direction === 'incoming').length,
      outgoing: data.filter((l: Letter) => l.direction === 'outgoing').length,
      replied: data.filter((l: Letter) => l.is_replied).length,
      overdue: data.filter((l: Letter) => l.is_overdue).length,
      pending: data.filter((l: Letter) => !l.is_replied && l.reply_required === 'required').length,
    };
  }, [data]);

  const handleCreate = () => {
    setEditingLetter(undefined);
    setFormOpen(true);
  };

  const handleEdit = (letter: Letter) => {
    setEditingLetter(letter);
    setFormOpen(true);
  };

  const handleDelete = async (letter: Letter) => {
    try {
      await deleteMutation.mutateAsync({ caseId, letterId: letter.id.toString() });
      toast.success('函件已删除');
      setDeleteConfirm(null);
    } catch {
      toast.error('删除失败');
    }
  };

  const handleGenerateReply = async (letter: Letter) => {
    try {
      const res = await generateReplyMutation.mutateAsync(letter.id.toString());
      setReplyDialog({ ...letter, draft_reply: res.draft });
      toast.success('回复草稿已生成');
    } catch {
      toast.error('生成失败，请重试');
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await discoverLetters(caseId);
      if (res.discovered > 0) {
        toast.success(`AI发现 ${res.discovered} 封新函件`);
      } else if (res.skipped > 0) {
        toast.info(`所有函件已存在（${res.skipped} 封已关联）`);
      } else {
        toast.info('证据中未发现新函件');
      }
      const status = await getDiscoveryStatus(caseId);
      setDiscoveryStatus(status);
      refetch();
    } catch {
      toast.error('扫描失败');
    } finally {
      setDiscovering(false);
    }
  };

  const hasActiveFilters = filterDirection !== 'all' || filterType !== 'all' || filterStatus !== 'all' || filterUrgency !== 'all';

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-lg font-bold">函件管理</h2>
          <p className="text-sm text-muted-foreground mt-1">AI自动从证据中识别函件，智能追踪回复期限与邮寄状态</p>
          {discoveryStatus && discoveryStatus.total_potential_letters > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              证据中发现 {discoveryStatus.total_potential_letters} 封函件类文件
              （已关联 {discoveryStatus.auto_discovered_letters} 封，手动创建 {discoveryStatus.manual_letters} 封）
              {discoveryStatus.has_pending_discovery && (
                <span className="text-amber-600 ml-1">· 点击"AI发现函件"自动提取</span>
              )}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleDiscover} disabled={discovering}>
            {discovering ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ScanEye className="mr-2 h-4 w-4" />}
            AI发现函件
          </Button>
          <Button size="sm" onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />新建函件
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">总计</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.incoming}</div>
            <div className="text-xs text-muted-foreground">收件</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-green-600">{stats.outgoing}</div>
            <div className="text-xs text-muted-foreground">发件</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-orange-500">{stats.pending}</div>
            <div className="text-xs text-muted-foreground">待回复</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-red-500">{stats.overdue}</div>
            <div className="text-xs text-muted-foreground">已超期</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 text-center">
            <div className="text-2xl font-bold text-gray-500">{stats.replied}</div>
            <div className="text-xs text-muted-foreground">已回复</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="space-y-2">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索函件标题..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant={hasActiveFilters ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="mr-2 h-4 w-4" />筛选
            {hasActiveFilters && <span className="ml-1 h-2 w-2 rounded-full bg-white" />}
          </Button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 p-3 bg-muted/50 rounded-lg">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">收发方向</label>
              <Select value={filterDirection} onValueChange={setFilterDirection}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {DIRECTION_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">函件类型</label>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {LETTER_TYPE_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">邮寄状态</label>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {MAIL_STATUS_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">紧急程度</label>
              <Select value={filterUrgency} onValueChange={setFilterUrgency}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {URGENT_LEVEL_OPTIONS.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {hasActiveFilters && (
              <div className="col-span-2 md:col-span-4">
                <Button variant="ghost" size="sm" onClick={() => {
                  setFilterDirection('all');
                  setFilterType('all');
                  setFilterStatus('all');
                  setFilterUrgency('all');
                }}>
                  <X className="mr-1 h-3 w-3" />清除筛选
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Letter List */}
      {!filteredLetters.length ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Mail className="mx-auto h-12 w-12 text-muted-foreground/50 mb-3" />
            <p className="text-muted-foreground">
              {searchTerm || hasActiveFilters ? '没有匹配的函件' : '暂无函件，点击"新建函件"添加'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredLetters.map((letter: Letter) => (
            <div key={letter.id} className="group relative">
              <LetterCard letter={letter} onClick={() => setDetailLetter(letter)} />
              {/* Action buttons */}
              <div className="absolute top-3 right-3 hidden group-hover:flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={(e) => { e.stopPropagation(); handleEdit(letter); }}
                  title="编辑"
                >
                  <Edit className="h-3.5 w-3.5" />
                </Button>
                {letter.reply_required === 'required' && !letter.is_replied && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={(e) => { e.stopPropagation(); handleGenerateReply(letter); }}
                    title="AI生成回复"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-red-500 hover:text-red-600"
                  onClick={(e) => { e.stopPropagation(); setDeleteConfirm(letter); }}
                  title="删除"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form Dialog */}
      <LetterFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        caseId={caseId}
        letter={editingLetter}
        onSuccess={() => setFormOpen(false)}
      />

      {/* Detail Dialog */}
      {detailLetter && (
        <Dialog open={!!detailLetter} onOpenChange={() => setDetailLetter(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center gap-2">
                <DialogTitle>{detailLetter.title}</DialogTitle>
                {detailLetter.is_overdue && (
                  <Badge variant="destructive"><AlertTriangle className="h-3 w-3 mr-1" />超期</Badge>
                )}
              </div>
              <DialogDescription>
                {getLabel(DIRECTION_OPTIONS, detailLetter.direction)} · {getLabel(LETTER_TYPE_OPTIONS, detailLetter.letter_type)}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-xs text-muted-foreground">文号</span>
                  <p className="text-sm">{detailLetter.reference_number || '-'}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">发送方</span>
                  <p className="text-sm">{detailLetter.sender || '-'}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">接收方</span>
                  <p className="text-sm">{detailLetter.recipient || '-'}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">函件日期</span>
                  <p className="text-sm">{formatDate(detailLetter.letter_date)}</p>
                </div>
              </div>

              {/* Status Info */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <span className="text-xs text-muted-foreground">回复要求</span>
                  <p className="text-sm">{getLabel(REPLY_REQUIREMENT_OPTIONS, detailLetter.reply_required)}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">紧急程度</span>
                  <p className="text-sm">{getLabel(URGENT_LEVEL_OPTIONS, detailLetter.urgent_level)}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">邮寄状态</span>
                  <p className="text-sm">{getLabel(MAIL_STATUS_OPTIONS, detailLetter.mail_status)}</p>
                </div>
              </div>

              {/* Deadline Info */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <span className="text-xs text-muted-foreground">截止日期</span>
                  <p className="text-sm">{formatDate(detailLetter.deadline)}</p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">距截止天数</span>
                  <p className={`text-sm ${detailLetter.is_overdue ? 'text-red-500' : ''}`}>
                    {detailLetter.days_until_deadline !== null && detailLetter.days_until_deadline !== undefined
                      ? (detailLetter.is_overdue ? `超期${detailLetter.days_until_deadline}天` : `剩余${detailLetter.days_until_deadline}天`)
                      : '-'}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">是否已回复</span>
                  <p className="text-sm">{detailLetter.is_replied ? '是' : '否'}</p>
                </div>
              </div>

              {/* Content */}
              {detailLetter.content_summary && (
                <div>
                  <span className="text-xs text-muted-foreground">内容摘要</span>
                  <p className="text-sm mt-1">{detailLetter.content_summary}</p>
                </div>
              )}
              {detailLetter.key_demands && (
                <div>
                  <span className="text-xs text-muted-foreground">核心诉求</span>
                  <p className="text-sm mt-1">{detailLetter.key_demands}</p>
                </div>
              )}
              {detailLetter.legal_basis && (
                <div>
                  <span className="text-xs text-muted-foreground">法律依据</span>
                  <p className="text-sm mt-1">{detailLetter.legal_basis}</p>
                </div>
              )}

              {/* Mailing Info */}
              {(detailLetter.tracking_number || detailLetter.courier_company) && (
                <div className="p-3 bg-muted/50 rounded-lg">
                  <span className="text-xs text-muted-foreground">邮寄信息</span>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    {detailLetter.tracking_number && <p className="text-sm">运单号: {detailLetter.tracking_number}</p>}
                    {detailLetter.courier_company && <p className="text-sm">快递公司: {detailLetter.courier_company}</p>}
                    {detailLetter.mail_sent_date && <p className="text-sm">邮寄日期: {formatDate(detailLetter.mail_sent_date)}</p>}
                    {detailLetter.mail_delivered_date && <p className="text-sm">送达日期: {formatDate(detailLetter.mail_delivered_date)}</p>}
                  </div>
                </div>
              )}

              {/* Reply Info */}
              {detailLetter.draft_reply && (
                <div>
                  <span className="text-xs text-muted-foreground">回复草稿</span>
                  <Textarea value={detailLetter.draft_reply} readOnly className="mt-1" rows={5} />
                </div>
              )}
              {detailLetter.reply_content && (
                <div>
                  <span className="text-xs text-muted-foreground">回复内容</span>
                  <p className="text-sm mt-1">{detailLetter.reply_content}</p>
                </div>
              )}
              {detailLetter.reply_analysis && (
                <div>
                  <span className="text-xs text-muted-foreground">AI回函分析</span>
                  <p className="text-sm mt-1 whitespace-pre-wrap">{detailLetter.reply_analysis}</p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDetailLetter(null)}>关闭</Button>
              <Button onClick={() => { setDetailLetter(null); handleEdit(detailLetter); }}>
                <Edit className="mr-2 h-4 w-4" />编辑
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>确认删除</DialogTitle>
              <DialogDescription>
                确定要删除函件「{deleteConfirm.title}」吗？此操作不可撤销。
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteConfirm(null)}>取消</Button>
              <Button variant="destructive" onClick={() => handleDelete(deleteConfirm)}>
                删除
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Reply Dialog */}
      {replyDialog && (
        <Dialog open={!!replyDialog} onOpenChange={() => setReplyDialog(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>回复草稿 - {replyDialog.title}</DialogTitle>
              <DialogDescription>AI生成的回复草稿，请审阅后使用</DialogDescription>
            </DialogHeader>
            <Textarea
              value={replyDialog.draft_reply || ''}
              onChange={(e) => setReplyDialog({ ...replyDialog, draft_reply: e.target.value })}
              rows={15}
              className="font-mono text-sm"
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => setReplyDialog(null)}>关闭</Button>
              <Button onClick={() => {
                toast.success('草稿已保存');
                setReplyDialog(null);
              }}>
                保存草稿
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
