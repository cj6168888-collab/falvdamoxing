import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { format } from 'date-fns';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { DatePicker } from '@/components/ui/date-picker';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateLetter, useUpdateLetter } from '@/hooks/use-letter';
import type {
  Letter,
  LetterDirection,
  LetterType,
} from '@/types/letter.types';
import {
  DIRECTION_OPTIONS,
  LETTER_TYPE_OPTIONS,
} from '@/types/letter.types';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface LetterFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  caseId: string;
  letter?: Letter; // 如果有值则是编辑模式
  onSuccess?: () => void;
}

interface LetterFormData {
  direction: LetterDirection;
  letter_type: LetterType;
  title: string;
  reference_number: string;
  sender: string;
  recipient: string;
  letter_date: Date | undefined;
  received_date: Date | undefined;
  deadline: Date | undefined;
  content_summary: string;
  key_demands: string;
  mailing_purpose: string;
  generation_notes: string;
}

export function LetterFormDialog({
  open,
  onOpenChange,
  caseId,
  letter,
  onSuccess,
}: LetterFormDialogProps) {
  const isEdit = !!letter;
  const createLetter = useCreateLetter();
  const updateLetter = useUpdateLetter();
  const isPending = createLetter.isPending || updateLetter.isPending;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<LetterFormData>({
    defaultValues: {
      direction: 'outgoing',
      letter_type: 'lawyer_letter',
      title: '',
      reference_number: '',
      sender: '',
      recipient: '',
      letter_date: undefined,
      received_date: undefined,
      deadline: undefined,
      content_summary: '',
      key_demands: '',
      mailing_purpose: '',
      generation_notes: '',
    },
  });

  // 编辑模式时填充表单
  useEffect(() => {
    if (letter) {
      reset({
        direction: letter.direction,
        letter_type: letter.letter_type,
        title: letter.title,
        reference_number: letter.reference_number || '',
        sender: letter.sender || '',
        recipient: letter.recipient || '',
        letter_date: letter.letter_date ? new Date(letter.letter_date) : undefined,
        received_date: letter.received_date ? new Date(letter.received_date) : undefined,
        deadline: letter.deadline ? new Date(letter.deadline) : undefined,
        content_summary: letter.content_summary || '',
        key_demands: letter.key_demands || '',
        mailing_purpose: letter.mailing_purpose || '',
        generation_notes: letter.generation_notes || '',
      });
    } else {
      reset({
        direction: 'outgoing',
        letter_type: 'lawyer_letter',
        title: '',
        reference_number: '',
        sender: '',
        recipient: '',
        letter_date: undefined,
        received_date: undefined,
        deadline: undefined,
        content_summary: '',
        key_demands: '',
        mailing_purpose: '',
        generation_notes: '',
      });
    }
  }, [letter, reset]);

  const direction = watch('direction');
  const letterDate = watch('letter_date');
  const receivedDate = watch('received_date');

  const onSubmit = async (data: LetterFormData) => {
    try {
      const payload = {
        direction: data.direction,
        letter_type: data.letter_type,
        title: data.title,
        reference_number: data.reference_number || undefined,
        sender: data.sender || undefined,
        recipient: data.recipient || undefined,
        letter_date: data.letter_date ? format(data.letter_date, 'yyyy-MM-dd') : undefined,
        received_date: data.received_date ? format(data.received_date, 'yyyy-MM-dd') : undefined,
        deadline: data.deadline ? format(data.deadline, 'yyyy-MM-dd') : undefined,
        content_summary: data.content_summary || undefined,
        key_demands: data.key_demands || undefined,
        mailing_purpose: data.mailing_purpose || undefined,
        generation_notes: data.generation_notes || undefined,
      };

      if (isEdit) {
        await updateLetter.mutateAsync({
          caseId,
          letterId: letter.id.toString(),
          data: payload,
        });
        toast.success('函件更新成功');
      } else {
        await createLetter.mutateAsync({
          caseId,
          data: payload,
        });
        toast.success('函件创建成功');
      }

      onOpenChange(false);
      reset();
      onSuccess?.();
    } catch (error) {
      toast.error(isEdit ? '更新失败' : '创建失败');
      console.error(error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? '编辑函件' : '新建函件'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* 第一行：方向和类型 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">收发方向 *</label>
              <Select
                value={direction}
                onValueChange={(val) => setValue('direction', val as LetterDirection)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择方向" />
                </SelectTrigger>
                <SelectContent>
                  {DIRECTION_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">函件类型 *</label>
              <Select
                value={watch('letter_type')}
                onValueChange={(val) => setValue('letter_type', val as LetterType)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  {LETTER_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 标题 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">函件标题 *</label>
            <Input
              {...register('title', { required: '请输入标题' })}
              placeholder="请输入函件标题"
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title.message}</p>
            )}
          </div>

          {/* 文号 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">文号/编号</label>
            <Input
              {...register('reference_number')}
              placeholder="如：[2024]xxx字第xx号"
            />
          </div>

          {/* 发送方和接收方 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {direction === 'incoming' ? '发件方' : '发件人/机构'}
              </label>
              <Input
                {...register('sender')}
                placeholder={direction === 'incoming' ? '对方发件方' : '我方发件人'}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {direction === 'incoming' ? '收件方' : '收件人/机构'}
              </label>
              <Input
                {...register('recipient')}
                placeholder={direction === 'incoming' ? '我方收件方' : '对方收件人'}
              />
            </div>
          </div>

          {/* 日期选择 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {direction === 'incoming' ? '收件日期' : '函件日期'}
              </label>
              <DatePicker
                date={letterDate}
                onSelect={(date) => setValue('letter_date', date)}
              />
            </div>

            {direction === 'incoming' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">收到日期</label>
                <DatePicker
                  date={receivedDate}
                  onSelect={(date) => setValue('received_date', date)}
                />
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">回复截止日期</label>
              <DatePicker
                date={watch('deadline')}
                onSelect={(date) => setValue('deadline', date)}
              />
            </div>
          </div>

          {/* 内容摘要 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">内容摘要</label>
            <Textarea
              {...register('content_summary')}
              placeholder="简要描述函件的主要内容..."
              rows={3}
            />
          </div>

          {/* 核心诉求 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">核心诉求</label>
            <Textarea
              {...register('key_demands')}
              placeholder="对方的主要诉求是什么..."
              rows={2}
            />
          </div>

          {/* 邮寄目的 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">邮寄目的说明</label>
            <Textarea
              {...register('mailing_purpose')}
              placeholder="说明本次邮寄的目的..."
              rows={2}
            />
          </div>

          {/* 生成前备注 */}
          <div className="space-y-2">
            <label className="text-sm font-medium">生成前备注</label>
            <Textarea
              {...register('generation_notes')}
              placeholder="生成回复前的特殊说明（如：哪个证据先不放、哪个主张先不提）..."
              rows={2}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              取消
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
