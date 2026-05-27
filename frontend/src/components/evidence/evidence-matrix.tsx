import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface EvidenceMatrixEvidence {
  id: string;
  name: string;
}

interface EvidenceMatrixIssue {
  id: string;
  title: string;
}

interface Props { evidence: EvidenceMatrixEvidence[]; issues: EvidenceMatrixIssue[]; }

export function EvidenceMatrix({ evidence, issues }: Props) {
  return (
    <Table>
      <TableHeader><TableRow><TableHead>证据</TableHead>{issues.map((i) => <TableHead key={i.id}>{i.title}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{evidence.map((e) => <TableRow key={e.id}><TableCell>{e.name}</TableCell>{issues.map((i) => <TableCell key={i.id}>-</TableCell>)}</TableRow>)}</TableBody>
    </Table>
  );
}
