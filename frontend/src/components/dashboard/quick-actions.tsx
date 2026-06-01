import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { FileText, MessageCircle, Plus, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface QuickActionItem {
  id: string;
  label: string;
  icon: typeof Plus;
  description: string;
  route: string;
  variant: 'default' | 'outline' | 'secondary';
}

const TEXT = {
  sectionTitle: '快捷入口',
};

const actions: QuickActionItem[] = [
  {
    id: 'new-case',
    label: '新建案件',
    icon: Plus,
    description: '创建新的法律案件',
    route: '/cases/new',
    variant: 'default',
  },
  {
    id: 'upload-evidence',
    label: '证据上传',
    icon: Upload,
    description: '上传案件相关证据材料',
    route: '/cases',
    variant: 'outline',
  },
  {
    id: 'generate-doc',
    label: '文书草稿',
    icon: FileText,
    description: '起草待核验法律文书',
    route: '/cases',
    variant: 'outline',
  },
  {
    id: 'legal-consult',
    label: '问题整理',
    icon: MessageCircle,
    description: '整理问题并提示风险',
    route: '/cases',
    variant: 'secondary',
  },
];

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <section aria-label={TEXT.sectionTitle}>
      <div className="mb-4 flex items-center gap-2">
        <Plus className="h-5 w-5 text-green-500" />
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
      </div>
      <div className="grid grid-cols-2 items-stretch gap-3 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <motion.div
              key={action.id}
              className="relative h-full min-w-0"
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.98 }}
              transition={{ duration: 0.15 }}
            >
              <Button
                variant={action.variant}
                className="flex h-full min-h-32 w-full flex-col items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-5 text-center shadow-sm transition-all duration-200 hover:border-gray-300 hover:shadow-md dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
                onClick={() => navigate(action.route)}
                aria-label={`${action.label}: ${action.description}`}
              >
                <div className="rounded-full bg-gray-100 p-2.5 dark:bg-gray-700">
                  <Icon className="h-5 w-5 text-gray-700 dark:text-gray-300" />
                </div>
                <div className="pointer-events-none min-w-0">
                  <span className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {action.label}
                  </span>
                  <span className="mt-0.5 block text-xs text-gray-500 dark:text-gray-400">
                    {action.description}
                  </span>
                </div>
              </Button>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
