import { CaseCard } from '@/components/common/case-card';
import type { Case } from '@/types/case.types';
import type { Meta, StoryObj } from '@storybook/react-vite';

const baseCase: Case = {
  id: 'case-001',
  title: 'Loan Dispute Case',
  type: 'Loan',
  status: 'negotiating',
  description: 'Private lending dispute with incomplete repayment records.',
  amount: 500000,
  plaintiff: { name: 'Zhang San' },
  defendant: { name: 'Li Si' },
  evidenceCount: 5,
  documentCount: 3,
  deadlineCount: 3,
  createdAt: '2026-04-01T00:00:00.000Z',
  updatedAt: '2026-04-08T00:00:00.000Z',
};

const meta = {
  title: 'Common/CaseCard',
  component: CaseCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    urgency: {
      control: 'select',
      options: ['expired', 'urgent', 'warning', 'normal'],
    },
    daysRemaining: {
      control: 'number',
    },
    selectable: {
      control: 'boolean',
    },
    selected: {
      control: 'boolean',
    },
  },
} satisfies Meta<typeof CaseCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const InProgressNormal: Story = {
  args: {
    caseData: baseCase,
    urgency: 'normal',
    daysRemaining: 45,
  },
};

export const UrgentWarning: Story = {
  args: {
    caseData: {
      ...baseCase,
      id: 'case-002',
      title: 'Contract Dispute Case',
      type: 'Contract',
      status: 'appealing',
      amount: 200000,
      plaintiff: { name: 'Company A' },
      defendant: { name: 'Company B' },
      evidenceCount: 8,
      documentCount: 2,
      deadlineCount: 1,
    },
    urgency: 'urgent',
    daysRemaining: 5,
  },
};

export const CompletedExpired: Story = {
  args: {
    caseData: {
      ...baseCase,
      id: 'case-003',
      title: 'Tort Compensation Case',
      type: 'Tort',
      status: 'closed',
      amount: 1500000,
      plaintiff: { name: 'Wang Wu' },
      defendant: { name: 'Zhao Liu' },
      evidenceCount: 12,
      documentCount: 6,
      deadlineCount: 0,
    },
    urgency: 'expired',
    daysRemaining: -3,
  },
};

export const DraftNormal: Story = {
  args: {
    caseData: {
      ...baseCase,
      id: 'case-004',
      title: 'Labor Dispute Case',
      type: 'Labor',
      status: 'preparing',
      amount: 80000,
      plaintiff: { name: 'Sun Qi' },
      defendant: { name: 'Tech Company' },
      evidenceCount: 2,
      documentCount: 1,
      deadlineCount: 2,
    },
    urgency: 'normal',
    daysRemaining: 60,
  },
};
