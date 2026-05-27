import { useEffect, useState } from 'react';

interface Props { text: string; onComplete: () => void; }

export function StreamResponse({ text, onComplete }: Props) {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        onComplete();
      }
    }, 20);
    return () => clearInterval(interval);
  }, [text, onComplete]);
  return <p className="text-sm whitespace-pre-wrap">{displayed}<span className="animate-pulse">|</span></p>;
}
