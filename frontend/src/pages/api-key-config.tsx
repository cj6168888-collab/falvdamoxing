import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  Key,
  Eye,
  EyeOff,
  Copy,
  Check,
  Download,
  ExternalLink,
  Shield,
  Bot,
  Globe,
  FileText,
  Calendar,
  CheckCircle2,
  Loader2,
  Info,
} from 'lucide-react';

// ============ 类型定义 ============
interface ApiConfig {
  key: string;
  name: string;
  description: string;
  placeholder: string;
  docsUrl?: string;
  required: boolean;
  category: 'llm' | 'law' | 'calendar' | 'utility' | 'verification';
}

interface ConfigState {
  [key: string]: string;
}

// ============ API 配置定义 ============
const API_CONFIGS: ApiConfig[] = [
  // ============ 大模型配置 ============
  {
    key: 'DASHSCOPE_API_KEY',
    name: '阿里云通义千问 API Key',
    description: '用于调用通义千问大语言模型，支持文书生成、案件分析等功能',
    placeholder: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx',
    docsUrl: 'https://dashscope.console.aliyun.com/apiKey',
    required: true,
    category: 'llm',
  },
  {
    key: 'OLLAMA_BASE_URL',
    name: 'Ollama 服务地址',
    description: '本地 Ollama 服务地址，默认为 http://localhost:11434',
    placeholder: 'http://localhost:11434',
    docsUrl: 'https://ollama.ai',
    required: false,
    category: 'llm',
  },
  {
    key: 'OLLAMA_MODEL',
    name: 'Ollama 模型名称',
    description: '本地部署的大模型名称，如 llama2, gemma:2b, mistral 等',
    placeholder: 'llama2',
    docsUrl: 'https://ollama.ai/models',
    required: false,
    category: 'llm',
  },
  {
    key: 'LOCAL_EMBEDDING_MODEL',
    name: '本地 Embedding 模型',
    description: '用于文本向量化的本地模型，建议使用 paraphrase-multilingual-MiniLM-L12-v2',
    placeholder: 'paraphrase-multilingual-MiniLM-L12-v2',
    required: false,
    category: 'llm',
  },

  // ============ 法律检索 API ============
  {
    key: 'LAW_API_KEY',
    name: '法研开放平台 API Key',
    description: '用于裁判文书查询、律师信息检索等法律数据服务',
    placeholder: '输入法研开放平台 API Key',
    docsUrl: 'https://api.law.yibie.net',
    required: false,
    category: 'law',
  },
  {
    key: 'BAITEN_API_KEY',
    name: '佰腾大数据 API Key',
    description: '用于法律法规大数据检索、企业工商信息查询',
    placeholder: '输入佰腾大数据 API Key',
    docsUrl: 'https://www.baiten.cn',
    required: false,
    category: 'law',
  },
  {
    key: 'YILIAN_API_KEY',
    name: '易连数据 API Key',
    description: '用于司法综合数据查询，包括诉讼服务、失信查询等',
    placeholder: '输入易连数据 API Key',
    required: false,
    category: 'law',
  },

  // ============ 节假日/期限 API ============
  {
    key: 'HOLIDAY_API_KEY',
    name: '节假日 API Key',
    description: '用于精确的法定期限计算，支持法定节假日判断',
    placeholder: '输入节假日 API Key',
    docsUrl: 'https://www.juhe.cn/console/api/detail/39',
    required: false,
    category: 'calendar',
  },

  // ============ 企业信息验证 ============
  {
    key: 'COMPANY_INFO_API_BASE_URL',
    name: '企业工商信息 API 地址',
    description: '用于企业工商信息查询的服务地址',
    placeholder: 'https://provider.example.com/api',
    required: false,
    category: 'verification',
  },
  {
    key: 'COMPANY_INFO_API_KEY',
    name: '企业工商信息 API Key',
    description: '用于企业名称、统一社会信用代码、法定代表人等工商信息查询',
    placeholder: '输入企业工商信息 API Key',
    required: false,
    category: 'verification',
  },
  {
    key: 'CLEARBIT_API_KEY',
    name: 'Clearbit API Key',
    description: '用于自动获取企业 Logo 和公司信息增强展示',
    placeholder: '输入 Clearbit API Key',
    docsUrl: 'https://clearbit.com',
    required: false,
    category: 'verification',
  },
  {
    key: 'NUMVERIFY_API_KEY',
    name: 'Numverify API Key',
    description: '用于验证电话号码格式和国家归属',
    placeholder: '输入 Numverify API Key',
    docsUrl: 'https://numverify.com',
    required: false,
    category: 'verification',
  },
  {
    key: 'MAILBOX_VALIDATOR_API_KEY',
    name: 'MailboxValidator API Key',
    description: '用于验证邮箱地址的有效性和可送达性',
    placeholder: '输入 MailboxValidator API Key',
    docsUrl: 'https://mailboxvalidator.com',
    required: false,
    category: 'verification',
  },

  // ============ 文档处理 API ============
  {
    key: 'PDFLAYER_API_KEY',
    name: 'pdflayer API Key',
    description: '用于将网页或 HTML 内容转换为 PDF 文档',
    placeholder: '输入 pdflayer API Key',
    docsUrl: 'https://pdflayer.com',
    required: false,
    category: 'utility',
  },
  {
    key: 'OCR_SPACE_API_KEY',
    name: 'OCR.space API Key',
    description: '用于云端 OCR 文字识别，支持图片转文字',
    placeholder: '输入 OCR.space API Key',
    docsUrl: 'https://ocr.space/ocrapi',
    required: false,
    category: 'utility',
  },
];

