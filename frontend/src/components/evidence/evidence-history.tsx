import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  History,
  TrendingUp,
  TrendingDown,
  Equal,
  Calendar,
  BarChart3,
  CheckCircle2,
  AlertCircle,
  FileText,
  Target,
  ArrowRight,
} from 'lucide-react';

export interface EvidenceGapRecord {
  id: string;
  record_date: string;
  total_evidence: number;
  required_evidence: number;
  filled_gaps: number;
  remaining_gaps: number;
  completeness_score: number; // 0-100
  gaps: EvidenceGap[];
}

export interface EvidenceGap {
  id: string;
  evidence_type: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  status: 'open' | 'in_progress' | 'resolved';
  created_date: string;
  resolved_date?: string;
  related_case_issue?: string;
}

interface EvidenceHistoryComparisonProps {
  caseId: string;
  records: EvidenceGapRecord[];
  currentRecord?: EvidenceGapRecord;
  onRecordSelect?: (record: EvidenceGapRecord) => void;
  onViewDetail?: (recordId: string) => void;
}

// 辅助函数：计算两个记录之间的变化
function calculateChanges(
  oldRecord: EvidenceGapRecord,
  newRecord: EvidenceGapRecord
): {
  completenessDelta: number;
  filledGaps: string[];
  newGaps: string[];
  remainingGapsDelta: number;
} {
  const oldGapIds = new Set(oldRecord.gaps.map((g) => g.id));
  const newGapIds = new Set(newRecord.gaps.map((g) => g.id));

  const filledGaps = oldRecord.gaps
    .filter((g) => !newGapIds.has(g.id))
    .map((g) => g.description);

  const newGaps = newRecord.gaps
    .filter((g) => !oldGapIds.has(g.id))
    .map((g) => g.description);

  return {
    completenessDelta: newRecord.completeness_score - oldRecord.completeness_score,
    filledGaps,
    newGaps,
    remainingGapsDelta: newRecord.remaining_gaps - oldRecord.remaining_gaps,
  };
}

// 进度可视化组件
function CompletenessProgress({
  score,
  size = 'md',
  showLabel = true,
}: {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}) {
  const getColor = (s: number) => {
    if (s >= 80) return 'bg-green-500';
    if (s >= 60) return 'bg-yellow-500';
    if (s >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const heights = { sm: 'h-1.5', md: 'h-2.5', lg: 'h-4' };
  const textSizes = { sm: 'text-xs', md: 'text-sm', lg: 'text-base' };

  return (
    <div className="flex items-center gap-2">
      <div className={`flex-1 ${heights[size]} bg-muted rounded-full overflow-hidden`}>
        <div
          className={`${heights[size]} ${getColor(score)} transition-all duration-500`}
          style={{ width: `${score}%` }}
        />
      </div>
      {showLabel && (
        <span className={`${textSizes[size]} font-medium`}>{Math.round(score)}%</span>
      )}
    </div>
  );
}

// 缺口变更标记组件
function GapChangeTag({
  type,
  count,
}: {
  type: 'filled' | 'new' | 'remaining';
  count: number;
}) {
  if (count === 0) return null;

  const config = {
    filled: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      label: '已填补',
      className: 'bg-green-100 text-green-700 border-green-200',
    },
    new: {
      icon: <AlertCircle className="h-3 w-3" />,
      label: '新增',
      className: 'bg-red-100 text-red-700 border-red-200',
    },
    remaining: {
      icon: <AlertCircle className="h-3 w-3" />,
      label: '剩余',
      className: 'bg-amber-100 text-amber-700 border-amber-200',
    },
  };

  const { icon, label, className } = config[type];

  return (
    <Badge variant="outline" className={`${className} gap-1`}>
      {icon}
      {count > 1 && `${count} `}{label}
    </Badge>
  );
}

// 历史记录卡片组件
function HistoryRecordCard({
  record,
  isSelected,
  isCurrent,
  onSelect,
  onViewDetail,
}: {
  record: EvidenceGapRecord;
  isSelected: boolean;
  isCurrent: boolean;
  onSelect: () => void;
  onViewDetail: () => void;
}) {
  const date = new Date(record.record_date);
  const formattedDate = date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });

  return (
    <div
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        isSelected
          ? 'border-primary bg-primary/5'
          : isCurrent
          ? 'border-green-200 bg-green-50/50'
          : 'hover:bg-muted/50'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{formattedDate}</span>
          {isCurrent && (
            <Badge variant="secondary" className="text-xs">
              当前
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onViewDetail(); }}>
          查看详情
        </Button>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">完整度</span>
            <CompletenessProgress score={record.completeness_score} size="sm" />
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span>{record.total_evidence}</span>
            <span className="text-muted-foreground">份证据</span>
          </div>
          <div className="flex items-center gap-1">
            <Target className="h-4 w-4 text-muted-foreground" />
            <span>{record.required_evidence}</span>
            <span className="text-muted-foreground">份需补充</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <GapChangeTag type="filled" count={record.filled_gaps} />
          <GapChangeTag type="remaining" count={record.remaining_gaps} />
        </div>
      </div>
    </div>
  );
}

