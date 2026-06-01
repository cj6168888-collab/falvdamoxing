import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  BriefcaseBusiness,
  Building2,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FileText,
  Handshake,
  HeartHandshake,
  MessageSquareText,
  PiggyBank,
  ShieldCheck,
  Upload,
  UserRound,
  UsersRound,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface MetricItem {
  label: string;
  value: string;
  tone: string;
}

interface WorkCard {
  title: string;
  description: string;
  icon: typeof Building2;
}

interface ActionItem {
  title: string;
  description: string;
  route: string;
  icon: typeof Upload;
}

const enterpriseMetrics: MetricItem[] = [
  { label: '待整理事项', value: '0', tone: 'text-blue-600' },
  { label: '合同风险', value: '0', tone: 'text-amber-600' },
  { label: '回款线索', value: '0', tone: 'text-emerald-600' },
  { label: '用工提醒', value: '0', tone: 'text-rose-600' },
];

const enterpriseCards: WorkCard[] = [
  {
    title: '合同风险',
    description: '审查付款、验收、违约、解除、管辖和担保条款，形成待核验风险清单。',
    icon: FileCheck2,
  },
  {
    title: '应收账款',
    description: '整理合同、对账、发票、催告和转账记录，沉淀回款行动底稿。',
    icon: PiggyBank,
  },
  {
    title: '劳动用工',
    description: '梳理入离职、工资、社保、竞业、解除和工伤风险，提示材料缺口。',
    icon: UsersRound,
  },
  {
    title: '客户供应商争议',
    description: '把沟通记录、交付节点、质量异议和损失线索整理成争议事实表。',
    icon: Handshake,
  },
  {
    title: '制度合规',
    description: '围绕印章、授权、审批、数据和知识产权形成企业内控检查项。',
    icon: ShieldCheck,
  },
  {
    title: '律师协作',
    description: '生成给外部律师的案情摘要、证据目录和待确认问题清单。',
    icon: BriefcaseBusiness,
  },
];

const enterpriseActions: ActionItem[] = [
  {
    title: '上传合同或函件',
    description: '先把原始材料放进系统，后续再做风险识别。',
    route: '/cases/new?template=contract_review',
    icon: Upload,
  },
  {
    title: '整理欠款材料',
    description: '从合同、对账、付款和催告记录开始建立回款底稿。',
    route: '/cases/new?template=debt_collection',
    icon: PiggyBank,
  },
  {
    title: '创建用工风险事项',
    description: '记录员工、时间、决定依据和已沟通内容。',
    route: '/cases/new?template=labor_employment',
    icon: UsersRound,
  },
  {
    title: '生成律师协作摘要',
    description: '把事实、诉求、证据和疑问整理成可转交材料。',
    route: '/cases',
    icon: MessageSquareText,
  },
];

const personalMetrics: MetricItem[] = [
  { label: '待处理问题', value: '0', tone: 'text-blue-600' },
  { label: '紧急风险', value: '0', tone: 'text-rose-600' },
  { label: '已存证据', value: '0', tone: 'text-emerald-600' },
  { label: '下一步行动', value: '0', tone: 'text-amber-600' },
];

const personalCards: WorkCard[] = [
  {
    title: '先稳住处境',
    description: '识别是否存在期限、安全、财产或证据灭失风险，先处理最急的事。',
    icon: HeartHandshake,
  },
  {
    title: '事实时间线',
    description: '用普通人能理解的方式，把发生时间、参与方和关键行为排清楚。',
    icon: Clock3,
  },
  {
    title: '证据保全',
    description: '提示聊天、转账、合同、照片、录音、快递和投诉记录如何保存。',
    icon: ShieldCheck,
  },
  {
    title: '沟通协商',
    description: '准备克制、留痕、可复核的沟通提纲，避免情绪化扩大风险。',
    icon: MessageSquareText,
  },
  {
    title: '投诉调解',
    description: '整理平台投诉、劳动仲裁、人民调解或行政投诉前需要的材料。',
    icon: ClipboardCheck,
  },
  {
    title: '文书草稿',
    description: '起草情况说明、投诉材料、调解申请或其他待核验文书草稿。',
    icon: FileText,
  },
];

