import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Search, BookOpen, Scale, FileText, Database } from 'lucide-react';
import { useCases, useInterpretations, useLaws, useSemanticSearch, useStats } from '@/api/legal-knowledge.api';
import type { GuidingCaseItem, InterpretationItem, LawItem } from '@/types/legal-knowledge.types';

type KnowledgeDisplayItem = Record<string, unknown> & {
  id: string;
  title: string;
  preview?: string;
};

function lawTitle(law: LawItem) {
  return law.title || [law.law_name, law.article_number].filter(Boolean).join(' ') || '未命名法律法规';
}

function toDisplayItem(item: LawItem | InterpretationItem | GuidingCaseItem | KnowledgeDisplayItem): KnowledgeDisplayItem {
  const raw = item as Record<string, unknown>;
  return {
    ...raw,
    id: String(raw.id),
    title: 'law_name' in item ? lawTitle(item as LawItem) : String(raw.title || '未命名条目'),
  };
}

export default function LegalKnowledgePage() {
  const [keyword, setKeyword] = useState('');
  const [activeTab, setActiveTab] = useState('search');
  const [page, setPage] = useState(1);
  const [selectedItem, setSelectedItem] = useState<KnowledgeDisplayItem | null>(null);

  const { data: stats } = useStats();
  const { data: lawsData, isLoading: loadingLaws } = useLaws(keyword, undefined, undefined, page);
  const { data: interpsData, isLoading: loadingInterps } = useInterpretations(keyword, page);
  const { data: casesData, isLoading: loadingCases } = useCases(keyword, undefined, page);
  const { data: searchData, isLoading: loadingSearch } = useSemanticSearch(keyword);

  const handleSearch = () => {
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">法律知识库</h1>
        <p className="text-sm text-muted-foreground mt-1">法律法规、司法解释、指导性案例查询</p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="flex items-center gap-2"><BookOpen className="h-5 w-5 text-muted-foreground" /><div className="text-2xl font-bold">{stats.total_laws || 0}</div></div><p className="text-xs text-muted-foreground">法律法规</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-2"><Scale className="h-5 w-5 text-muted-foreground" /><div className="text-2xl font-bold">{stats.total_interpretations || 0}</div></div><p className="text-xs text-muted-foreground">司法解释</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-2"><FileText className="h-5 w-5 text-muted-foreground" /><div className="text-2xl font-bold">{stats.total_guiding_cases || 0}</div></div><p className="text-xs text-muted-foreground">指导案例</p></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-2"><Database className="h-5 w-5 text-muted-foreground" /><div className="text-2xl font-bold">{stats.total_litigation_costs || 0}</div></div><p className="text-xs text-muted-foreground">诉讼费用规则</p></CardContent></Card>
        </div>
      )}

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-10" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="搜索法律法规、司法解释、案例..." onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }} />
        </div>
        <Button onClick={handleSearch} disabled={!keyword.trim()}>搜索</Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="search">综合搜索</TabsTrigger>
          <TabsTrigger value="laws">法律法规</TabsTrigger>
          <TabsTrigger value="interpretations">司法解释</TabsTrigger>
          <TabsTrigger value="cases">指导案例</TabsTrigger>
        </TabsList>

        <TabsContent value="search">
          {loadingSearch ? <PageSkeleton /> : searchData ? (
            <div className="space-y-4">
              {searchData.total === 0 ? (
                <EmptyState title="未找到相关内容" description="请尝试其他关键词" />
              ) : (
                <>
                  {searchData.results?.laws?.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2 flex items-center gap-2"><BookOpen className="h-4 w-4" />法律法规 ({searchData.results.laws.length})</h3>
                      <div className="space-y-2">
                        {searchData.results.laws.map((item) => (
                          <Card key={item.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(item))}>
                            <CardContent className="p-3">
                              <p className="font-medium">{item.title}</p>
                              {item.preview && <p className="text-sm text-muted-foreground mt-1">{item.preview}</p>}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                  {searchData.results?.interpretations?.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2 flex items-center gap-2"><Scale className="h-4 w-4" />司法解释 ({searchData.results.interpretations.length})</h3>
                      <div className="space-y-2">
                        {searchData.results.interpretations.map((item) => (
                          <Card key={item.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(item))}>
                            <CardContent className="p-3">
                              <p className="font-medium">{item.title}</p>
                              {item.preview && <p className="text-sm text-muted-foreground mt-1">{item.preview}</p>}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                  {searchData.results?.cases?.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2 flex items-center gap-2"><FileText className="h-4 w-4" />指导案例 ({searchData.results.cases.length})</h3>
                      <div className="space-y-2">
                        {searchData.results.cases.map((item) => (
                          <Card key={item.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(item))}>
                            <CardContent className="p-3">
                              <p className="font-medium">{item.title}</p>
                              {item.preview && <p className="text-sm text-muted-foreground mt-1">{item.preview}</p>}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : (
            <EmptyState title="输入关键词开始搜索" description="支持搜索法律法规、司法解释和指导案例" />
          )}
        </TabsContent>

        <TabsContent value="laws">
          {loadingLaws ? <PageSkeleton /> : lawsData ? (
            <div className="space-y-3">
              {lawsData.total === 0 ? (
                <EmptyState title="未找到法律法规" description="请尝试其他关键词" />
              ) : (
                <>
                  {lawsData.laws.map((law) => (
                    <Card key={law.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(law))}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{lawTitle(law)}</p>
                            <div className="flex gap-2 mt-1">
                              {law.category && <Badge variant="outline">{law.category}</Badge>}
                            </div>
                            {law.content_preview && <p className="text-sm text-muted-foreground mt-2">{law.content_preview}</p>}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">共 {lawsData.total} 条</p>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                      <Button variant="outline" size="sm" disabled={page * 20 >= lawsData.total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <EmptyState title="输入关键词搜索法律法规" description="支持按标题、内容搜索" />
          )}
        </TabsContent>

        <TabsContent value="interpretations">
          {loadingInterps ? <PageSkeleton /> : interpsData ? (
            <div className="space-y-3">
              {interpsData.total === 0 ? (
                <EmptyState title="未找到司法解释" description="请尝试其他关键词" />
              ) : (
                <>
                  {interpsData.interpretations.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(item))}>
                      <CardContent className="p-4">
                        <p className="font-medium">{item.title}</p>
                        {item.doc_number && <p className="text-sm text-muted-foreground mt-1">{item.doc_number}</p>}
                        {item.content_preview && <p className="text-sm text-muted-foreground mt-2">{item.content_preview}</p>}
                      </CardContent>
                    </Card>
                  ))}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">共 {interpsData.total} 条</p>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                      <Button variant="outline" size="sm" disabled={page * 20 >= interpsData.total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <EmptyState title="输入关键词搜索司法解释" description="支持按标题、内容搜索" />
          )}
        </TabsContent>

        <TabsContent value="cases">
          {loadingCases ? <PageSkeleton /> : casesData ? (
            <div className="space-y-3">
              {casesData.total === 0 ? (
                <EmptyState title="未找到指导案例" description="请尝试其他关键词" />
              ) : (
                <>
                  {casesData.cases.map((item) => (
                    <Card key={item.id} className="cursor-pointer hover:border-primary/50" onClick={() => setSelectedItem(toDisplayItem(item))}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{item.title}</p>
                            <div className="flex gap-2 mt-1">
                              {item.case_number && <Badge variant="outline">{item.case_number}</Badge>}
                              {item.case_type && <Badge variant="secondary">{item.case_type}</Badge>}
                            </div>
                            {item.summary_preview && <p className="text-sm text-muted-foreground mt-2">{item.summary_preview}</p>}
                          </div>
                          {item.court && <p className="text-sm text-muted-foreground">{item.court}</p>}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">共 {casesData.total} 条</p>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</Button>
                      <Button variant="outline" size="sm" disabled={page * 20 >= casesData.total} onClick={() => setPage(p => p + 1)}>下一页</Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <EmptyState title="输入关键词搜索指导案例" description="支持按标题、要点、判决搜索" />
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={!!selectedItem} onOpenChange={(open) => { if (!open) setSelectedItem(null); }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{selectedItem?.title as string || '详情'}</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            {selectedItem && Object.entries(selectedItem).filter(([k]) => !['id', 'title', 'content_preview', 'key_points_preview', 'preview'].includes(k)).map(([key, value]) => (
              <div key={key}>
                <h4 className="font-medium text-sm text-muted-foreground capitalize">{key}</h4>
                <p className="text-sm mt-1 whitespace-pre-wrap">{typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}</p>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
