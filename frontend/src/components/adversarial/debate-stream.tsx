/**
 * 模拟庭审流式辩论组件
 * 实现完整的对抗性分析辩论界面，包括：
 * - 多角色辩论（对手、我方、裁判、战略家）
 * - 实时轮询进度
 * - 用户参与辩论
 * - 战略建议输出
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  startDebateStream,
  getDebateProgress,
  continueDebate,
  type DebateProgress,
  type DebateRound,
  type DebateRequest,
} from '@/api/adversarial.api';
import {
  Play,
  RefreshCw,
  Send,
  Loader2,
  Scale,
  Target,
  MessageSquare,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BookOpen,
  FileText,
} from 'lucide-react';

interface DebateStreamPanelProps {
  caseId: string;
  opponentName?: string;
  onDebateComplete?: (report: string) => void;
}

// 角色图标和颜色配置
const SPEAKER_CONFIG = {
  '🔴 对手律师': { icon: '🔴', label: '对手律师', color: '#ef4444', bgColor: 'bg-red-50 border-red-200' },
  '🟢 我方律师': { icon: '🟢', label: '我方律师', color: '#22c55e', bgColor: 'bg-green-50 border-green-200' },
  '⚖️ 裁判': { icon: '⚖️', label: '裁判', color: '#3b82f6', bgColor: 'bg-blue-50 border-blue-200' },
  '🎯 战略家': { icon: '🎯', label: '战略家', color: '#a855f7', bgColor: 'bg-purple-50 border-purple-200' },
  '👤 用户': { icon: '👤', label: '用户', color: '#6b7280', bgColor: 'bg-gray-50 border-gray-200' },
  '🎯 AI 顾问': { icon: '🎯', label: 'AI 顾问', color: '#f59e0b', bgColor: 'bg-amber-50 border-amber-200' },
};

// 阶段配置
const DEBATE_STAGES = [
  { value: '协商', label: '协商阶段', icon: '🤝' },
  { value: '诉前准备', label: '诉前准备', icon: '📋' },
  { value: '诉讼', label: '诉讼阶段', icon: '⚖️' },
  { value: '审理', label: '审理阶段', icon: '🏛️' },
  { value: '上诉', label: '上诉阶段', icon: '📤' },
  { value: '执行', label: '执行阶段', icon: '💰' },
];

export function DebateStreamPanel({ caseId, opponentName, onDebateComplete }: DebateStreamPanelProps) {
  // 状态管理
  const [debateId, setDebateId] = useState<string | null>(null);
  const [progress, setProgress] = useState<DebateProgress | null>(null);
  const [userInput, setUserInput] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [activeTab, setActiveTab] = useState('debate');
  const [selectedStage, setSelectedStage] = useState('协商');
  const [showThinking, setShowThinking] = useState<Record<string, boolean>>({});

  const scrollRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [progress?.rounds, scrollToBottom]);

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // 启动辩论
  const handleStartDebate = async () => {
    if (!caseId || isStarting) return;

    setIsStarting(true);
    try {
      const requestData: Partial<DebateRequest> = {
        分析阶段: selectedStage,
        对手名称: opponentName,
      };

      const result = await startDebateStream(caseId, requestData);
      setDebateId(result.debate_id);
      setProgress({
        debate_id: result.debate_id,
        status: 'started',
        current_round: 0,
        rounds: [],
        current_thinking: {},
        final_report: null,
        started_at: new Date().toISOString(),
      });

      // 开始轮询
      startPolling(result.debate_id);
    } catch (error) {
      console.error('启动辩论失败:', error);
    } finally {
      setIsStarting(false);
    }
  };

  // 轮询辩论进度
  const startPolling = (id: string) => {
    setIsPolling(true);

    pollingRef.current = setInterval(async () => {
      try {
        const data = await getDebateProgress(id);
        setProgress(data);

        // 如果辩论完成，停止轮询
        if (data.status === 'completed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setIsPolling(false);
          setActiveTab('report');
          onDebateComplete?.(data.final_report || '');
        } else if (data.status === 'failed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setIsPolling(false);
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 2000); // 每2秒轮询一次
  };

  // 发送用户输入
  const handleSendMessage = async () => {
    if (!userInput.trim() || !debateId || isSending) return;

    setIsSending(true);
    const input = userInput;
    setUserInput('');

    try {
      await continueDebate(debateId, input);
      // 继续轮询以获取更新
      if (!isPolling && pollingRef.current === null) {
        startPolling(debateId);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setIsSending(false);
    }
  };

  // 重置辩论
  const handleReset = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    setDebateId(null);
    setProgress(null);
    setIsPolling(false);
    setActiveTab('debate');
  };

  // 切换思考过程显示
  const toggleThinking = (key: string) => {
    setShowThinking(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // 获取当前阶段进度
  const getProgressPercentage = () => {
    if (!progress) return 0;
    const totalRounds = Math.max(4, progress.current_round || progress.rounds.length);
    const completedRounds = progress.rounds.length;
    return Math.min((completedRounds / totalRounds) * 100, 100);
  };

  // 渲染单个辩论轮次
  const renderRound = (round: DebateRound, index: number) => {
    const config = SPEAKER_CONFIG[round.speaker as keyof typeof SPEAKER_CONFIG] || {
      icon: '💬',
      label: '未知',
      color: '#6b7280',
      bgColor: 'bg-gray-50',
    };

    return (
      <div key={`${round.round}-${index}`} className={`mb-4 ${config.bgColor} border rounded-lg p-4`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">{config.icon}</span>
            <span className="font-medium" style={{ color: config.color }}>{config.label}</span>
            <Badge variant="outline" className="text-xs">第 {round.round} 轮</Badge>
          </div>
          <span className="text-xs text-muted-foreground">{round.timestamp}</span>
        </div>

        {/* 思考过程 */}
        {round.thinking && (
          <div className="mb-2">
            <button
              onClick={() => toggleThinking(`${round.round}-${index}`)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {showThinking[`${round.round}-${index}`] ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              <Sparkles className="h-3 w-3" />
              思考过程
            </button>
            {showThinking[`${round.round}-${index}`] && (
              <p className="text-xs text-muted-foreground italic mt-1 pl-4 border-l-2 border-muted">
                {round.thinking}
              </p>
            )}
          </div>
        )}

        {/* 内容 */}
        <div className="prose prose-sm max-w-none">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{round.content}</p>
        </div>
      </div>
    );
  };

  // 渲染思考状态
  const renderThinkingState = () => {
    if (!progress || !Object.keys(progress.current_thinking).length) return null;

    return (
      <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <div className="flex-1">
          {Object.entries(progress.current_thinking).map(([key, value]) => (
            <p key={key} className="text-sm text-muted-foreground">{value}</p>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* 辩论控制栏 */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              模拟庭审辩论
            </CardTitle>
            <div className="flex items-center gap-2">
              {debateId && (
                <Badge variant={isPolling ? 'default' : 'secondary'}>
                  {isPolling ? '分析中...' : '已完成'}
                </Badge>
              )}
              {debateId && (
                <Button variant="outline" size="sm" onClick={handleReset}>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  重新开始
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 阶段选择 */}
          {!debateId && (
            <div className="space-y-2">
              <label className="text-sm font-medium">选择案件阶段</label>
              <div className="flex flex-wrap gap-2">
                {DEBATE_STAGES.map(stage => (
                  <Button
                    key={stage.value}
                    variant={selectedStage === stage.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedStage(stage.value)}
                  >
                    <span className="mr-1">{stage.icon}</span>
                    {stage.label}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* 进度条 */}
          {debateId && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">分析进度</span>
                <span>{Math.round(getProgressPercentage())}%</span>
              </div>
              <Progress value={getProgressPercentage()} className="h-2" />
            </div>
          )}

          {/* 启动按钮 */}
          {!debateId && (
            <Button
              className="w-full"
              size="lg"
              onClick={handleStartDebate}
              disabled={isStarting || !caseId}
            >
              {isStarting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  启动辩论分析...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  开始模拟庭审辩论
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* 辩论内容区 */}
      {debateId && progress && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="debate" className="gap-1">
              <MessageSquare className="h-4 w-4" />
              辩论过程
              {progress.rounds.length > 0 && (
                <Badge variant="secondary" className="ml-1">{progress.rounds.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="report" className="gap-1" disabled={!progress.final_report}>
              <FileText className="h-4 w-4" />
              战略报告
            </TabsTrigger>
          </TabsList>

          {/* 辩论过程标签 */}
          <TabsContent value="debate" className="mt-4">
            <Card>
              <CardContent className="p-0">
                {/* 辩论历史 */}
                <ScrollArea className="h-[500px] p-4" ref={scrollRef}>
                  {progress.rounds.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">正在初始化辩论...</p>
                      <p className="text-xs text-muted-foreground mt-2">
                        系统将模拟对手律师、我方律师、裁判和战略家四个角色进行对抗分析
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {progress.rounds.map((round, index) => renderRound(round, index))}
                    </div>
                  )}

                  {/* 当前思考状态 */}
                  {progress.status !== 'completed' && renderThinkingState()}
                  {progress.warning && (
                    <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
                      {progress.warning}
                    </div>
                  )}
                  {progress.status === 'failed' && (
                    <div className="mt-3 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                      {progress.error || '辩论生成失败，请检查模型服务配置后重试'}
                    </div>
                  )}
                </ScrollArea>

                <Separator />

                {/* 用户输入区 */}
                <div className="p-4 space-y-3">
                  <div className="flex gap-2">
                    <Textarea
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      placeholder="输入你的辩论观点或问题，AI将模拟对方反驳并生成应对策略..."
                      className="min-h-[80px]"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                    />
                    <Button
                      className="self-end"
                      onClick={handleSendMessage}
                      disabled={isSending || !userInput.trim()}
                    >
                      {isSending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    按 Enter 发送，Shift+Enter 换行
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 战略报告标签 */}
          <TabsContent value="report" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  战略总结报告
                </CardTitle>
              </CardHeader>
              <CardContent>
                {progress.final_report ? (
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap">{progress.final_report}</div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <AlertCircle className="h-8 w-8 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">报告生成中...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* 帮助信息 */}
      {!debateId && (
        <Card className="bg-muted/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <BookOpen className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-2 text-sm">
                <h4 className="font-medium">模拟庭审辩论说明</h4>
                <p className="text-muted-foreground">
                  本功能模拟真实的法庭对抗场景，通过AI多角色扮演进行对抗性分析：
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-1">
                  <li><span className="text-red-500">🔴 对手律师</span> - 从对方角度分析可能的攻击策略</li>
                  <li><span className="text-green-500">🟢 我方律师</span> - 制定防守反击策略</li>
                  <li><span className="text-blue-500">⚖️ 裁判</span> - 模拟法官视角评估论点</li>
                  <li><span className="text-purple-500">🎯 战略家</span> - 综合分析形成完整战略方案</li>
                </ul>
                <p className="text-muted-foreground">
                  您可以在辩论过程中随时输入观点或问题，AI将进行针对性分析。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// 辩论轮次时间线组件
export function DebateTimeline({ rounds }: { rounds: DebateRound[] }) {
  return (
    <div className="relative">
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
      <div className="space-y-4">
        {rounds.map((round, index) => {
          const config = SPEAKER_CONFIG[round.speaker as keyof typeof SPEAKER_CONFIG] || {
            icon: '💬',
            label: '未知',
            color: '#6b7280',
          };

          return (
            <div key={`timeline-${round.round}-${index}`} className="relative pl-10">
              <div
                className="absolute left-2 w-4 h-4 rounded-full border-2 border-background"
                style={{ backgroundColor: config.color }}
              />
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{config.icon} {config.label}</span>
                  <Badge variant="outline" className="text-xs">第 {round.round} 轮</Badge>
                </div>
                <p className="text-xs text-muted-foreground">{round.timestamp}</p>
                <p className="text-sm line-clamp-2">{round.content.substring(0, 100)}...</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 辩论状态卡片组件
export function DebateStatusCard({ progress }: { progress: DebateProgress | null }) {
  if (!progress) return null;

  const statusConfig = {
    started: { label: '已启动', color: 'bg-blue-500', textColor: 'text-blue-600' },
    in_progress: { label: '进行中', color: 'bg-yellow-500', textColor: 'text-yellow-600' },
    completed: { label: '已完成', color: 'bg-green-500', textColor: 'text-green-600' },
    failed: { label: '失败', color: 'bg-red-500', textColor: 'text-red-600' },
    not_found: { label: '未找到', color: 'bg-red-500', textColor: 'text-red-600' },
  };

  const config = statusConfig[progress.status as keyof typeof statusConfig] || statusConfig.not_found;

  return (
    <div className="flex items-center gap-3">
      <div className={`w-3 h-3 rounded-full ${config.color} ${progress.status === 'in_progress' ? 'animate-pulse' : ''}`} />
      <span className={`text-sm font-medium ${config.textColor}`}>{config.label}</span>
      <span className="text-sm text-muted-foreground">
        {progress.rounds.length > 0 && `已进行 ${progress.rounds.length} 轮`}
      </span>
    </div>
  );
}
