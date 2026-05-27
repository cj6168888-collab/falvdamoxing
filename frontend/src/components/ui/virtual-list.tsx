import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';
interface VirtualListProps<T> { items: T[]; renderItem: (item: T, index: number) => React.ReactNode; estimateSize?: number; }
export function VirtualList<T>({ items, renderItem, estimateSize = 50 }: VirtualListProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({ count: items.length, getScrollElement: () => parentRef.current, estimateSize: () => estimateSize });
  return (<div ref={parentRef} className="overflow-auto" style={{ height: '100%' }}><div style={{ height: virtualizer.getTotalSize(), width: '100%', position: 'relative' }}>{virtualizer.getVirtualItems().map((virtualRow) => (<div key={virtualRow.index} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: virtualRow.size, transform: `translateY(${virtualRow.start}px)` }}>{renderItem(items[virtualRow.index], virtualRow.index)}</div>))}</div></div>);
}
