import { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Users,
  User,
  Plus,
  Trash2,
  Mic,
  Settings,
  ChevronDown,
  Check,
} from 'lucide-react';

// 预设角色类型
export type SpeakerRole = 'judge' | 'plaintiff_lawyer' | 'defendant_lawyer' | 'witness' | 'plaintiff' | 'defendant' | 'other';

export interface Speaker {
  id: string;
  name: string;
  role: SpeakerRole;
  color: string;
  isActive?: boolean;
  confidence?: number; // 识别参考 0-1
}

interface SpeakerConfig {
  label: string;
  color: string;
  icon: typeof Users;
  defaultName: string;
}

const SPEAKER_CONFIGS: Record<SpeakerRole, SpeakerConfig> = {
  judge: {
    label: '法官',
    color: '#ef4444', // 红色
    icon: Users,
    defaultName: '法官',
  },
  plaintiff_lawyer: {
    label: '原告律师',
    color: '#22c55e', // 绿色
    icon: User,
    defaultName: '原告律师',
  },
  defendant_lawyer: {
    label: '被告律师',
    color: '#3b82f6', // 蓝色
    icon: User,
    defaultName: '被告律师',
  },
  witness: {
    label: '证人',
    color: '#f59e0b', // 黄色
    icon: User,
    defaultName: '证人',
  },
  plaintiff: {
    label: '原告',
    color: '#10b981', // 翠绿色
    icon: User,
    defaultName: '原告',
  },
  defendant: {
    label: '被告',
    color: '#6366f1', // 靛蓝色
    icon: User,
    defaultName: '被告',
  },
  other: {
    label: '其他',
    color: '#6b7280', // 灰色
    icon: User,
    defaultName: '其他人员',
  },
};

interface SpeakerIdentifierProps {
  /** 当前发言文本 */
  currentText?: string;
  /** 当前发言的角色 */
  currentSpeaker?: string;
  /** 识别参考 */
  confidence?: number;
  /** 发言人们 */
  speakers?: Speaker[];
  /** 当前发言人 ID */
  activeSpeakerId?: string;
  /** 模式：auto（自动识别）/ manual（手动切换） */
  mode?: 'auto' | 'manual';
  /** 发言变化回调 */
  onSpeakerChange?: (speakerId: string) => void;
  /** 添加发言人回调 */
  onAddSpeaker?: (speaker: Speaker) => void;
  /** 删除发言人回调 */
  onRemoveSpeaker?: (speakerId: string) => void;
  /** 更新发言人回调 */
  onUpdateSpeaker?: (speaker: Speaker) => void;
  /** 是否显示设置 */
  showSettings?: boolean;
  /** 是否启用 */
  enabled?: boolean;
  /** 类名 */
  className?: string;
}

