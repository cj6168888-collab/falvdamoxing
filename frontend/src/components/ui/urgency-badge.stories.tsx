import type { Meta, StoryObj } from '@storybook/react-vite';
import { UrgencyBadge } from './urgency-badge';

const meta = {
  title: 'UI/UrgencyBadge',
  component: UrgencyBadge,
  tags: ['autodocs'],
  argTypes: {
    daysRemaining: { control: { type: 'number' } },
    label: { control: { type: 'text' } },
    className: { control: { type: 'text' } },
  },
} satisfies Meta<typeof UrgencyBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Expired: Story = {
  args: {
    daysRemaining: -2,
  },
};

export const Urgent: Story = {
  args: {
    daysRemaining: 3,
  },
};

export const Warning: Story = {
  args: {
    daysRemaining: 15,
  },
};

export const Normal: Story = {
  args: {
    daysRemaining: 45,
  },
};
