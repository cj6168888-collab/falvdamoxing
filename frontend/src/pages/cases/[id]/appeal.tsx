import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Upload, FileText, ArrowUpRight, Scale } from 'lucide-react';

interface AppealRecord {
  id: string | number;
  title?: string;
  court_name?: string;
  status?: string;
  overview?: string;
}

export default function CaseAppealPage() {
  const { id } = useParams<{ id: string }>();

  // Use identical logic / hooks but point to appeal endpoints
  // In reality, it should call `/api/appeal/case/${id}`
  const { data: appeals, isLoading } = useQuery({
    queryKey: ['case-appeal', id],
    queryFn: () => axiosInstance.get<AppealRecord[]>(`/api/appeal/case/${id}`).then(res => res.data).catch(() => []),
    enabled: !!id,
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2"><ArrowUpRight className="h-5 w-5 text-primary" />二审/上诉/再审跟进</h2>
          <p className="text-sm text-muted-foreground mt-1">若对一审判决不服，此处可管理上诉状生成及二审诉讼程序的跟踪记录</p>
        </div>
        <Button><ArrowUpRight className="h-4 w-4 mr-2" />发起上诉</Button>
      </div>

      {(!appeals || appeals.length === 0) ? (
        <Card className="border-dashed bg-muted/10">
          <CardContent className="h-64 flex flex-col items-center justify-center text-center">
            <Scale className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <h3 className="text-lg font-medium mb-1">未启动二审/再审程序</h3>
            <p className="text-muted-foreground text-sm max-w-sm">
              可通过 AI 提取一审判决的争议焦点，自动为您起草针对性的上诉状内容，或引入新的关键证据。
            </p>
            <div className="mt-6 flex gap-3">
              <Button variant="default"><FileText className="h-4 w-4 mr-2" />AI 起草上诉状</Button>
              <Button variant="outline"><Upload className="h-4 w-4 mr-2" />上传一审判决书</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {appeals.map((appeal) => (
            <Card key={appeal.id} className="border-l-4 border-l-primary">
              <CardHeader>
                <CardTitle className="text-base">{appeal.title || '二审诉讼程序'}</CardTitle>
                <CardDescription>上诉法院: {appeal.court_name || '待定'} | 状态: {appeal.status || '准备中'}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{appeal.overview || '暂无上诉策略描述'}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
