import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props { strengths: string[]; weaknesses: string[]; opponentWeaknesses: string[]; opponentStrengths: string[]; }

export function SwotQuadrant({ strengths, weaknesses, opponentWeaknesses, opponentStrengths }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <Card><CardHeader><CardTitle className="text-green-600">我方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{strengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-red-600">我方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{weaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-amber-600">对方劣势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentWeaknesses.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
      <Card><CardHeader><CardTitle className="text-blue-600">对方优势</CardTitle></CardHeader><CardContent><ul className="list-disc pl-5">{opponentStrengths.map((s, i) => <li key={i} className="text-sm">{s}</li>)}</ul></CardContent></Card>
    </div>
  );
}
