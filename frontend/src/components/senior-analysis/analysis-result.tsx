import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { caseUnderstanding: string; strategySuggestions: string[]; riskWarnings: string[]; }

export function AnalysisResult({ caseUnderstanding, strategySuggestions, riskWarnings }: Props) {
  return (
    <div className="space-y-4">
      <Card><CardHeader><CardTitle>案件理解</CardTitle></CardHeader><CardContent><p className="text-sm whitespace-pre-wrap">{caseUnderstanding}</p></CardContent></Card>
      <Card><CardHeader><CardTitle>策略建议</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{strategySuggestions?.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle>风险提示</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{riskWarnings?.map((w, i) => <li key={i} className="text-sm text-red-600">{w}</li>)}</ul></CardContent></Card>
    </div>
  );
}