// 历史对比面板组件
function HistoryComparisonPanel({
  oldRecord,
  newRecord,
}: {
  oldRecord: EvidenceGapRecord;
  newRecord: EvidenceGapRecord;
}) {
  const changes = useMemo(
    () => calculateChanges(oldRecord, newRecord),
    [oldRecord, newRecord]
  );

  const formatDelta = (delta: number) => {
    const sign = delta > 0 ? '+' : '';
    return `${sign}${delta.toFixed(1)}`;
  };

  return (
    <div className="space-y-6">
      {/* 概览对比 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            概览对比
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{newRecord.total_evidence}</div>
              <div className="text-xs text-muted-foreground">证据总数</div>
              {newRecord.total_evidence !== oldRecord.total_evidence && (
                <div className="text-xs text-green-600 mt-1">
                  {formatDelta(newRecord.total_evidence - oldRecord.total_evidence)}
                </div>
              )}
            </div>

            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {newRecord.completeness_score}%
              </div>
              <div className="text-xs text-muted-foreground">完整度</div>
              <div
                className={`text-xs mt-1 ${
                  changes.completenessDelta >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatDelta(changes.completenessDelta)}%
              </div>
            </div>

            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{newRecord.filled_gaps}</div>
              <div className="text-xs text-muted-foreground">已填补</div>
              {changes.filledGaps.length > 0 && (
                <div className="text-xs text-green-600 mt-1">
                  +{changes.filledGaps.length}
                </div>
              )}
            </div>

            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="text-2xl font-bold text-amber-600">
                {newRecord.remaining_gaps}
              </div>
              <div className="text-xs text-muted-foreground">剩余缺口</div>
              {changes.remainingGapsDelta !== 0 && (
                <div
                  className={`text-xs mt-1 ${
                    changes.remainingGapsDelta < 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatDelta(changes.remainingGapsDelta)}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 趋势变化 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">趋势变化</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 完整度趋势 */}
          <div className="flex items-center gap-4">
            <div className="w-20 text-right">
              <div className="text-lg font-bold">{oldRecord.completeness_score}%</div>
              <div className="text-xs text-muted-foreground">之前</div>
            </div>
            <div className="flex-1 flex items-center gap-2">
              <Progress
                value={oldRecord.completeness_score}
                className="h-3 flex-1"
              />
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
              <Progress
                value={newRecord.completeness_score}
                className="h-3 flex-1"
              />
            </div>
            <div className="w-20">
              <div className="text-lg font-bold">{newRecord.completeness_score}%</div>
              <div className="text-xs text-muted-foreground">之后</div>
            </div>
          </div>

          {/* 变化趋势图标 */}
          <div className="flex items-center justify-center gap-2">
            {changes.completenessDelta > 0 ? (
              <Badge variant="secondary" className="gap-1 bg-green-100 text-green-700">
                <TrendingUp className="h-4 w-4" />
                完整度提升 {formatDelta(changes.completenessDelta)}%
              </Badge>
            ) : changes.completenessDelta < 0 ? (
              <Badge variant="secondary" className="gap-1 bg-red-100 text-red-700">
                <TrendingDown className="h-4 w-4" />
                完整度下降 {formatDelta(Math.abs(changes.completenessDelta))}%
              </Badge>
            ) : (
              <Badge variant="secondary" className="gap-1">
                <Equal className="h-4 w-4" />
                完整度无变化
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 缺口详情对比 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 已填补的缺口 */}
        <Card className="border-green-200">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-green-700">
              <CheckCircle2 className="h-5 w-5" />
              已填补的缺口 ({changes.filledGaps.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {changes.filledGaps.length > 0 ? (
              <ul className="space-y-2">
                {changes.filledGaps.map((gap, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 p-2 bg-green-50 rounded-lg text-sm"
                  >
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                无已填补的缺口
              </p>
            )}
          </CardContent>
        </Card>

        {/* 新增的缺口 */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertCircle className="h-5 w-5" />
              新增的缺口 ({changes.newGaps.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {changes.newGaps.length > 0 ? (
              <ul className="space-y-2">
                {changes.newGaps.map((gap, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 p-2 bg-red-50 rounded-lg text-sm"
                  >
                    <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                无新增缺口
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// 主组件：证据缺口历史对比
export function EvidenceHistoryComparison({
  caseId: _caseId,
  records,
  currentRecord,
  onRecordSelect,
  onViewDetail,
}: EvidenceHistoryComparisonProps) {
  const [selectedRecord, setSelectedRecord] = useState<EvidenceGapRecord | null>(
    records.length > 1 ? records[records.length - 2] : null
  );
  const [compareDialogOpen, setCompareDialogOpen] = useState(false);

  const handleRecordSelect = (record: EvidenceGapRecord) => {
    setSelectedRecord(record);
    onRecordSelect?.(record);
  };

  const handleCompare = () => {
    if (selectedRecord && currentRecord) {
      setCompareDialogOpen(true);
    }
  };

  // 按日期排序（最新的在前）
  const sortedRecords = useMemo(
    () => [...records].sort((a, b) => new Date(b.record_date).getTime() - new Date(a.record_date).getTime()),
    [records]
  );

  if (records.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <History className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">暂无历史记录</h3>
          <p className="text-sm text-muted-foreground">
            证据缺口诊断历史记录将在这里显示
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <History className="h-5 w-5" />
            证据缺口历史
          </h2>
          <p className="text-sm text-muted-foreground">
            共 {records.length} 条记录 · 点击选择对比基准
          </p>
        </div>
        {selectedRecord && currentRecord && (
          <Button onClick={handleCompare} className="gap-2">
            <BarChart3 className="h-4 w-4" />
            对比当前状态
          </Button>
        )}
      </div>

      {/* 历史记录列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 当前记录 */}
        {currentRecord && (
          <HistoryRecordCard
            record={currentRecord}
            isSelected={selectedRecord?.id === currentRecord.id}
            isCurrent={true}
            onSelect={() => handleRecordSelect(currentRecord)}
            onViewDetail={() => onViewDetail?.(currentRecord.id)}
          />
        )}

        {/* 历史记录 */}
        {sortedRecords
          .filter((r) => r.id !== currentRecord?.id)
          .map((record) => (
            <HistoryRecordCard
              key={record.id}
              record={record}
              isSelected={selectedRecord?.id === record.id}
              isCurrent={false}
              onSelect={() => handleRecordSelect(record)}
              onViewDetail={() => onViewDetail?.(record.id)}
            />
          ))}
      </div>

      {/* 完整度趋势图（简化版） */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            完整度趋势
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end justify-between gap-2 h-32 px-4">
            {sortedRecords.map((record) => {
              const height = `${record.completeness_score}%`;
              const isSelected = selectedRecord?.id === record.id;
              const isCurrent = currentRecord?.id === record.id;

              return (
                <div key={record.id} className="flex-1 flex flex-col items-center gap-2">
                  <div
                    className={`w-full max-w-12 rounded-t transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-primary'
                        : isCurrent
                        ? 'bg-green-500'
                        : 'bg-muted-foreground/30 hover:bg-muted-foreground/50'
                    }`}
                    style={{ height }}
                    onClick={() => handleRecordSelect(record)}
                    title={`${record.completeness_score}%`}
                  />
                  <span className="text-xs text-muted-foreground">
                    {new Date(record.record_date).toLocaleDateString('zh-CN', {
                      month: '2-digit',
                      day: '2-digit',
                    })}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex items-center justify-center gap-4 mt-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-primary" />
              <span>选中对比</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500" />
              <span>当前状态</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-muted-foreground/30" />
              <span>历史记录</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 对比对话框 */}
      <Dialog open={compareDialogOpen} onOpenChange={setCompareDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              证据缺口对比
              <span className="text-sm font-normal text-muted-foreground ml-2">
                {selectedRecord && new Date(selectedRecord.record_date).toLocaleDateString()} vs{' '}
                {currentRecord && new Date(currentRecord.record_date).toLocaleDateString()}
              </span>
            </DialogTitle>
          </DialogHeader>
          {selectedRecord && currentRecord && (
            <HistoryComparisonPanel oldRecord={selectedRecord} newRecord={currentRecord} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
