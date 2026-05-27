interface Props { oldContent: string; newContent: string; }

export function VersionDiff({ oldContent, newContent }: Props) {
  const oldLines = oldContent.split('\n');
  const newLines = newContent.split('\n');
  const maxLines = Math.max(oldLines.length, newLines.length);
  const diff: { type: string; oldLine?: string; newLine?: string }[] = [];
  for (let i = 0; i < maxLines; i++) {
    if (oldLines[i] === newLines[i]) {
      diff.push({ type: 'same', oldLine: oldLines[i], newLine: newLines[i] });
    } else {
      if (oldLines[i]) diff.push({ type: 'removed', oldLine: oldLines[i] });
      if (newLines[i]) diff.push({ type: 'added', newLine: newLines[i] });
    }
  }
  return (
    <div className="rounded-md border font-mono text-sm">
      {diff.map((line, i) => (
        <div key={i} className={`flex px-3 py-1 ${line.type === 'added' ? 'bg-green-50 dark:bg-green-900/20' : line.type === 'removed' ? 'bg-red-50 dark:bg-red-900/20' : ''}`}>
          <span className="w-8 shrink-0 text-muted-foreground">{i + 1}</span>
          <span className={line.type === 'added' ? 'text-green-700 dark:text-green-400' : line.type === 'removed' ? 'text-red-700 dark:text-red-400' : ''}>
            {line.type === 'added' ? '+ ' : line.type === 'removed' ? '- ' : '  '}
            {line.newLine || line.oldLine}
          </span>
        </div>
      ))}
    </div>
  );
}
