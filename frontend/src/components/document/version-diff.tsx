import { useMemo } from 'react';
import * as Diff from 'diff';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Plus, 
  Minus, 
  Equal,
  ChevronDown,
  ChevronRight,
  FileText,
  Clock
} from 'lucide-react';
import { useState } from 'react';

interface DocumentVersion {
  version: number;
  content: string;
  timestamp: string;
  author?: string;
  status?: 'draft' | 'review' | 'final';
}

interface VersionDiffProps {
  oldVersion: DocumentVersion;
  newVersion: DocumentVersion;
  onClose?: () => void;
}

export function VersionDiff({ oldVersion, newVersion, onClose }: VersionDiffProps) {
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('unified');

  const diffResult = useMemo(() => {
    return Diff.diffLines(oldVersion.content, newVersion.content);
  }, [oldVersion.content, newVersion.content]);

  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    let unchanged = 0;

    diffResult.forEach((part) => {
      const lines = part.value.split('\n').filter(l => l.trim()).length;
      if (part.added) {
        added += lines;
      } else if (part.removed) {
        removed += lines;
      } else {
        unchanged += lines;
      }
    });

    return { added, removed, unchanged };
  }, [diffResult]);

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className="h-full overflow-hidden">
      <CardHeader className="border-b bg-muted/50 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <CardTitle className="text-base">版本对比</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600 border-green-600 bg-green-50">
                <Plus className="h-3 w-3 mr-1" />+{stats.added}
              </Badge>
              <Badge variant="outline" className="text-red-600 border-red-600 bg-red-50">
                <Minus className="h-3 w-3 mr-1" />-{stats.removed}
              </Badge>
              <Badge variant="outline">
                <Equal className="h-3 w-3 mr-1" />{stats.unchanged}
              </Badge>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center border rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode('unified')}
                className={`px-2 py-1 text-xs ${viewMode === 'unified' ? 'bg-primary text-primary-foreground' : 'bg-background'}`}
              >
                统一
              </button>
              <button
                onClick={() => setViewMode('split')}
                className={`px-2 py-1 text-xs ${viewMode === 'split' ? 'bg-primary text-primary-foreground' : 'bg-background'}`}
              >
                并排
              </button>
            </div>
            {onClose && (
              <Button variant="outline" size="sm" onClick={onClose}>
                关闭
              </Button>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <span>v{oldVersion.version} ({formatDate(oldVersion.timestamp)})</span>
          <span>→</span>
          <span>v{newVersion.version} ({formatDate(newVersion.timestamp)})</span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {viewMode === 'unified' ? (
          <UnifiedDiffView diffResult={diffResult} />
        ) : (
          <SplitDiffView oldVersion={oldVersion} newVersion={newVersion} />
        )}
      </CardContent>
    </Card>
  );
}

interface DiffViewProps {
  diffResult: Diff.Change[];
}

function UnifiedDiffView({ diffResult }: DiffViewProps) {
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set());

  const toggleSection = (index: number) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="font-mono text-sm overflow-auto max-h-[600px]">
      {diffResult.map((part, index) => {
        const lines = part.value.split('\n').filter(l => l.trim() !== '' || part.value.includes('\n'));
        const isCollapsed = collapsedSections.has(index) && !part.added && !part.removed;
        const bgClass = part.added
          ? 'bg-green-50 border-l-4 border-green-500'
          : part.removed
          ? 'bg-red-50 border-l-4 border-red-500'
          : 'bg-background';

        if (lines.length > 10 && !part.added && !part.removed) {
          return (
            <div key={index}>
              <button
                onClick={() => toggleSection(index)}
                className="flex items-center gap-2 w-full px-4 py-2 text-xs text-muted-foreground hover:bg-muted/50"
              >
                {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                省略 {lines.length} 行未更改内容
              </button>
              {!isCollapsed && lines.map((line, lineIndex) => (
                <div key={`${index}-${lineIndex}`} className={`px-4 py-0.5 ${bgClass}`}>
                  <span className="inline-block w-12 text-right mr-4 text-muted-foreground select-none">
                    {lineIndex + 1}
                  </span>
                  <span className={part.added ? 'text-green-700' : part.removed ? 'text-red-700' : 'text-muted-foreground'}>
                    {part.added ? '+' : part.removed ? '-' : ' '}
                  </span>
                  <span>{line}</span>
                </div>
              ))}
            </div>
          );
        }

        return lines.map((line, lineIndex) => (
          <div key={`${index}-${lineIndex}`} className={`px-4 py-0.5 ${bgClass}`}>
            <span className="inline-block w-12 text-right mr-4 text-muted-foreground select-none">
              {lineIndex + 1}
            </span>
            <span className={part.added ? 'text-green-700' : part.removed ? 'text-red-700' : 'text-muted-foreground'}>
              {part.added ? '+' : part.removed ? '-' : ' '}
            </span>
            <span className={part.added ? 'text-green-900' : part.removed ? 'text-red-900' : ''}>
              {line}
            </span>
          </div>
        ));
      })}
    </div>
  );
}

