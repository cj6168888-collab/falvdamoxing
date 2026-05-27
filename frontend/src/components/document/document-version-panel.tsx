import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DocumentVersion } from '@/components/common/document-version';

interface Version { version: number; timestamp: string; }
interface Props { versions: Version[]; currentVersion: number; onSelect: (v: number) => void; onCompare: (v: number) => void; }

export function DocumentVersionPanel({ versions, currentVersion, onSelect, onCompare }: Props) {
  return (
    <Card>
      <CardHeader><CardTitle>版本历史</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {versions.map((v) => (
          <DocumentVersion key={v.version} version={v.version} timestamp={v.timestamp} isCurrent={v.version === currentVersion} onSelect={() => onSelect(v.version)} onCompare={() => onCompare(v.version)} />
        ))}
      </CardContent>
    </Card>
  );
}
