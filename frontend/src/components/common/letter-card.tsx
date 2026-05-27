import { Mail, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Letter } from '@/types/letter.types';
import { LETTER_TYPE_OPTIONS, DIRECTION_OPTIONS, MAIL_STATUS_OPTIONS, URGENT_LEVEL_OPTIONS } from '@/types/letter.types';

const getLabel = (options: Array<{ value: string; label: string }>, value: string) => {
  return options.find(o => o.value === value)?.label || value;
};

const getUrgentColor = (level: string) => {
  const opt = URGENT_LEVEL_OPTIONS.find(o => o.value === level);
  return opt?.color || 'bg-gray-500';
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

interface Props {
  letter: Letter;
  onClick: () => void;
}

export function LetterCard({ letter, onClick }: Props) {
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium text-base">{letter.title}</span>
            {letter.is_overdue && (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            )}
          </div>
          <div className="flex gap-1.5 flex-wrap justify-end">
            <Badge variant="outline" className="text-xs">
              {getLabel(DIRECTION_OPTIONS, letter.direction)}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {getLabel(LETTER_TYPE_OPTIONS, letter.letter_type)}
            </Badge>
            <Badge className={`text-xs text-white ${getUrgentColor(letter.urgent_level)}`}>
              {getLabel(URGENT_LEVEL_OPTIONS.map(o => ({ ...o, label: o.label })), letter.urgent_level)}
            </Badge>
            {letter.is_replied && (
              <Badge variant="default" className="text-xs">
                <CheckCircle className="h-3 w-3 mr-1" />已回复
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex gap-4">
            <span>邮寄: {getLabel(MAIL_STATUS_OPTIONS, letter.mail_status)}</span>
            {letter.deadline && (
              <span>截止: {formatDate(letter.deadline)}</span>
            )}
            {letter.days_until_deadline !== null && letter.days_until_deadline !== undefined && (
              <span className={letter.is_overdue ? 'text-red-500' : ''}>
                {letter.is_overdue ? `超期${letter.days_until_deadline}天` : `剩余${letter.days_until_deadline}天`}
              </span>
            )}
          </div>
          <span>{formatDate(letter.created_at)}</span>
        </div>
        {letter.content_summary && (
          <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{letter.content_summary}</p>
        )}
      </CardContent>
    </Card>
  );
}
