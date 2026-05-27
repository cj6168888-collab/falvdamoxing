import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Plus, Send, FileText, Loader2, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

interface DebateMessage {
  id: string;
  role: 'user' | 'ai' | 'opponent';
  content: string;
  timestamp: string;
}

export function DebateStreamPanel({ caseId }: { caseId: string }) {
  const [messages, setMessages] = useState<DebateMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const userMsg: DebateMessage = { id: Date.now().toString(), role: 'user', content: input, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsStreaming(true);

    try {
      const response = await fetch(`/api/对抗性分析/case/${caseId}/debate-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: userMsg.content, debate_round: messages.length + 1 }),
      });

      if (response.ok) {
        const data = await response.json();
        const aiMsg: DebateMessage = {
          id: (Date.now() + 1).toString(),
          role: 'ai',
          content: data.response || data.content || data.message || 'AI 回复生成完成',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);
      }
    } catch {
      const errorMsg: DebateMessage = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'AI 回复生成失败，请稍后重试',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <Card>
      <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" />流式辩论</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {!messages.length && <p className="text-sm text-muted-foreground text-center py-8">输入你的辩论观点，AI 将模拟对方反驳并生成应对策略</p>}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                <div className="flex items-center gap-2 mb-1">
                  {msg.role === 'user' ? <Send className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                  <span className="text-xs opacity-70">{msg.role === 'user' ? '我方' : 'AI 分析'}</span>
                </div>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {isStreaming && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg p-3 bg-muted">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">AI 正在生成...</span>
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Textarea value={input} onChange={(e) => setInput(e.target.value)} placeholder="输入辩论观点..." rows={2} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }} />
          <Button onClick={handleSend} disabled={isStreaming || !input.trim()} className="self-end">{isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}</Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function ChecklistPanel({ caseId }: { caseId: string }) {
  const [checklist, setChecklist] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const loadChecklist = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/time-control/case/${caseId}/checklist`);
      if (res.ok) {
        const data = await res.json();
        setChecklist(data);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5" />律师检查清单</CardTitle>
          <Button variant="outline" size="sm" onClick={loadChecklist} disabled={loading}>{loading ? '加载中...' : '加载清单'}</Button>
        </div>
      </CardHeader>
      <CardContent>
        {!checklist ? (
          <p className="text-sm text-muted-foreground text-center py-8">点击"加载清单"获取律师级检查清单</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(checklist).map(([category, items]) => (
              <div key={category}>
                <h4 className="font-medium mb-2">{category}</h4>
                <div className="space-y-1">
                  {Array.isArray(items) ? items.map((item: string, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="h-4 w-4 rounded border border-gray-300" />
                      <span>{item}</span>
                    </div>
                  )) : <p className="text-sm text-muted-foreground">{String(items)}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ProofUploadPanel({ letterId }: { letterId: string }) {
  const [proofs, setProofs] = useState<Array<Record<string, unknown>>>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ delivery_method: '', tracking_number: '', delivery_date: '', recipient: '', notes: '' });

  const loadProofs = async () => {
    try {
      const res = await fetch(`/api/time-control/letters/${letterId}/proof`);
      if (res.ok) {
        const data = await res.json();
        setProofs(data.proofs || []);
      }
    } catch {
      // ignore
    }
  };

  const handleSubmit = async () => {
    try {
      const res = await fetch(`/api/time-control/letters/${letterId}/proof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setDialogOpen(false);
        setForm({ delivery_method: '', tracking_number: '', delivery_date: '', recipient: '', notes: '' });
        loadProofs();
      }
    } catch {
      // ignore
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" />送达证明</CardTitle>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (open) loadProofs(); }}>
            <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加证明</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>添加送达证明</DialogTitle></DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2"><Label>送达方式</Label><Input value={form.delivery_method} onChange={(e) => setForm({ ...form, delivery_method: e.target.value })} placeholder="例如：EMS快递/挂号信/直接送达" /></div>
                <div className="space-y-2"><Label>快递单号</Label><Input value={form.tracking_number} onChange={(e) => setForm({ ...form, tracking_number: e.target.value })} /></div>
                <div className="space-y-2"><Label>送达日期</Label><Input type="date" value={form.delivery_date} onChange={(e) => setForm({ ...form, delivery_date: e.target.value })} /></div>
                <div className="space-y-2"><Label>签收人</Label><Input value={form.recipient} onChange={(e) => setForm({ ...form, recipient: e.target.value })} /></div>
                <div className="space-y-2"><Label>备注</Label><Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} /></div>
                <Button onClick={handleSubmit} className="w-full">提交证明</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {!proofs.length ? (
          <p className="text-sm text-muted-foreground text-center py-8">暂无送达证明</p>
        ) : (
          <div className="space-y-3">
            {proofs.map((proof, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div>
                  <p className="font-medium">{String(proof.delivery_method || '未填写')}</p>
                  <p className="text-sm text-muted-foreground">
                    {proof.tracking_number ? `单号: ${String(proof.tracking_number)}` : ''}
                    {proof.delivery_date ? ` · 日期: ${String(proof.delivery_date)}` : ''}
                    {proof.recipient ? ` · 签收人: ${String(proof.recipient)}` : ''}
                  </p>
                </div>
                <Badge variant="outline">已送达</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AiReplyAnalysisPanel({ letterId }: { letterId: string }) {
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const analyzeReply = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/time-control/letters/${letterId}/ai-analyze-reply`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><AlertCircle className="h-5 w-5" />AI 分析回函</CardTitle>
          <Button variant="outline" size="sm" onClick={analyzeReply} disabled={loading}>{loading ? '分析中...' : 'AI 分析'}</Button>
        </div>
      </CardHeader>
      <CardContent>
        {!analysis ? (
          <p className="text-sm text-muted-foreground text-center py-8">点击"AI 分析"对回函进行智能分析</p>
        ) : (
          <div className="space-y-4">
            {analysis.summary ? <div><h4 className="font-medium mb-1">摘要</h4><p className="text-sm text-muted-foreground whitespace-pre-wrap">{String(analysis.summary)}</p></div> : null}
            {analysis.key_points ? <div><h4 className="font-medium mb-1">关键要点</h4><p className="text-sm text-muted-foreground whitespace-pre-wrap">{String(analysis.key_points)}</p></div> : null}
            {analysis.suggested_response ? <div><h4 className="font-medium mb-1">建议回复</h4><p className="text-sm text-muted-foreground whitespace-pre-wrap">{String(analysis.suggested_response)}</p></div> : null}
            {analysis.risk_assessment ? <div><h4 className="font-medium mb-1">风险评估</h4><p className="text-sm text-muted-foreground whitespace-pre-wrap">{String(analysis.risk_assessment)}</p></div> : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function MailTrackingPanel({ caseId }: { caseId: string }) {
  const [tracking, setTracking] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const loadTracking = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/time-control/case/${caseId}/mail-tracking`);
      if (res.ok) {
        const data = await res.json();
        setTracking(data);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2"><Clock className="h-5 w-5" />邮件跟踪</CardTitle>
          <Button variant="outline" size="sm" onClick={loadTracking} disabled={loading}>{loading ? '加载中...' : '刷新'}</Button>
        </div>
      </CardHeader>
      <CardContent>
        {!tracking ? (
          <p className="text-sm text-muted-foreground text-center py-8">点击"刷新"获取邮件跟踪信息</p>
        ) : (
          <div className="space-y-3">
            {tracking.total_letters !== undefined && (
              <div className="grid grid-cols-3 gap-4 text-center">
                <div><p className="text-2xl font-bold">{String(tracking.total_letters)}</p><p className="text-xs text-muted-foreground">总函件</p></div>
                {tracking.pending_replies !== undefined && <div><p className="text-2xl font-bold text-amber-500">{String(tracking.pending_replies)}</p><p className="text-xs text-muted-foreground">待回复</p></div>}
                {tracking.received_replies !== undefined && <div><p className="text-2xl font-bold text-green-500">{String(tracking.received_replies)}</p><p className="text-xs text-muted-foreground">已回复</p></div>}
              </div>
            )}
            {Array.isArray(tracking.letters) && tracking.letters.map((letter: Record<string, unknown>, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div>
                  <p className="font-medium">{String(letter.title || '未命名')}</p>
                  <p className="text-sm text-muted-foreground">{String(letter.direction || '')}{letter.sent_date ? ` · ${String(letter.sent_date)}` : ''}</p>
                </div>
                <Badge variant={letter.status === 'replied' ? 'default' : letter.status === 'pending' ? 'outline' : 'secondary'}>
                  {String(letter.status || 'unknown')}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