interface SplitViewProps {
  oldVersion: DocumentVersion;
  newVersion: DocumentVersion;
}

function SplitDiffView({ oldVersion, newVersion }: SplitViewProps) {
  const oldLines = oldVersion.content.split('\n');
  const newLines = newVersion.content.split('\n');

  const diffResult = Diff.diffArrays(oldLines, newLines);

  return (
    <div className="grid grid-cols-2 divide-x overflow-auto max-h-[600px]">
      {/* Left panel - old version */}
      <div className="overflow-auto">
        <div className="sticky top-0 bg-muted/80 px-4 py-2 text-xs font-medium border-b flex items-center gap-2">
          <FileText className="h-4 w-4" />
          v{oldVersion.version} ({new Date(oldVersion.timestamp).toLocaleDateString()})
        </div>
        <div className="font-mono text-sm">
          {diffResult.map((part, partIndex) => {
            if (part.added) return null;
            return part.value.map((line, lineIndex) => (
              <div
                key={`old-${partIndex}-${lineIndex}`}
                className={`px-4 py-0.5 ${part.removed ? 'bg-red-50 text-red-700' : ''}`}
              >
                <span className="inline-block w-8 text-right mr-2 text-muted-foreground select-none text-xs">
                  {partIndex}-{lineIndex + 1}
                </span>
                <span>{line}</span>
              </div>
            ));
          })}
        </div>
      </div>

      {/* Right panel - new version */}
      <div className="overflow-auto">
        <div className="sticky top-0 bg-muted/80 px-4 py-2 text-xs font-medium border-b flex items-center gap-2">
          <FileText className="h-4 w-4" />
          v{newVersion.version} ({new Date(newVersion.timestamp).toLocaleDateString()})
        </div>
        <div className="font-mono text-sm">
          {diffResult.map((part, partIndex) => {
            if (part.removed) return null;
            return part.value.map((line, lineIndex) => (
              <div
                key={`new-${partIndex}-${lineIndex}`}
                className={`px-4 py-0.5 ${part.added ? 'bg-green-50 text-green-700' : ''}`}
              >
                <span className="inline-block w-8 text-right mr-2 text-muted-foreground select-none text-xs">
                  {partIndex}-{lineIndex + 1}
                </span>
                <span>{line}</span>
              </div>
            ));
          })}
        </div>
      </div>
    </div>
  );
}

// Version History Component
interface VersionHistoryProps {
  versions: DocumentVersion[];
  currentVersion: number;
  onSelect: (version: number) => void;
  onCompare: (v1: number, v2: number) => void;
}

export function VersionHistory({ versions, currentVersion, onSelect, onCompare }: VersionHistoryProps) {
  const [compareMode, setCompareMode] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);

  const handleVersionClick = (version: number) => {
    if (compareMode) {
      if (selectedVersions.includes(version)) {
        setSelectedVersions(selectedVersions.filter(v => v !== version));
      } else if (selectedVersions.length < 2) {
        const newSelected = [...selectedVersions, version].sort((a, b) => a - b);
        setSelectedVersions(newSelected);
        if (newSelected.length === 2) {
          onCompare(newSelected[0], newSelected[1]);
          setCompareMode(false);
          setSelectedVersions([]);
        }
      }
    } else {
      onSelect(version);
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <Card>
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <CardTitle className="text-base">版本历史</CardTitle>
          </div>
          <Button
            variant={compareMode ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setCompareMode(!compareMode);
              setSelectedVersions([]);
            }}
          >
            {compareMode ? '取消对比' : '对比版本'}
          </Button>
        </div>
        {compareMode && (
          <p className="text-xs text-muted-foreground mt-2">
            选择两个版本进行对比 (已选择 {selectedVersions.length}/2)
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-2">
        {versions
          .sort((a, b) => b.version - a.version)
          .map((version) => (
            <div
              key={version.version}
              onClick={() => handleVersionClick(version.version)}
              className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                version.version === currentVersion
                  ? 'border-primary bg-primary/5'
                  : selectedVersions.includes(version.version)
                  ? 'border-primary/50 bg-primary/10'
                  : 'hover:bg-muted/50'
              }`}
            >
              <div className="flex items-center gap-3">
                {compareMode && (
                  <div className={`w-4 h-4 rounded border ${
                    selectedVersions.includes(version.version)
                      ? 'bg-primary border-primary'
                      : 'border-muted-foreground'
                  }`} />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">v{version.version}</span>
                    {version.version === currentVersion && (
                      <Badge variant="secondary" className="text-xs">当前</Badge>
                    )}
                    {version.status && (
                      <Badge
                        variant={version.status === 'final' ? 'default' : 'outline'}
                        className="text-xs"
                      >
                        {version.status === 'draft' ? '草稿' : version.status === 'review' ? '审核中' : '定稿'}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{formatDate(version.timestamp)}</p>
                </div>
              </div>
              {!compareMode && version.version !== currentVersion && (
                <Button variant="ghost" size="sm" className="text-xs">
                  对比
                </Button>
              )}
            </div>
          ))}
      </CardContent>
    </Card>
  );
}
