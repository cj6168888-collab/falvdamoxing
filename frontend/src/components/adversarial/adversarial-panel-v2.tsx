import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  ADVERSARIAL_MODES,
  type AdversarialMode,
  type CourtQuestion,
  type CrossExaminationTarget,
  type TTSConfig,
  type VoicePrintConfig,
  type EmergencyOverrideConfig,
} from '@/types/adversarial-v2.types';
import { LegalDisclaimer } from '@/components/common/legal-disclaimer';
import { 
  Volume2, 
  Mic, 
  UserCheck, 
  Play, 
  Pause, 
  SkipForward,
  Shield,
  Zap,
  Target,
} from 'lucide-react';

// Mode Selection Component
interface ModeSelectorProps {
  currentMode: AdversarialMode | null;
  onModeChange: (mode: AdversarialMode) => void;
}

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {ADVERSARIAL_MODES.map((mode) => (
        <Card
          key={mode.mode}
          className={`cursor-pointer transition-all ${
            currentMode === mode.mode 
              ? 'ring-2 ring-primary' 
              : 'hover:shadow-md'
          }`}
          onClick={() => onModeChange(mode.mode)}
        >
          <CardContent className="p-4 text-center">
            <div className="text-4xl mb-2">{mode.icon}</div>
            <h3 className="font-medium">{mode.label}</h3>
            <p className="text-xs text-muted-foreground mt-1">{mode.description}</p>
            {currentMode === mode.mode && (
              <Badge className="mt-2">当前模式</Badge>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Question Preparation Mode Component
interface QuestionPreparationProps {
  questions: CourtQuestion[];
  onAddQuestion: (q: CourtQuestion) => void;
  onUpdateQuestion: (q: CourtQuestion) => void;
  onDeleteQuestion: (id: string) => void;
}

export function QuestionPreparation({
  questions,
  onAddQuestion,
  onUpdateQuestion,
  onDeleteQuestion: _onDeleteQuestion,
}: QuestionPreparationProps) {
  const [newQuestion, setNewQuestion] = useState('');

  const handleAdd = () => {
    if (!newQuestion.trim()) return;
    onAddQuestion({
      id: Date.now().toString(),
      question: newQuestion,
      type: 'open',
      purpose: '',
      isPrepared: false,
      difficulty: 'medium',
    });
    setNewQuestion('');
  };

  const preparedCount = questions.filter(q => q.isPrepared).length;
  const progress = questions.length > 0 ? (preparedCount / questions.length) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Progress */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">准备进度</span>
            <span className="text-sm text-muted-foreground">
              {preparedCount} / {questions.length}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </CardContent>
      </Card>

      {/* Add Question */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          placeholder="输入问题..."
          className="flex-1 px-3 py-2 border rounded-md"
        />
        <Button onClick={handleAdd}>添加</Button>
      </div>

      {/* Question List */}
      <div className="space-y-2">
        {questions.map((q) => (
          <Card key={q.id}>
            <CardContent className="p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={q.type === 'closed' ? 'default' : 'outline'}>
                      {q.type === 'open' ? '开放式' : q.type === 'closed' ? '封闭式' : q.type === 'leading' ? '诱导式' : '假设式'}
                    </Badge>
                    <Badge variant={q.difficulty === 'easy' ? 'secondary' : q.difficulty === 'medium' ? 'outline' : 'destructive'}>
                      {q.difficulty === 'easy' ? '简单' : q.difficulty === 'medium' ? '中等' : '困难'}
                    </Badge>
                  </div>
                  <p className="mt-2">{q.question}</p>
                  {q.purpose && (
                    <p className="text-xs text-muted-foreground mt-1">
                      目的: {q.purpose}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant={q.isPrepared ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => onUpdateQuestion({ ...q, isPrepared: !q.isPrepared })}
                  >
                    {q.isPrepared ? '已准备' : '标记准备'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Cross Examination Mode Component
interface CrossExaminationProps {
  targets: CrossExaminationTarget[];
  activeTarget: string | null;
  onSelectTarget: (id: string) => void;
  onAddTarget: (t: CrossExaminationTarget) => void;
}

export function CrossExamination({
  targets,
  activeTarget,
  onSelectTarget,
  onAddTarget,
}: CrossExaminationProps) {
  const active = targets.find(t => t.id === activeTarget);

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Target List */}
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle className="text-base">询问对象</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {targets.map((target) => (
            <div
              key={target.id}
              onClick={() => onSelectTarget(target.id)}
              className={`p-3 rounded-lg border cursor-pointer ${
                activeTarget === target.id ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{target.name}</span>
                <Badge variant="outline">{target.role}</Badge>
              </div>
              {target.credibility !== undefined && (
                <div className="mt-2">
                  <div className="text-xs text-muted-foreground">可信度</div>
                  <Progress value={target.credibility} className="h-1 mt-1" />
                </div>
              )}
            </div>
          ))}
          <Button variant="outline" className="w-full" onClick={() => onAddTarget({
            id: Date.now().toString(),
            name: '新对象',
            role: 'witness',
            statements: [],
          })}>
            + 添加询问对象
          </Button>
        </CardContent>
      </Card>

      {/* Target Details */}
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle className="text-base">
            {active?.name || '选择一个询问对象'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {active ? (
            <div className="space-y-4">
              {/* Statements */}
              <div>
                <h4 className="text-sm font-medium mb-2">陈述记录</h4>
                <div className="space-y-2">
                  {active.statements.map((s) => (
                    <div key={s.id} className={`p-3 rounded-lg border ${
                      s.isFavorable ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                    }`}>
                      <div className="flex items-start justify-between">
                        <p className="text-sm">{s.statement}</p>
                        {s.canImpeach && (
                          <Badge variant="destructive" className="text-xs">可质疑</Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        来源: {s.source === 'deposition' ? '笔录' : s.source === 'hearing' ? '庭审' : '文书'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Vulnerabilities */}
              {active.vulnerabilities && active.vulnerabilities.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2 text-red-600">质证重点</h4>
                  <ul className="space-y-1">
                    {active.vulnerabilities.map((v, i) => (
                      <li key={i} className="text-sm flex items-center gap-2">
                        <Target className="h-3 w-3 text-red-500" />
                        {v}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              从左侧选择一个询问对象
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// TTS Component
interface TTSControlsProps {
  config: TTSConfig;
  onConfigChange: (config: TTSConfig) => void;
  onSpeak: (text: string) => void;
  isPlaying: boolean;
}

export function TTSControls({ config, onConfigChange, onSpeak, isPlaying }: TTSControlsProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Volume2 className="h-4 w-4" />
            语音播报
          </CardTitle>
          <Switch
            checked={config.enabled}
            onCheckedChange={(enabled) => onConfigChange({ ...config, enabled })}
          />
        </div>
      </CardHeader>
      {config.enabled && (
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => onSpeak('暂停')}
              disabled={!isPlaying}
            >
              <Pause className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => onSpeak('继续')}
            >
              <Play className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => onSpeak('跳过')}
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm">语速</Label>
              <span className="text-sm text-muted-foreground">{config.speed}x</span>
            </div>
            <Slider
              value={[config.speed * 50]}
              min={25}
              max={100}
              step={5}
              onValueChange={([v]) => onConfigChange({ ...config, speed: v / 50 })}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm">音调</Label>
              <span className="text-sm text-muted-foreground">{config.pitch.toFixed(1)}</span>
            </div>
            <Slider
              value={[config.pitch * 50]}
              min={25}
              max={100}
              step={5}
              onValueChange={([v]) => onConfigChange({ ...config, pitch: v / 50 })}
            />
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Voice Print Component
interface VoicePrintControlsProps {
  config: VoicePrintConfig;
  onConfigChange: (config: VoicePrintConfig) => void;
  speakers: Array<{ id: string; name: string; color: string }>;
  currentSpeaker: string | null;
}

export function VoicePrintControls({
  config,
  onConfigChange,
  speakers,
  currentSpeaker,
}: VoicePrintControlsProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <UserCheck className="h-4 w-4" />
            声纹识别
          </CardTitle>
          <Switch
            checked={config.enabled}
            onCheckedChange={(enabled) => onConfigChange({ ...config, enabled })}
          />
        </div>
      </CardHeader>
      {config.enabled && (
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Mic className={`h-4 w-4 ${currentSpeaker ? 'text-green-500 animate-pulse' : 'text-muted-foreground'}`} />
            <span className="text-sm">
              {currentSpeaker 
                ? `识别中: ${speakers.find(s => s.id === currentSpeaker)?.name || '未知'}`
                : '等待识别...'
              }
            </span>
          </div>

          {/* Speaker Indicators */}
          <div className="flex flex-wrap gap-2">
            {speakers.map((speaker) => (
              <Badge
                key={speaker.id}
                style={{ backgroundColor: speaker.color }}
                className="text-white"
              >
                {speaker.name}
              </Badge>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <Label className="text-sm">识别发言人</Label>
            <Switch
              checked={config.identifySpeakers}
              onCheckedChange={(identifySpeakers) => onConfigChange({ ...config, identifySpeakers })}
            />
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Emergency Override Component
interface EmergencyOverrideProps {
  config: EmergencyOverrideConfig;
  onConfigChange: (config: EmergencyOverrideConfig) => void;
  onTrigger: (type: string) => void;
}

export function EmergencyOverride({
  config,
  onConfigChange,
  onTrigger,
}: EmergencyOverrideProps) {
  return (
    <Card className="border-red-200 bg-red-50/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2 text-red-700">
            <Shield className="h-4 w-4" />
            紧急接管
          </CardTitle>
          <Switch
            checked={config.enabled}
            onCheckedChange={(enabled) => onConfigChange({ ...config, enabled })}
          />
        </div>
      </CardHeader>
      {config.enabled && (
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium">触发条件</h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.triggerConditions.speakerDetected}
                  onChange={(e) => onConfigChange({
                    ...config,
                    triggerConditions: { ...config.triggerConditions, speakerDetected: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">检测到新发言人</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.triggerConditions.keyEvidenceMentioned}
                  onChange={(e) => onConfigChange({
                    ...config,
                    triggerConditions: { ...config.triggerConditions, keyEvidenceMentioned: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">关键证据被提及</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.triggerConditions.hostileQuestion}
                  onChange={(e) => onConfigChange({
                    ...config,
                    triggerConditions: { ...config.triggerConditions, hostileQuestion: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">出现刁难性问题</span>
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-medium">自动动作</h4>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.autoActions.alertLawyer}
                  onChange={(e) => onConfigChange({
                    ...config,
                    autoActions: { ...config.autoActions, alertLawyer: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">通知律师</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.autoActions.showReminder}
                  onChange={(e) => onConfigChange({
                    ...config,
                    autoActions: { ...config.autoActions, showReminder: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">显示提醒</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.autoActions.voiceReminder}
                  onChange={(e) => onConfigChange({
                    ...config,
                    autoActions: { ...config.autoActions, voiceReminder: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">语音提醒</span>
              </label>
            </div>
          </div>

          <Button 
            variant="destructive" 
            className="w-full"
            onClick={() => onTrigger('manual')}
          >
            <Zap className="h-4 w-4 mr-2" />
            手动触发紧急接管
          </Button>
        </CardContent>
      )}
    </Card>
  );
}

// Main Adversarial Panel V2
interface AdversarialPanelV2Props {
  caseId: string;
}

export function AdversarialPanelV2({ caseId: _caseId }: AdversarialPanelV2Props) {
  const [activeMode, setActiveMode] = useState<AdversarialMode | null>(null);
  const [ttsConfig, setTtsConfig] = useState<TTSConfig>({
    enabled: false,
    voice: 'female',
    speed: 1,
    pitch: 1,
  });
  const [voiceConfig, setVoiceConfig] = useState<VoicePrintConfig>({
    enabled: false,
    speakerCount: 2,
    identifySpeakers: true,
  });
  const [emergencyConfig, setEmergencyConfig] = useState<EmergencyOverrideConfig>({
    enabled: true,
    triggerConditions: {
      speakerDetected: true,
      keyEvidenceMentioned: true,
      hostileQuestion: false,
      emotionalEscalation: false,
    },
    autoActions: {
      alertLawyer: true,
      showReminder: true,
      voiceReminder: false,
    },
  });
  const [questions, setQuestions] = useState<CourtQuestion[]>([]);
  const [targets, setTargets] = useState<CrossExaminationTarget[]>([]);
  const [activeTarget, setActiveTarget] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSpeaker] = useState<string | null>(null);

  const speakers = [
    { id: 'speaker-1', name: '我方', color: '#22c55e' },
    { id: 'speaker-2', name: '对方', color: '#ef4444' },
    { id: 'speaker-3', name: '法官', color: '#3b82f6' },
  ];

  const handleSpeak = (action: string) => {
    if (!ttsConfig.enabled) return;
    // TTS implementation
    console.log('TTS:', action);
    setIsPlaying(action !== '暂停');
  };

  return (
    <div className="space-y-6">
      {/* Mode Selection */}
      <div>
        <h2 className="text-lg font-bold mb-4">庭审辅助</h2>
        <LegalDisclaimer variant="adversarial" compact />
        <ModeSelector currentMode={activeMode} onModeChange={setActiveMode} />
      </div>

      {/* Mode Content */}
      {activeMode && (
        <Tabs defaultValue={activeMode}>
          <TabsList>
            <TabsTrigger value={activeMode}>
              {ADVERSARIAL_MODES.find(m => m.mode === activeMode)?.label}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value={activeMode} className="mt-4">
            {activeMode === 'question_preparation' && (
              <QuestionPreparation
                questions={questions}
                onAddQuestion={(q) => setQuestions([...questions, q])}
                onUpdateQuestion={(q) => setQuestions(questions.map(x => x.id === q.id ? q : x))}
                onDeleteQuestion={(id) => setQuestions(questions.filter(x => x.id !== id))}
              />
            )}
            
            {activeMode === 'cross_examination' && (
              <CrossExamination
                targets={targets}
                activeTarget={activeTarget}
                onSelectTarget={setActiveTarget}
                onAddTarget={(t) => setTargets([...targets, t])}
              />
            )}
            
            {activeMode === 'strategy_planning' && (
              <div className="text-center py-12 text-muted-foreground">
                策略规划模式开发中...
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* Controls Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <TTSControls
          config={ttsConfig}
          onConfigChange={setTtsConfig}
          onSpeak={handleSpeak}
          isPlaying={isPlaying}
        />
        
        <VoicePrintControls
          config={voiceConfig}
          onConfigChange={setVoiceConfig}
          speakers={speakers}
          currentSpeaker={currentSpeaker}
        />
        
        <EmergencyOverride
          config={emergencyConfig}
          onConfigChange={setEmergencyConfig}
          onTrigger={(type) => console.log('Emergency triggered:', type)}
        />
      </div>
    </div>
  );
}