// ============ 分类配置 ============
const CATEGORY_CONFIG = {
  llm: {
    label: '大模型配置',
    icon: Bot,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
  },
  law: {
    label: '法律数据API',
    icon: Globe,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
  },
  calendar: {
    label: '期限计算API',
    icon: Calendar,
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
  },
  verification: {
    label: '信息验证API',
    icon: Shield,
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
  },
  utility: {
    label: '工具类API',
    icon: FileText,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50 border-gray-200',
  },
};

// ============ 单个 API Key 输入组件 ============
interface ApiKeyInputProps {
  config: ApiConfig;
  value: string;
  onChange: (key: string, value: string) => void;
  onValidate?: (key: string) => Promise<boolean>;
}

function ApiKeyInput({ config, value, onChange, onValidate }: ApiKeyInputProps) {
  const [showKey, setShowKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validated, setValidated] = useState<boolean | null>(null);

  const categoryConfig = CATEGORY_CONFIG[config.category];
  const Icon = categoryConfig.icon;
  const hasValue = value && value.length > 0;

  const handleCopy = async () => {
    if (value) {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleValidate = async () => {
    if (!onValidate) return;
    setIsValidating(true);
    setValidated(null);
    try {
      const result = await onValidate(config.key);
      setValidated(result);
    } catch {
      setValidated(false);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${categoryConfig.color}`} />
          {config.name}
          {config.required && <span className="text-red-500">*</span>}
        </Label>
        <div className="flex items-center gap-2">
          {hasValue && (
            <>
              {validated !== null && (
                <Badge variant={validated ? 'default' : 'destructive'} className="text-xs">
                  {validated ? '已验证' : '验证失败'}
                </Badge>
              )}
              {onValidate && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleValidate}
                  disabled={isValidating}
                  className="h-6 px-2 text-xs"
                >
                  {isValidating ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3" />
                  )}
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-6 px-2 text-xs"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowKey(!showKey)}
            className="h-6 px-2 text-xs"
          >
            {showKey ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
          </Button>
        </div>
      </div>
      <div className="relative">
        <Input
          type={showKey ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(config.key, e.target.value)}
          placeholder={config.placeholder}
          className="pr-20 font-mono text-sm"
          autoComplete="off"
        />
        {config.docsUrl && (
          <a
            href={config.docsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        )}
      </div>
      <p className="text-xs text-muted-foreground">{config.description}</p>
    </div>
  );
}

// ============ 分类卡片组件 ============
interface CategoryCardProps {
  category: keyof typeof CATEGORY_CONFIG;
  configs: ApiConfig[];
  values: ConfigState;
  onChange: (key: string, value: string) => void;
  onValidate?: (key: string) => Promise<boolean>;
  completedCount: number;
  totalCount: number;
}

function CategoryCard({
  category,
  configs,
  values,
  onChange,
  onValidate,
  completedCount,
  totalCount,
}: CategoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const config = CATEGORY_CONFIG[category];
  const Icon = config.icon;

  return (
    <Card className={config.bgColor}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${config.color}`} />
            <CardTitle className="text-base">{config.label}</CardTitle>
            <Badge variant="secondary" className="text-xs">
              {completedCount}/{totalCount}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '收起' : '展开'}
          </Button>
        </div>
        <CardDescription>
          {completedCount === 0
            ? '暂未配置'
            : completedCount === totalCount
            ? '已全部配置'
            : `${totalCount - completedCount} 项待配置`}
        </CardDescription>
      </CardHeader>
      {isExpanded && (
        <CardContent className="space-y-4">
          {configs.map((cfg) => (
            <div key={cfg.key} className="p-3 bg-background/50 rounded-lg">
              <ApiKeyInput
                config={cfg}
                value={values[cfg.key] || ''}
                onChange={onChange}
                onValidate={onValidate}
              />
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  );
}

// ============ 主页面组件 ============
export default function ApiKeyConfigPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'all' | 'llm' | 'law' | 'calendar' | 'verification' | 'utility'>('all');
  const [configValues, setConfigValues] = useState<ConfigState>({});
  const [savedConfigs, setSavedConfigs] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // 加载配置
  useEffect(() => {
    const loadConfigs = async () => {
      try {
        const response = await fetch('/api/config/api-keys');
        if (response.ok) {
          const data = await response.json();
          const masked: ConfigState = {};
          const configs = data.configs || {};
          for (const [key, value] of Object.entries(configs)) {
            if (value && typeof value === 'string' && value.length > 0) {
              masked[key] = value;
            }
          }
          setConfigValues(masked);
        }
      } catch (error) {
        console.error('加载配置失败:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadConfigs();
  }, []);

  const handleConfigChange = useCallback((key: string, value: string) => {
    setConfigValues((prev) => ({ ...prev, [key]: value }));
    setSavedConfigs((prev) => {
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/config/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          configs: Object.fromEntries(
            Object.entries(configValues).filter(([, value]) => value && !value.includes('****')),
          ),
        }),
      });

      if (response.ok) {
        setSavedConfigs(new Set(Object.keys(configValues).filter((k) => configValues[k])));
        toast({
          title: '保存成功',
          description: 'API Key 配置已保存',
          variant: 'default',
        });
      } else {
        throw new Error('保存失败');
      }
    } catch (error) {
      toast({
        title: '保存失败',
        description: '请检查配置后重试',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportEnv = () => {
    const envContent = Object.entries(configValues)
      .filter(([_, value]) => value && !value.includes('****'))
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '.env';
    a.click();
    URL.revokeObjectURL(url);

    toast({
      title: '导出成功',
      description: '环境变量文件已导出为 .env',
    });
  };

  const handleReset = () => {
    setConfigValues({});
    setSavedConfigs(new Set());
    toast({
      title: '已重置',
      description: '所有配置已清空',
    });
  };

  // 按分类分组配置
  const groupedConfigs = API_CONFIGS.reduce((acc, config) => {
    if (!acc[config.category]) {
      acc[config.category] = [];
    }
    acc[config.category].push(config);
    return acc;
  }, {} as Record<string, ApiConfig[]>);

  // 计算每个分类的完成数量
  const getCategoryProgress = (category: string) => {
    const configs = groupedConfigs[category] || [];
    const completed = configs.filter(
      (c) => configValues[c.key] && !configValues[c.key].includes('****')
    ).length;
    return { completed, total: configs.length };
  };

  // 获取标签页配置
  const tabs = [
    { id: 'all', label: '全部', count: API_CONFIGS.length },
    { id: 'llm', label: '大模型', count: groupedConfigs.llm?.length || 0 },
    { id: 'law', label: '法律API', count: (groupedConfigs.law?.length || 0) + (groupedConfigs.calendar?.length || 0) },
    { id: 'verification', label: '验证API', count: groupedConfigs.verification?.length || 0 },
    { id: 'utility', label: '工具API', count: groupedConfigs.utility?.length || 0 },
  ];

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* 页面标题 */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Key className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">API Key 配置</h1>
            <p className="text-sm text-muted-foreground">
              管理大模型和第三方服务的 API 密钥配置
            </p>
          </div>
        </div>
      </div>

      {/* 重要提示 */}
      <Card className="mb-6 border-blue-200 bg-blue-50/50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-blue-900 mb-1">配置说明</p>
              <ul className="text-blue-800 space-y-1 list-disc list-inside">
                <li>所有 API Key 均通过环境变量配置，支持重启后持久化</li>
                <li>敏感信息会以掩码形式显示，不会明文保存在前端</li>
                <li>建议生产环境使用 Docker 环境变量或密钥管理服务</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="mb-6">
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="gap-2">
              {tab.label}
              <Badge variant="secondary" className="text-xs">
                {tab.count}
              </Badge>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* 配置内容 */}
      <div className="grid gap-6" aria-busy={isLoading}>
        {/* 大模型配置 */}
        {(activeTab === 'all' || activeTab === 'llm') && (
          <CategoryCard
            category="llm"
            configs={groupedConfigs.llm || []}
            values={configValues}
            onChange={handleConfigChange}
            completedCount={getCategoryProgress('llm').completed}
            totalCount={getCategoryProgress('llm').total}
          />
        )}

        {/* 法律数据API */}
        {(activeTab === 'all' || activeTab === 'law') && (
          <>
            <CategoryCard
              category="law"
              configs={groupedConfigs.law || []}
              values={configValues}
              onChange={handleConfigChange}
              completedCount={getCategoryProgress('law').completed}
              totalCount={getCategoryProgress('law').total}
            />
            <CategoryCard
              category="calendar"
              configs={groupedConfigs.calendar || []}
              values={configValues}
              onChange={handleConfigChange}
              completedCount={getCategoryProgress('calendar').completed}
              totalCount={getCategoryProgress('calendar').total}
            />
          </>
        )}

        {/* 信息验证API */}
        {(activeTab === 'all' || activeTab === 'verification') && (
          <CategoryCard
            category="verification"
            configs={groupedConfigs.verification || []}
            values={configValues}
            onChange={handleConfigChange}
            completedCount={getCategoryProgress('verification').completed}
            totalCount={getCategoryProgress('verification').total}
          />
        )}

        {/* 工具类API */}
        {(activeTab === 'all' || activeTab === 'utility') && (
          <CategoryCard
            category="utility"
            configs={groupedConfigs.utility || []}
            values={configValues}
            onChange={handleConfigChange}
            completedCount={getCategoryProgress('utility').completed}
            totalCount={getCategoryProgress('utility').total}
          />
        )}
      </div>

      {/* 操作按钮 */}
      <div className="mt-8 flex items-center justify-between pt-6 border-t">
        <div className="text-sm text-muted-foreground">
          {savedConfigs.size > 0 && (
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              已保存 {savedConfigs.size} 项配置
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleReset}>
            重置
          </Button>
          <Button variant="outline" onClick={handleExportEnv}>
            <Download className="h-4 w-4 mr-2" />
            导出 .env
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Check className="h-4 w-4 mr-2" />
                保存配置
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

