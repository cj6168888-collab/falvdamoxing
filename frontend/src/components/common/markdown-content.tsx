import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { cn } from '@/lib/utils';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * 深度清理 AI 输出内容，确保 Markdown 渲染正确
 */
function cleanMarkdownContent(content: string): string {
  let cleaned = content;

  // 1. 移除 JSON 代码块（```json ... ``` 和 ``` ... ```）
  cleaned = cleaned.replace(/```(?:json)?\s*[\s\S]*?```/g, '');

  // 2. 移除所有代码块标记
  cleaned = cleaned.replace(/```\s*/g, '');

  // 3. 清理分隔线噪音（纯符号行）
  cleaned = cleaned.replace(/^(?:[=\-*~_#]){3,}\s*$/gm, '');

  // 4. 修复中文标题格式：确保 # 后有空格
  // ##一、案情 → ## 一、案情
  cleaned = cleaned.replace(/^(#{1,6})([^\s#])/gm, '$1 $2');

  // 5. 修复列表格式：确保 - * + 后有空格（如果后面有内容）
  cleaned = cleaned.replace(/^(\s*[-*+])([^\s\n])/gm, '$1 $2');

  // 6. 修复数字列表格式
  cleaned = cleaned.replace(/^(\s*\d+\.)([^\s\n])/gm, '$1 $2');

  // 7. 清理连续空行
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  // 8. 清理行首尾空白
  cleaned = cleaned.split('\n').map(line => line.trimEnd()).join('\n');

  // 9. 确保标题前后有空行
  cleaned = cleaned.replace(/([^\n])\n(#{1,6}\s)/g, '$1\n\n$2');
  cleaned = cleaned.replace(/(#{1,6}\s[^\n]+)\n([^\n#])/g, '$1\n\n$2');

  // 10. 确保列表前后有空行
  cleaned = cleaned.replace(/([^\n])\n(\s*[-*+]\s)/g, '$1\n\n$2');
  cleaned = cleaned.replace(/([^\n])\n(\s*\d+\.\s)/g, '$1\n\n$2');

  // 11. 确保表格前后有空行
  if (/\|/.test(cleaned)) {
    cleaned = cleaned.replace(/([^\n|])\n(\s*\|)/g, '$1\n\n$2');
  }

  // 12. 修复加粗格式：**text** 前后确保有空格（如果在句子中间则不需要）
  // 移除孤立的 ** 行
  cleaned = cleaned.replace(/^\s*\*\*\s*$/gm, '');
  cleaned = cleaned.replace(/^\s*\*\s*$/gm, '');

  // 13. 移除纯数字/符号行（AI 常见的无意义输出）
  cleaned = cleaned.replace(/^\s*(?:\d+|[=\-*~_])\s*$/gm, '');

  return cleaned.trim();
}

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  const cleanedContent = cleanMarkdownContent(content);

  return (
    <div className={cn('prose prose-sm max-w-none dark:prose-invert', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold mt-6 mb-3 pb-2 border-b border-border">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold mt-5 mb-2 text-primary flex items-center gap-2">
              <span className="w-1 h-5 bg-primary rounded-sm inline-block flex-shrink-0" />
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mt-4 mb-1.5 text-foreground">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold mt-3 mb-1 text-muted-foreground">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed mb-2 text-foreground/90">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-5 space-y-1 text-sm mb-3 text-foreground/90">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 space-y-1 text-sm mb-3 text-foreground/90">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-sm leading-relaxed">{children}</li>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4 rounded-lg border border-border">
              <table className="min-w-full border-collapse text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/80">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="border-b border-border px-4 py-2.5 text-left font-semibold text-foreground">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border-b border-border/50 px-4 py-2 text-foreground/90 last:border-b-0">
              {children}
            </td>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-muted/30 transition-colors">{children}</tr>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className && !String(children).includes('\n');
            if (isInline) {
              return (
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono text-primary" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <pre className="rounded-lg bg-muted p-4 overflow-x-auto my-3 border border-border">
                <code className="text-xs font-mono text-foreground/90" {...props}>
                  {children}
                </code>
              </pre>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary pl-4 py-2 my-3 bg-primary/5 rounded-r">
              {children}
            </blockquote>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-foreground">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-muted-foreground">{children}</em>
          ),
          a: ({ href, children }) => (
            <a href={href} className="text-primary underline hover:text-primary/80 transition-colors" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
          hr: () => (
            <hr className="my-4 border-border" />
          ),
        }}
      >
        {cleanedContent}
      </ReactMarkdown>
    </div>
  );
}
