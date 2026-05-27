import { useState } from 'react';
import { useExecutionOverview, useExecutionRecords, useExecutionTasks, useExecutionAssets, useCreateExecutionRecord, useCreateExecutionTask, useCreateExecutionAsset, useDeleteExecutionTask, useUpdateExecutionTask, generateExecutionApplication } from '@/api/execution.api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Plus, FileText, MapPin, Sparkles, Trash2, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import type { ExecutionTask as TaskType, ExecutionAsset as AssetType } from '@/types/execution.types';

const STATUS_MAP: Record<string, string> = {
  pending: '待申请', applied: '已申请', accepted: '已受理', in_progress: '执行中',
  partially_completed: '部分执行', fully_completed: '执行完毕', terminated: '终止执行', suspended: '中止执行',
};
const PRIORITY_MAP: Record<string, string> = { high: '高', medium: '中', low: '低' };
const TASK_STATUS_MAP: Record<string, string> = { todo: '待办', in_progress: '进行中', completed: '已完成', cancelled: '已取消' };
const ASSET_STATUS_MAP: Record<string, string> = { discovered: '已发现', confirmed: '已确认', controlled: '已控制', disposed: '已处置' };

function getPriorityColor(p: string) {
  const c: Record<string, string> = { high: 'text-red-500', medium: 'text-amber-500', low: 'text-gray-500' };
  return c[p] || 'text-gray-500';
}

interface Props { caseId: string; }

