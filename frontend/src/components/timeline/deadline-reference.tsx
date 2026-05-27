import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const REFERENCES = [
  { name: '普通民事诉讼', period: '3年' },
  { name: '身体伤害', period: '1年' },
  { name: '租金纠纷', period: '1年' },
  { name: '借款纠纷', period: '3年' },
  { name: '答辩期', period: '15日' },
  { name: '举证期限', period: '30日' },
  { name: '民事上诉', period: '15日' },
  { name: '执行申请', period: '2年' },
];

export function DeadlineReference() {
  return (
    <Card>
      <CardHeader><CardTitle>常用法定期限参考</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {REFERENCES.map((r) => (
            <div key={r.name} className="flex justify-between text-sm">
              <span>{r.name}</span>
              <span className="font-medium">{r.period}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
