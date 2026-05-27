import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calculator, Plus, Minus, RotateCcw, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface AmountCalculatorProps {
  caseId: number;
  analysisId?: number;
  recommendedAmount?: number | null;
  breakdown?: Record<string, string>;
  maxPossible?: string;
  onConfirmed?: (amount: number) => void;
  onError?: (error: string) => void;
}

export function AmountCalculator({
  caseId,
  analysisId,
  recommendedAmount,
  breakdown,
  maxPossible,
  onConfirmed,
  onError,
}: AmountCalculatorProps) {
  const [amount, setAmount] = useState<number>(recommendedAmount || 0);
  const [history, setHistory] = useState<string[]>([]);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleNumber = (num: string) => {
    setAmount(prev => {
      const newVal = prev === 0 ? num : prev.toString() + num;
      return parseFloat(newVal) || 0;
    });
  };

  const handleOp = (op: '+' | '-') => {
    setHistory(prev => [...prev, amount.toString(), op]);
    setAmount(0);
  };

  const handleEqual = () => {
    if (history.length === 0) return;
    const fullExpr = [...history, amount.toString()].join(' ');
    try {
      const parts = fullExpr.split(' ');
      let result = parseFloat(parts[0]) || 0;
      for (let i = 1; i < parts.length; i += 2) {
        const op = parts[i];
        const num = parseFloat(parts[i + 1]) || 0;
        if (op === '+') result += num;
        else if (op === '-') result -= num;
      }
      setAmount(Math.round(result));
      setHistory([]);
    } catch {
      // ignore
    }
  };

  const handleClear = () => {
    setAmount(0);
    setHistory([]);
  };

  const handlePercent = (percent: number) => {
    const base = recommendedAmount || amount;
    setAmount(Math.round(base * percent / 100));
  };

  const handleConfirm = async () => {
    if (!caseId) {
      toast.error('缺少案件ID');
      return;
    }

    setIsConfirming(true);
    try {
      const { default: axiosInstance } = await import('@/api/client');

      // 调用确认建议 API
      const confirmedFields: Record<string, number> = { claim_amount: amount };
      await axiosInstance.post('/api/smart-chat/confirm-suggestion', {
        analysis_id: analysisId,
        confirmed_fields: confirmedFields,
      });

      toast.success(`已确认诉讼金额：¥${amount.toLocaleString()}`);
      onConfirmed?.(amount);
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' &&
        err !== null &&
        'response' in err &&
        typeof (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail ===
          'string'
          ? (err as { response: { data: { detail: string } } }).response.data.detail
          : undefined;
      const errorMsg = detail || (err instanceof Error ? err.message : '更新失败');
      toast.error(errorMsg);
      onError?.(errorMsg);
    } finally {
      setIsConfirming(false);
    }
  };

  const formatCurrency = (val: number) => {
    return val.toLocaleString('zh-CN');
  };

  return (
    <Card className="bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-purple-700 dark:text-purple-400 flex items-center gap-1">
          <Calculator className="h-3.5 w-3.5" />
          金额计算器
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 金额显示 */}
        <div className="text-right">
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            ¥{formatCurrency(amount)}
          </p>
          {recommendedAmount && amount !== recommendedAmount && (
            <p className="text-xs text-muted-foreground">
              建议金额：¥{formatCurrency(recommendedAmount)}
            </p>
          )}
        </div>

        {/* 快捷按钮 */}
        {recommendedAmount && (
          <div className="flex flex-wrap gap-1">
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => setAmount(recommendedAmount)}
            >
              使用建议
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => handlePercent(50)}
            >
              50%
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => handlePercent(80)}
            >
              80%
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={() => handlePercent(100)}
            >
              100%
            </Button>
          </div>
        )}

        {/* 计算器键盘 */}
        <div className="grid grid-cols-4 gap-1">
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('1')}>1</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('2')}>2</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('3')}>3</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleOp('+')}>
            <Plus className="h-3 w-3" />
          </Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('4')}>4</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('5')}>5</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('6')}>6</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleOp('-')}>
            <Minus className="h-3 w-3" />
          </Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('7')}>7</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('8')}>8</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('9')}>9</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('000')}>000</Button>
          <Button variant="outline" size="sm" className="h-8 col-span-2" onClick={() => handleNumber('0')}>0</Button>
          <Button variant="outline" size="sm" className="h-8" onClick={() => handleNumber('.')}>.</Button>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 h-8" onClick={handleClear}>
            <RotateCcw className="h-3 w-3 mr-1" />清零
          </Button>
          <Button variant="default" size="sm" className="flex-1 h-8" onClick={handleEqual}>
            = 计算
          </Button>
          {caseId && (
            <Button
              variant="secondary"
              size="sm"
              className="flex-1 h-8"
              onClick={handleConfirm}
              disabled={isConfirming}
            >
              {isConfirming ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <Check className="h-3 w-3 mr-1" />
              )}
              确认
            </Button>
          )}
        </div>

        {/* 参考信息 */}
        {breakdown && Object.keys(breakdown).length > 0 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground font-medium mb-1">金额构成参考</p>
            <div className="space-y-0.5">
              {Object.entries(breakdown).map(([key, value]) => (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-muted-foreground">{key}</span>
                  <span className="font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {maxPossible && (
          <p className="text-xs text-muted-foreground">
            最高可主张：{maxPossible}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default AmountCalculator;