export function ExecutionDashboard({ caseId }: Props) {
  const { data: overview, isLoading: loadingOverview } = useExecutionOverview(caseId);
  const { data: recordsData } = useExecutionRecords(caseId);
  const { data: tasksData } = useExecutionTasks(caseId);
  const { data: assetsData } = useExecutionAssets(caseId);

  const [recordDialog, setRecordDialog] = useState(false);
  const [taskDialog, setTaskDialog] = useState(false);
  const [assetDialog, setAssetDialog] = useState(false);
  const [recordForm, setRecordForm] = useState({ title: '', content: '', record_type: '', result: '', progress: 0 });
  const [taskForm, setTaskForm] = useState<Partial<TaskType>>({ title: '', priority: 'medium', status: 'todo' });
  const [assetForm, setAssetForm] = useState<Partial<AssetType>>({ asset_name: '', status: 'discovered' });

  const createRecord = useCreateExecutionRecord(caseId);
  const createTask = useCreateExecutionTask(caseId);
  const createAsset = useCreateExecutionAsset(caseId);
  const deleteTask = useDeleteExecutionTask(caseId);
  const updateTask = useUpdateExecutionTask(caseId);

  if (loadingOverview) return <PageSkeleton />;

  const records = recordsData?.records || [];
  const tasks = tasksData?.tasks || [];
  const assets = assetsData?.assets || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">执行跟踪</h1>
          <p className="text-sm text-muted-foreground mt-1">判决生效后的强制执行程序管理</p>
        </div>
        <Button variant="outline" onClick={() => generateExecutionApplication(caseId).catch(() => {})}>
          <Sparkles className="mr-2 h-4 w-4" />AI 生成执行申请书
        </Button>
      </div>

      {overview && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{overview.status ? STATUS_MAP[overview.status] || overview.status : '未开始'}</div><p className="text-xs text-muted-foreground">执行状态</p></CardContent></Card>
            <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{overview.progress}%</div><p className="text-xs text-muted-foreground">执行进度</p></CardContent></Card>
            <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{overview.total_tasks}</div><p className="text-xs text-muted-foreground">执行任务</p></CardContent></Card>
            <Card><CardContent className="pt-6"><div className="text-2xl font-bold">{overview.total_assets}</div><p className="text-xs text-muted-foreground">财产线索</p></CardContent></Card>
          </div>

          {overview.execution_case_number && (
            <Card>
              <CardHeader><CardTitle>执行基本信息</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                <div><span className="text-muted-foreground">执行案号:</span> {overview.execution_case_number}</div>
                {overview.execution_court && <div><span className="text-muted-foreground">执行法院:</span> {overview.execution_court}</div>}
                {overview.executor_name && <div><span className="text-muted-foreground">执行法官:</span> {overview.executor_name}</div>}
                {overview.execution_amount && <div><span className="text-muted-foreground">执行标的:</span> {overview.execution_amount}</div>}
                {overview.executed_amount && <div><span className="text-muted-foreground">已执行:</span> {overview.executed_amount}</div>}
                {overview.remaining_amount && <div><span className="text-muted-foreground">剩余:</span> {overview.remaining_amount}</div>}
              </CardContent>
            </Card>
          )}
        </>
      )}

      <Tabs defaultValue="tasks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="records">执行记录 ({records.length})</TabsTrigger>
          <TabsTrigger value="tasks">执行任务 ({tasks.length})</TabsTrigger>
          <TabsTrigger value="assets">财产线索 ({assets.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="records" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={recordDialog} onOpenChange={setRecordDialog}>
              <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加记录</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>添加执行记录</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2"><Label>标题</Label><Input value={recordForm.title} onChange={(e) => setRecordForm({ ...recordForm, title: e.target.value })} /></div>
                  <div className="space-y-2"><Label>记录类型</Label><Input value={recordForm.record_type} onChange={(e) => setRecordForm({ ...recordForm, record_type: e.target.value })} placeholder="例如：法院通知/财产查控" /></div>
                  <div className="space-y-2"><Label>详细内容</Label><Textarea value={recordForm.content} onChange={(e) => setRecordForm({ ...recordForm, content: e.target.value })} rows={4} /></div>
                  <div className="space-y-2"><Label>结果</Label><Textarea value={recordForm.result} onChange={(e) => setRecordForm({ ...recordForm, result: e.target.value })} rows={2} /></div>
                  <Button onClick={async () => { if (!recordForm.title) return; await createRecord.mutateAsync(recordForm); setRecordDialog(false); setRecordForm({ title: '', content: '', record_type: '', result: '', progress: 0 }); }} disabled={createRecord.isPending} className="w-full">{createRecord.isPending ? '创建中...' : '添加记录'}</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          {!records.length ? (
            <EmptyState title="暂无执行记录" description="记录执行过程中的每一次进展" />
          ) : (
            <div className="space-y-3">
              {records.map((r) => (
                <Card key={r.id}>
                  <CardContent className="p-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{r.title}</span>
                        {r.record_type && <Badge variant="outline">{r.record_type}</Badge>}
                      </div>
                      {r.content && <p className="text-sm text-muted-foreground">{r.content}</p>}
                      {r.result && <p className="text-sm"><span className="text-muted-foreground">结果:</span> {r.result}</p>}
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        {r.record_date && <span>{new Date(r.record_date).toLocaleDateString('zh-CN')}</span>}
                        {r.court_name && <span>法院: {r.court_name}</span>}
                        {r.judge_name && <span>法官: {r.judge_name}</span>}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={taskDialog} onOpenChange={setTaskDialog}>
              <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加任务</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>添加执行任务</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2"><Label>任务标题</Label><Input value={taskForm.title || ''} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} /></div>
                  <div className="space-y-2"><Label>描述</Label><Textarea value={taskForm.description || ''} onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} rows={2} /></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2"><Label>优先级</Label>
                      <Select value={taskForm.priority} onValueChange={(v) => setTaskForm({ ...taskForm, priority: v as TaskType['priority'] })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="high">高</SelectItem><SelectItem value="medium">中</SelectItem><SelectItem value="low">低</SelectItem></SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2"><Label>截止日期</Label><Input type="datetime-local" value={taskForm.due_date || ''} onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })} /></div>
                  </div>
                  <Button onClick={async () => { if (!taskForm.title) return; await createTask.mutateAsync(taskForm); setTaskDialog(false); setTaskForm({ title: '', priority: 'medium', status: 'todo' }); }} disabled={createTask.isPending} className="w-full">{createTask.isPending ? '创建中...' : '添加任务'}</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          {!tasks.length ? (
            <EmptyState title="暂无执行任务" description="创建任务来跟踪执行进度" />
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <Card key={task.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <button onClick={async () => {
                          const newStatus = task.status === 'todo' ? 'in_progress' : task.status === 'in_progress' ? 'completed' : task.status;
                          if (newStatus !== task.status) await updateTask.mutateAsync({ taskId: task.id, data: { status: newStatus } });
                        }} className="flex-shrink-0">
                          {task.status === 'completed' ? <CheckCircle2 className="h-5 w-5 text-green-500" /> :
                           task.status === 'in_progress' ? <Clock className="h-5 w-5 text-blue-500" /> :
                           <AlertCircle className="h-5 w-5 text-gray-400" />}
                        </button>
                        <div>
                          <span className={task.status === 'completed' ? 'line-through text-muted-foreground' : 'font-medium'}>{task.title}</span>
                          <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                            <span className={getPriorityColor(task.priority)}>{PRIORITY_MAP[task.priority]}</span>
                            <span>{TASK_STATUS_MAP[task.status]}</span>
                            {task.due_date && <span>截止: {new Date(task.due_date).toLocaleDateString('zh-CN')}</span>}
                          </div>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => deleteTask.mutate(task.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="assets" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={assetDialog} onOpenChange={setAssetDialog}>
              <DialogTrigger asChild><Button size="sm"><Plus className="mr-1 h-3 w-3" />添加财产线索</Button></DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>添加财产线索</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2"><Label>财产名称</Label><Input value={assetForm.asset_name || ''} onChange={(e) => setAssetForm({ ...assetForm, asset_name: e.target.value })} /></div>
                  <div className="space-y-2"><Label>财产类型</Label>
                    <Select value={assetForm.asset_type} onValueChange={(v) => setAssetForm({ ...assetForm, asset_type: v })}>
                      <SelectTrigger><SelectValue placeholder="选择类型" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bank_account">银行账户</SelectItem>
                        <SelectItem value="real_estate">房产</SelectItem>
                        <SelectItem value="vehicle">车辆</SelectItem>
                        <SelectItem value="equity">股权</SelectItem>
                        <SelectItem value="receivables">应收账款</SelectItem>
                        <SelectItem value="other">其他</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2"><Label>估值</Label><Input value={assetForm.estimated_value || ''} onChange={(e) => setAssetForm({ ...assetForm, estimated_value: e.target.value })} placeholder="例如：100万" /></div>
                  <div className="space-y-2"><Label>描述</Label><Textarea value={assetForm.description || ''} onChange={(e) => setAssetForm({ ...assetForm, description: e.target.value })} rows={2} /></div>
                  <Button onClick={async () => { if (!assetForm.asset_name) return; await createAsset.mutateAsync(assetForm); setAssetDialog(false); setAssetForm({ asset_name: '', status: 'discovered' }); }} disabled={createAsset.isPending} className="w-full">{createAsset.isPending ? '创建中...' : '添加财产线索'}</Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
          {!assets.length ? (
            <EmptyState title="暂无财产线索" description="添加被执行人的可供执行财产" />
          ) : (
            <div className="space-y-2">
              {assets.map((asset) => (
                <Card key={asset.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{asset.asset_name}</span>
                          {asset.asset_type && <Badge variant="outline">{asset.asset_type}</Badge>}
                        </div>
                        {asset.description && <p className="text-sm text-muted-foreground">{asset.description}</p>}
                        <div className="flex gap-4 text-xs text-muted-foreground">
                          {asset.estimated_value && <span>估值: {asset.estimated_value}</span>}
                          {asset.location && <span>位置: {asset.location}</span>}
                        </div>
                      </div>
                      <Badge variant={asset.status === 'controlled' ? 'default' : asset.status === 'disposed' ? 'secondary' : 'outline'}>
                        {ASSET_STATUS_MAP[asset.status] || asset.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
