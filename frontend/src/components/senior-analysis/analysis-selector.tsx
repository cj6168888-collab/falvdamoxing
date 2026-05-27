import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AIProgress } from '@/components/common/ai-progress';
import { useSeniorAnalysisHook } from '@/hooks/use-senior-analysis';

const DEPTH_STEPS: Record<string, string[]> = {
  quick: ['正在读取案件概要...', '正在分析核心争议...', '正在生成建议...'],
  standard: ['正在读取案件信息...', '正在分析当事人关系...', '正在评估证据链...', '正在分析法律适用...', '正在生成策略建议...', '即将完成...'],
  deep: ['正在全面读取案件数据...', '正在分析案件背景...', '正在分析当事人关系网络...', '正在深度评估证据效力...', '正在分析法律适用与判例...', '正在制定诉讼策略...', '正在评估风险与应对...', '正在生成完整分析报告...', '即将完成...'],
};

const DEPTH_DURATION: Record<string, number> = {
  quick: 15000,
  standard: 30000,
  deep: 60000,
};

interface Props { caseId: string; }

export function AnalysisSelector({ caseId }: Props) {
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const { data, isLoading } = useSeniorAnalysisHook(caseId, depth);
  const steps = DEPTH_STEPS[depth] || DEPTH_STEPS.standard;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant={depth === 'quick' ? 'default' : 'outline'} onClick={() => setDepth('quick')}>快速</Button>
        <Button variant={depth === 'standard' ? 'default' : 'outline'} onClick={() => setDepth('standard')}>标准</Button>
        <Button variant={depth === 'deep' ? 'default' : 'outline'} onClick={() => setDepth('deep')}>深度</Button>
      </div>
      {isLoading ? (
        <AIProgress
          isActive={true}
          title={`资深律师分析（${depth === 'quick' ? '快速' : depth === 'standard' ? '标准' : '深度'}）`}
          estimatedDuration={DEPTH_DURATION[depth]}
          steps={steps}
        />
      ) : (
        <Card>
          <CardHeader><CardTitle>资深律师分析 ({depth})</CardTitle></CardHeader>
          <CardContent>
            {data ? (
              <>
                <div><p className="text-sm text-muted-foreground">核心争议</p><p>{data.caseUnderstanding}</p></div>
                <div className="mt-3"><p className="text-sm text-muted-foreground">策略建议</p><ul className="list-disc pl-5">{data.strategySuggestions?.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></div>
              </>
            ) : <p className="text-muted-foreground">暂无分析数据</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
