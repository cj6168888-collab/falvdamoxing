import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { 
  ClarificationQuestion, 
  ClarificationOption,
  IntentResult,
  SuggestedAction,
  QuickAction
} from '@/types/chat-v2.types';
import { INTENT_LABELS, INTENT_COLORS } from '@/types/chat-v2.types';
import { HelpCircle, ChevronRight, Lightbulb, X } from 'lucide-react';

interface ClarificationPanelProps {
  questions: ClarificationQuestion[];
  currentIndex: number;
  onAnswer: (answer: string, option?: ClarificationOption) => void;
  onSkip: () => void;
  suggestedActions?: SuggestedAction[];
  intentResult?: IntentResult | null;
}

export function ClarificationPanel({
  questions,
  currentIndex,
  onAnswer,
  onSkip,
}: ClarificationPanelProps) {
  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;

  if (!currentQuestion) {
    return null;
  }

  return (
    <Card className="border-amber-200 bg-amber-50/50">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5 text-amber-600" />
            <span className="font-medium text-amber-900">需要更多信息</span>
          </div>
          <Badge variant="outline" className="text-amber-700 border-amber-300">
            {currentIndex + 1} / {questions.length}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="h-1.5 bg-amber-200 rounded-full mb-4 overflow-hidden">
          <div 
            className="h-full bg-amber-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Question */}
        <p className="text-sm text-gray-700 mb-1">{currentQuestion.question}</p>
        <p className="text-xs text-gray-500 mb-4">{currentQuestion.context}</p>

        {/* Options */}
        {currentQuestion.options && (
          <div className="grid gap-2">
            {currentQuestion.options.map((option) => (
              <button
                key={option.value}
                onClick={() => onAnswer(option.value, option)}
                className="flex items-center justify-between p-3 rounded-lg border border-amber-200 bg-white hover:bg-amber-50 hover:border-amber-400 transition-colors text-left"
              >
                <div>
                  <span className="font-medium">{option.label}</span>
                  {option.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{option.description}</p>
                  )}
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </button>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-amber-200">
          <Button variant="ghost" size="sm" onClick={onSkip} className="text-gray-600">
            <X className="h-4 w-4 mr-1" />
            跳过
          </Button>
          <span className="text-xs text-gray-500">按 Enter 继续</span>
        </div>
      </CardContent>
    </Card>
  );
}

// Intent Display Badge
interface IntentBadgeProps {
  intent: IntentResult;
  onActionClick?: (action: SuggestedAction) => void;
}

export function IntentBadge({ intent, onActionClick }: IntentBadgeProps) {
  const colorClass = INTENT_COLORS[intent.intent] || INTENT_COLORS.unknown;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge className={colorClass}>
        {INTENT_LABELS[intent.intent]}
        <span className="ml-1 opacity-70">
          {Math.round(intent.confidence * 100)}%
        </span>
      </Badge>

      {intent.suggestedActions && intent.suggestedActions.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {intent.suggestedActions.map((action) => (
            <Button
              key={action.id}
              variant="outline"
              size="sm"
              onClick={() => onActionClick?.(action)}
              className="h-auto py-1.5 text-xs"
            >
              {action.icon && <span className="mr-1">{action.icon}</span>}
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

// Suggested Actions Panel
interface SuggestedActionsPanelProps {
  actions: SuggestedAction[];
  onActionClick: (action: SuggestedAction) => void;
  intent: IntentResult | null;
}

export function SuggestedActionsPanel({
  actions,
  onActionClick,
}: SuggestedActionsPanelProps) {
  if (!actions.length) return null;

  return (
    <Card className="border-blue-100 bg-blue-50/50">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-900">建议操作</span>
        </div>
        <div className="grid gap-2">
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => onActionClick(action)}
              className="flex items-start gap-3 p-3 rounded-lg border border-blue-100 bg-white hover:bg-blue-50 hover:border-blue-300 transition-colors text-left"
            >
              {action.icon && (
                <span className="text-xl">{action.icon}</span>
              )}
              <div className="flex-1">
                <span className="font-medium text-sm">{action.label}</span>
                <p className="text-xs text-gray-500 mt-0.5">{action.description}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400 mt-1" />
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Quick Actions Bar
interface QuickActionsBarProps {
  actions: QuickAction[];
  onActionClick: (action: QuickAction) => void;
}

export function QuickActionsBar({ actions, onActionClick }: QuickActionsBarProps) {
  return (
    <div className="flex items-center gap-2 p-2 border-t bg-muted/30 overflow-x-auto">
      <span className="text-xs text-muted-foreground whitespace-nowrap">快捷操作:</span>
      {actions.map((action) => (
        <button
          key={action.id}
          onClick={() => onActionClick(action)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-background border text-xs hover:bg-muted transition-colors whitespace-nowrap"
        >
          <span>{action.icon}</span>
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  );
}

// Guided Mode Indicator
interface GuidedModeIndicatorProps {
  mode: 'normal' | 'guided' | 'clarification';
  onModeChange: (mode: 'normal' | 'guided' | 'clarification') => void;
}

export function GuidedModeIndicator({
  mode,
  onModeChange,
}: GuidedModeIndicatorProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
      {(['normal', 'guided', 'clarification'] as const).map((m) => (
        <button
          key={m}
          onClick={() => onModeChange(m)}
          className={`px-3 py-1 rounded text-xs transition-colors ${
            mode === m
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted-foreground/10'
          }`}
        >
          {m === 'normal' && '自由对话'}
          {m === 'guided' && '引导模式'}
          {m === 'clarification' && '澄清模式'}
        </button>
      ))}
    </div>
  );
}
