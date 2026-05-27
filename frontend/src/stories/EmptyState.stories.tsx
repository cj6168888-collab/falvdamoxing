import type { Meta, StoryObj } from '@storybook/react-vite';
import { EmptyState } from '@/components/common/empty-state';
import { FileText, Scale, Bell } from 'lucide-react';

const meta = {
  title: 'Common/EmptyState',
  component: EmptyState,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    icon: {
      control: false,
    },
    onAction: {
      action: 'clicked',
    },
  },
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const EvidenceEmpty: Story = {
  args: {
    icon: FileText,
    title: '还没有证据',
    description: '试试上传第一份证据，帮助您构建完整的证据链。',
    actionLabel: '上传证据',
  },
};

export const CaseEmpty: Story = {
  args: {
    icon: Scale,
    title: '暂无案件',
    description: '创建您的第一个案件，开始追踪管理。',
    actionLabel: '新建案件',
  },
};

export const ReminderEmpty: Story = {
  args: {
    icon: Bell,
    title: '暂无提醒',
    description: '设置提醒，不错过任何重要期限。',
    actionLabel: '添加提醒',
  },
};
