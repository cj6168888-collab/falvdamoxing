import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { isCompanyInfoUnavailableError } from '@/api/company.api';
import type { CompanyInfo, CompanyScore, CompanyComparison, CompanySearchParams } from '@/types/company-check.types';
import {
  Search,
  Building2,
  AlertTriangle,
  XCircle,
  Shield,
  Link2,
  ExternalLink,
  MapPin,
  Phone,
  Mail,
  Globe,
  Users,
  ChevronRight,
  RefreshCw,
  Copy,
} from 'lucide-react';

// Company Search Component
interface CompanySearchProps {
  onSearch: (params: CompanySearchParams) => Promise<CompanyInfo[]>;
  onSelect: (company: CompanyInfo) => void;
}

export function CompanySearch({ onSearch, onSelect }: CompanySearchProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<CompanyInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    setError(null);
    
    try {
      const companies = await onSearch({ name: query });
      setResults(companies);
    } catch (err) {
      setError(isCompanyInfoUnavailableError(err) ? err.message : '搜索失败，请稍后重试');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [query, onSearch]);

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入企业名称、统一社会信用代码或注册号..."
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={isSearching}>
          {isSearching ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          搜索
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-destructive/10 text-destructive rounded-lg flex items-center gap-2">
          <XCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Results */}
      <div className="space-y-2">
        {results.map((company) => (
          <Card
            key={company.creditCode}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onSelect(company)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {company.logoUrl ? (
                    <img src={company.logoUrl} alt="" className="w-12 h-12 rounded" />
                  ) : (
                    <div className="w-12 h-12 bg-muted rounded flex items-center justify-center">
                      <Building2 className="h-6 w-6 text-muted-foreground" />
                    </div>
                  )}
                  <div>
                    <h4 className="font-medium">{company.name}</h4>
                    <p className="text-sm text-muted-foreground">{company.creditCode}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={company.status === '在业' ? 'default' : 'secondary'}>
                        {company.status}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        法定代表人: {company.legalPerson}
                      </span>
                    </div>
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Company Detail Component
interface CompanyDetailProps {
  company: CompanyInfo;
  score?: CompanyScore;
}

export function CompanyDetail({ company, score }: CompanyDetailProps) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            {company.logoUrl ? (
              <img src={company.logoUrl} alt="" className="w-20 h-20 rounded-lg" />
            ) : (
              <div className="w-20 h-20 bg-muted rounded-lg flex items-center justify-center">
                <Building2 className="h-10 w-10 text-muted-foreground" />
              </div>
            )}
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold">{company.name}</h2>
                <Badge variant={company.status === '在业' ? 'default' : 'secondary'}>
                  {company.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{company.creditCode}</p>
              
              {/* Score */}
              {score && (
                <div className="mt-3 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-primary">{score.overall}</span>
                    <span className="text-sm text-muted-foreground">综合评分</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Shield
                        key={i}
                        className={`h-4 w-4 ${
                          i < Math.floor(score.overall / 20)
                            ? 'text-primary fill-primary'
                            : 'text-muted-foreground'
                        }`}
                      />
                    ))}
                  </div>
                  <Badge variant="outline">{score.creditRating}</Badge>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            基本信息
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <InfoItem label="法定代表人" value={company.legalPerson} />
            <InfoItem label="注册资本" value={company.registeredCapital} />
            <InfoItem label="成立日期" value={company.establishmentDate} />
            <InfoItem label="营业期限" value={company.businessTerm} />
            <InfoItem label="企业类型" value={company.organizationType} />
            <InfoItem label="所属行业" value={company.industry} />
          </div>
          <Separator className="my-4" />
          <InfoItem 
            label="注册地址" 
            value={company.registeredAddress}
            icon={<MapPin className="h-4 w-4" />}
          />
          <InfoItem 
            label="经营范围" 
            value={company.businessScope}
            className="mt-4"
          />
        </CardContent>
      </Card>

      {/* Contact Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Phone className="h-4 w-4" />
            联系方式
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {company.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span>{company.phone}</span>
                <Button variant="ghost" size="sm" className="ml-auto">
                  <Copy className="h-3 w-3 mr-1" />复制
                </Button>
              </div>
            )}
            {company.email && (
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <span>{company.email}</span>
              </div>
            )}
            {company.website && (
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  {company.website}
                </a>
                <ExternalLink className="h-3 w-3" />
              </div>
            )}
            {!company.phone && !company.email && !company.website && (
              <p className="text-muted-foreground text-sm">暂无联系方式</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Risks */}
      {company.risks && company.risks.length > 0 && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-4 w-4" />
              风险信息 ({company.risks.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {company.risks.map((risk, index) => (
                <div key={index} className={`p-3 rounded-lg ${getRiskColor(risk.level)}`}>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className={getRiskColor(risk.level)}>
                      {risk.type === 'lawsuit' ? '诉讼' : 
                       risk.type === 'execution' ? '执行' : 
                       risk.type === 'tax' ? '税务' : 
                       risk.type === 'credit' ? '信用' : '行政处罚'}
                    </Badge>
                    <span className="text-xs">{risk.date}</span>
                  </div>
                  <p className="font-medium mt-1">{risk.title}</p>
                  <p className="text-sm mt-1">{risk.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Shareholders */}
      {company.shareholders && company.shareholders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4" />
              股东信息
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {company.shareholders.map((sh, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                  <div>
                    <span className="font-medium">{sh.name}</span>
                    <Badge variant="outline" className="ml-2">
                      {sh.type === 'person' ? '自然人' : '企业'}
                    </Badge>
                  </div>
                  <div className="text-right">
                    {sh.contributionAmount && (
                      <p className="text-sm">{sh.contributionAmount}</p>
                    )}
                    {sh.contributionRatio && (
                      <p className="text-xs text-muted-foreground">{sh.contributionRatio}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Related Companies */}
      {company.relatedCompanies && company.relatedCompanies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Link2 className="h-4 w-4" />
              关联企业
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {company.relatedCompanies.map((rc, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                  <span>{rc.name}</span>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{rc.relationship}</Badge>
                    <Badge variant="secondary">{rc.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Company Comparison Component
interface CompanyComparisonViewProps {
  comparison: CompanyComparison;
}

export function CompanyComparisonView({ comparison }: CompanyComparisonViewProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">企业对比</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2 font-medium">对比项</th>
                {comparison.companies.map((c) => (
                  <th key={c.creditCode} className="text-left p-2 font-medium">
                    {c.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparison.comparisonItems.map((item, index) => (
                <tr key={index} className="border-b">
                  <td className="p-2 text-muted-foreground">{item.label}</td>
                  {comparison.companies.map((c) => (
                    <td key={c.creditCode} className="p-2">
                      {item.values[c.creditCode] || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

// Info Item Helper
function InfoItem({ 
  label, 
  value, 
  icon, 
  className = '' 
}: { 
  label: string; 
  value?: string; 
  icon?: React.ReactNode;
  className?: string;
}) {
  if (!value) return null;
  
  return (
    <div className={className}>
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        {icon}
        {label}
      </div>
      <p className="mt-1">{value}</p>
    </div>
  );
}