export function SpeakerIdentifier({
  currentText = '',
  currentSpeaker,
  confidence = 0,
  speakers = [],
  activeSpeakerId,
  mode = 'manual',
  onSpeakerChange,
  onAddSpeaker,
  onRemoveSpeaker,
  onUpdateSpeaker,
  showSettings = true,
  enabled = true,
  className = '',
}: SpeakerIdentifierProps) {
  const [speakerPopoverOpen, setSpeakerPopoverOpen] = useState(false);
  const [settingsPopoverOpen, setSettingsPopoverOpen] = useState(false);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  const [newSpeakerRole, setNewSpeakerRole] = useState<SpeakerRole>('other');
  const [confidenceThreshold, setConfidenceThreshold] = useState([0.6]);

  // 获取当前发言人的配置
  const getActiveSpeakerConfig = useCallback(() => {
    const speaker = speakers.find((s) => s.id === activeSpeakerId);
    if (speaker) {
      return SPEAKER_CONFIGS[speaker.role];
    }
    return SPEAKER_CONFIGS.other;
  }, [speakers, activeSpeakerId]);

  const activeConfig = getActiveSpeakerConfig();

  // 添加新发言人
  const handleAddSpeaker = () => {
    if (!newSpeakerName.trim()) return;

    const newSpeaker: Speaker = {
      id: `speaker-${Date.now()}`,
      name: newSpeakerName.trim(),
      role: newSpeakerRole,
      color: SPEAKER_CONFIGS[newSpeakerRole].color,
    };

    onAddSpeaker?.(newSpeaker);
    setNewSpeakerName('');
    setNewSpeakerRole('other');
  };

  // 删除发言人
  const handleRemoveSpeaker = (speakerId: string) => {
    onRemoveSpeaker?.(speakerId);
  };

  // 选择发言人
  const handleSelectSpeaker = (speakerId: string) => {
    onSpeakerChange?.(speakerId);
    setSpeakerPopoverOpen(false);
  };

  // 快速角色切换
  const handleQuickRoleSwitch = (role: SpeakerRole) => {
    const speaker = speakers.find((s) => s.id === activeSpeakerId);
    if (speaker) {
      const updated: Speaker = {
        ...speaker,
        role,
        color: SPEAKER_CONFIGS[role].color,
      };
      onUpdateSpeaker?.(updated);
    }
  };

  // 获取识别参考等级
  const getConfidenceLevel = (conf: number) => {
    if (conf >= 0.8) return { label: '高', color: 'text-green-600' };
    if (conf >= 0.6) return { label: '中', color: 'text-yellow-600' };
    return { label: '低', color: 'text-red-600' };
  };

  const confidenceLevel = getConfidenceLevel(confidence);

  // 默认发言人列表
  const defaultSpeakers: Speaker[] = speakers.length > 0 ? speakers : [
    { id: 'judge', name: '法官', role: 'judge', color: SPEAKER_CONFIGS.judge.color },
    { id: 'plaintiff_lawyer', name: '原告律师', role: 'plaintiff_lawyer', color: SPEAKER_CONFIGS.plaintiff_lawyer.color },
    { id: 'defendant_lawyer', name: '被告律师', role: 'defendant_lawyer', color: SPEAKER_CONFIGS.defendant_lawyer.color },
    { id: 'witness', name: '证人', role: 'witness', color: SPEAKER_CONFIGS.witness.color },
  ];

  return (
    <Card className={className}>
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <CardTitle className="text-sm">发言人识别</CardTitle>
            {!enabled && (
              <Badge variant="outline" className="text-xs">
                已禁用
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* 识别参考显示 */}
            {confidence > 0 && (
              <Badge
                variant="outline"
                className={`text-xs ${confidenceLevel.color}`}
              >
                识别参考: {Math.round(confidence * 100)}%
              </Badge>
            )}

            {/* 当前发言人选择 */}
            <Popover open={speakerPopoverOpen} onOpenChange={setSpeakerPopoverOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1"
                  disabled={!enabled || mode === 'auto'}
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: activeConfig.color }}
                  />
                  <span className="max-w-[100px] truncate">
                    {currentSpeaker || activeConfig.label}
                  </span>
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 p-0" align="end">
                <div className="p-2">
                  <div className="text-xs font-medium text-muted-foreground mb-2">
                    选择发言人
                  </div>
                  <div className="space-y-1">
                    {defaultSpeakers.map((speaker) => (
                      <button
                        key={speaker.id}
                        onClick={() => handleSelectSpeaker(speaker.id)}
                        className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm hover:bg-muted transition-colors ${
                          speaker.id === activeSpeakerId ? 'bg-muted' : ''
                        }`}
                      >
                        <span
                          className="h-3 w-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: speaker.color }}
                        />
                        <span className="flex-1 text-left truncate">{speaker.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {SPEAKER_CONFIGS[speaker.role].label}
                        </span>
                        {speaker.id === activeSpeakerId && (
                          <Check className="h-4 w-4 text-primary" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            {/* 设置按钮 */}
            {showSettings && (
              <Popover open={settingsPopoverOpen} onOpenChange={setSettingsPopoverOpen}>
                <PopoverTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Settings className="h-4 w-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-72" align="end">
                  <div className="space-y-4">
                    <div className="text-sm font-medium">发言人设置</div>

                    {/* 添加新发言人 */}
                    <div className="space-y-2">
                      <Label className="text-xs">添加发言人</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="姓名"
                          value={newSpeakerName}
                          onChange={(e) => setNewSpeakerName(e.target.value)}
                          className="flex-1"
                        />
                        <Button size="sm" onClick={handleAddSpeaker}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <select
                        className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                        value={newSpeakerRole}
                        onChange={(e) => setNewSpeakerRole(e.target.value as SpeakerRole)}
                      >
                        {Object.entries(SPEAKER_CONFIGS).map(([key, config]) => (
                          <option key={key} value={key}>
                            {config.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* 识别参考阈值 */}
                    {mode === 'auto' && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label className="text-xs">识别参考阈值</Label>
                          <span className="text-xs text-muted-foreground">
                            {Math.round(confidenceThreshold[0] * 100)}%
                          </span>
                        </div>
                        <Slider
                          value={confidenceThreshold}
                          onValueChange={setConfidenceThreshold}
                          min={0}
                          max={1}
                          step={0.1}
                        />
                      </div>
                    )}

                    {/* 当前发言人快捷切换 */}
                    {activeSpeakerId && (
                      <div className="space-y-2">
                        <Label className="text-xs">快捷切换角色</Label>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(SPEAKER_CONFIGS)
                            .filter(([key]) => key !== 'other')
                            .map(([key, config]) => (
                              <Button
                                key={key}
                                variant="outline"
                                size="sm"
                                className="h-6 px-2 text-xs gap-1"
                                onClick={() => handleQuickRoleSwitch(key as SpeakerRole)}
                              >
                                <span
                                  className="h-2 w-2 rounded-full"
                                  style={{ backgroundColor: config.color }}
                                />
                                {config.label}
                              </Button>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* 已发言人们列表 */}
                    <div className="space-y-2">
                      <Label className="text-xs">已发言人们</Label>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {defaultSpeakers.map((speaker) => (
                          <div
                            key={speaker.id}
                            className="flex items-center justify-between py-1"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: speaker.color }}
                              />
                              <span className="text-sm truncate max-w-[120px]">
                                {speaker.name}
                              </span>
                            </div>
                            {speaker.id !== 'judge' && (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={() => handleRemoveSpeaker(speaker.id)}
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            )}
          </div>
        </div>

        {/* 发言内容预览 */}
        {currentText && (
          <div className="mt-2 p-2 rounded-md bg-muted/50 text-xs">
            <div className="flex items-center gap-2 mb-1">
              <Mic className="h-3 w-3 text-muted-foreground animate-pulse" />
              <span className="text-muted-foreground">当前发言:</span>
            </div>
            <p className="text-foreground line-clamp-2">{currentText}</p>
          </div>
        )}
      </CardHeader>
    </Card>
  );
}