const personalActions: ActionItem[] = [
  {
    title: '描述遇到的事',
    description: '不用专业术语，先把事情原样讲出来。',
    route: '/cases/new?template=personal_general',
    icon: UserRound,
  },
  {
    title: '列出最担心的问题',
    description: '把害怕、疑问和对方说法拆成可判断的问题。',
    route: '/cases/new?template=urgent_risk',
    icon: AlertTriangle,
  },
  {
    title: '上传关键凭证',
    description: '先保存聊天、转账、合同、照片、录音等材料。',
    route: '/cases',
    icon: Upload,
  },
  {
    title: '获得下一步清单',
    description: '形成今天能做什么、暂时别做什么、需要核验什么。',
    route: '/cases',
    icon: ClipboardCheck,
  },
];

function Metrics({ items }: { items: MetricItem[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="pt-6">
            <div className={`text-2xl font-bold ${item.tone}`}>{item.value}</div>
            <p className="text-xs text-muted-foreground">{item.label}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function WorkAreas({ items }: { items: WorkCard[] }) {
  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-slate-950 dark:text-slate-50">核心工作区</h2>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title}>
              <CardHeader className="space-y-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-200">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base">{item.title}</CardTitle>
                  <CardDescription className="mt-2 leading-6">{item.description}</CardDescription>
                </div>
              </CardHeader>
            </Card>
          );
        })}
      </div>
    </section>
  );
}

function ActionList({ items }: { items: ActionItem[] }) {
  const navigate = useNavigate();

  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-slate-950 dark:text-slate-50">今天可以先做</h2>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <Button
              key={item.title}
              type="button"
              variant="outline"
              className="h-auto justify-start gap-3 rounded-lg p-4 text-left"
              onClick={() => navigate(item.route)}
            >
              <Icon className="h-5 w-5 shrink-0 text-teal-700 dark:text-teal-300" />
              <span className="min-w-0">
                <span className="block text-sm font-semibold">{item.title}</span>
                <span className="mt-1 block whitespace-normal text-xs font-normal text-muted-foreground">
                  {item.description}
                </span>
              </span>
            </Button>
          );
        })}
      </div>
    </section>
  );
}

function AudienceDashboardShell({
  eyebrow,
  title,
  description,
  notice,
  metrics,
  cards,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  notice: string;
  metrics: MetricItem[];
  cards: WorkCard[];
  actions: ActionItem[];
}) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6">
        <p className="text-sm font-medium text-teal-700 dark:text-teal-300">{eyebrow}</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-950 dark:text-slate-50">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p>
      </header>

      <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
        {notice}
      </div>

      <div className="space-y-8">
        <Metrics items={metrics} />
        <ActionList items={actions} />
        <WorkAreas items={cards} />
      </div>
    </div>
  );
}

export function EnterpriseDashboard() {
  return (
    <AudienceDashboardShell
      eyebrow="企业版"
      title="企业法律顾问工作台"
      description="把合同、回款、用工、客户供应商争议和合规事项纳入一个持续留痕的法律风险工作台，让企业在日常经营中也能有靠谱的法律顾问感。"
      notice="系统输出用于风险识别、材料整理和行动准备。涉及重大金额、裁员解除、诉讼仲裁或高风险合规事项时，请在提交或执行前进行专业复核。"
      metrics={enterpriseMetrics}
      cards={enterpriseCards}
      actions={enterpriseActions}
    />
  );
}

export function PersonalDashboard() {
  return (
    <AudienceDashboardShell
      eyebrow="个人版"
      title="个人法律后盾"
      description="当普通人遇到法律问题时，先把人扶住：看清事实、保住证据、识别风险、拆出今天能做的下一步，而不是把焦虑继续放大。"
      notice="这里不会承诺结果，也不会替你作出最终决定。它会陪你把事实和证据整理清楚，提示哪些事要先做、哪些话要谨慎说、哪些材料需要核验。"
      metrics={personalMetrics}
      cards={personalCards}
      actions={personalActions}
    />
  );
}
