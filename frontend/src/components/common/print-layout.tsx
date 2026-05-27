import React from 'react';

interface Props { children: React.ReactNode; }

export function PrintLayout({ children }: Props) {
  return <div className="print:p-8 print:bg-white">{children}</div>;
}
