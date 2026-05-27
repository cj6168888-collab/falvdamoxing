const fs = require('fs');
const path = require('path');
const base = 'd:\\www\\法律大模型\\frontend\\src';

function writeFile(relPath, content) {
  const fullPath = path.join(base, relPath);
  const dir = path.dirname(fullPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(fullPath, content, 'utf-8');
  console.log('Fixed:', relPath);
}

// Fix chat-container.tsx
writeFile('components/chat/chat-container.tsx', `import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { useSendMessage } from '@/hooks/use-chat';

interface ChatContainerProps { caseId: string; }

export function ChatContainer({ caseId }: ChatContainerProps) {
  const [message, setMessage] = useState('');
  const send = useSendMessage(caseId);
  const handleSend = () => {
    if (message.trim()) {
      send.mutate(message.trim());
      setMessage('');
    }
  };
  return (
    <div className="flex flex-col h-[600px]">
      <CardContent className="flex-1 overflow-y-auto space-y-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm">您好！我是您的法律助手。请描述您的法律问题。</p>
          </CardContent>
        </Card>
      </CardContent>
      <div className="flex gap-2 p-4 border-t">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="输入您的问题..."
          className="flex-1"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <Button onClick={handleSend} disabled={send.isPending}>
          {send.isPending ? '发送中...' : '发送'}
        </Button>
      </div>
    </div>
  );
}
`);

// Fix clarification-panel.tsx
writeFile('components/chat/clarification-panel.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Props {
  questions: string[];
  onAnswer: (index: number, answer: string) => void;
  onSkip: () => void;
}

export function ClarificationPanel({ questions, onAnswer, onSkip }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>澄清问题</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {questions.map((q, i) => (
          <div key={i}>
            <p className="text-sm font-medium">{q}</p>
            <div className="flex gap-2 mt-1">
              <Button size="sm" onClick={() => onAnswer(i, '是')}>是</Button>
              <Button size="sm" variant="outline" onClick={() => onAnswer(i, '否')}>否</Button>
              <Button size="sm" variant="ghost" onClick={() => onAnswer(i, '不确定')}>不确定</Button>
            </div>
          </div>
        ))}
        <Button variant="ghost" size="sm" onClick={onSkip}>跳过直接分析</Button>
      </CardContent>
    </Card>
  );
}
`);

// Fix intent-display.tsx
writeFile('components/chat/intent-display.tsx', `import { Badge } from '@/components/ui/badge';

interface Props { intent: string; confidence: number; }

export function IntentDisplay({ intent, confidence }: Props) {
  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline">意图: {intent}</Badge>
      <span className="text-xs text-muted-foreground">{Math.round(confidence * 100)}% 置信度</span>
    </div>
  );
}
`);

// Fix deadline-interrupt.tsx
writeFile('components/common/deadline-interrupt.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useState } from 'react';

interface Props { onSubmit: (data: { type: string; date: string; description: string }) => void; }

export function DeadlineInterrupt({ onSubmit }: Props) {
  const [type, setType] = useState('');
  const [date, setDate] = useState('');
  const [description, setDescription] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>中断/顺延事件</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <select value={type} onChange={(e) => setType(e.target.value)} className="w-full rounded-md border p-2">
          <option value="">选择事件类型</option>
          <option value="催款函">催款函</option>
          <option value="起诉">起诉</option>
          <option value="和解协议">和解协议</option>
          <option value="调解">调解</option>
        </select>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="事件描述" />
        <Button onClick={() => onSubmit({ type, date, description })} disabled={!type || !date}>保存</Button>
      </CardContent>
    </Card>
  );
}
`);

// Fix party-form.tsx
writeFile('components/common/party-form.tsx', `import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Props { onSubmit: (data: Record<string, string>) => void; onCancel: () => void; }

export function PartyForm({ onSubmit, onCancel }: Props) {
  const [name, setName] = useState('');
  const [role, setRole] = useState('plaintiff');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  return (
    <Card>
      <CardHeader><CardTitle>添加当事人</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div><Label>姓名</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
        <div><Label>角色</Label>
          <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full rounded-md border p-2">
            <option value="plaintiff">原告</option>
            <option value="defendant">被告</option>
            <option value="third_party">第三人</option>
          </select>
        </div>
        <div><Label>电话</Label><Input value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
        <div><Label>地址</Label><Input value={address} onChange={(e) => setAddress(e.target.value)} /></div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>取消</Button>
          <Button onClick={() => onSubmit({ name, role, phone, address })}>保存</Button>
        </div>
      </CardContent>
    </Card>
  );
}
`);

// Fix quick-questions.tsx
writeFile('components/chat/quick-questions.tsx', `import { Button } from '@/components/ui/button';

interface Props { questions: string[]; onSelect: (q: string) => void; }

export function QuickQuestions({ questions, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q) => (
        <Button key={q} variant="outline" size="sm" onClick={() => onSelect(q)}>{q}</Button>
      ))}
    </div>
  );
}
`);

// Fix stream-response.tsx
writeFile('components/chat/stream-response.tsx', `import { useEffect, useState } from 'react';

interface Props { text: string; onComplete: () => void; }

export function StreamResponse({ text, onComplete }: Props) {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        onComplete();
      }
    }, 20);
    return () => clearInterval(interval);
  }, [text, onComplete]);
  return <p className="text-sm whitespace-pre-wrap">{displayed}<span className="animate-pulse">|</span></p>;
}
`);

// Fix chat-message.tsx
writeFile('components/chat/chat-message.tsx', `import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface Props { role: 'user' | 'assistant' | 'system'; content: string; timestamp: string; }

export function ChatMessage({ role, content, timestamp }: Props) {
  return (
    <div className={cn('flex', role === 'user' ? 'justify-end' : 'justify-start')}>
      <Card className={cn('max-w-[80%]', role === 'user' ? 'bg-primary text-primary-foreground' : '')}>
        <CardContent className="p-3">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
          <p className={cn('text-xs mt-1', role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
            {timestamp}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
`);

// Fix chat-sidebar.tsx
writeFile('components/chat/chat-sidebar.tsx', `import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  conversations: { id: string; title: string; updatedAt: string }[];
  onSelect: (id: string) => void;
}

export function ChatSidebar({ conversations, onSelect }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>对话历史</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        {conversations.map((c) => (
          <button key={c.id} onClick={() => onSelect(c.id)} className="w-full text-left p-2 rounded hover:bg-muted">
            <p className="text-sm font-medium truncate">{c.title}</p>
            <p className="text-xs text-muted-foreground">{c.updatedAt}</p>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
`);

// Fix chat-input.tsx
writeFile('components/chat/chat-input.tsx', `import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';

interface Props { onSend: (message: string) => void; isLoading?: boolean; }

export function ChatInput({ onSend, isLoading }: Props) {
  const [message, setMessage] = useState('');
  const handleSend = () => {
    if (message.trim()) {
      onSend(message.trim());
      setMessage('');
    }
  };
  return (
    <div className="flex gap-2 p-4 border-t">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="输入您的问题..."
        className="flex-1"
        rows={2}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      <Button onClick={handleSend} disabled={isLoading} size="icon">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
`);

console.log('All chat components fixed!');
