import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Scale, TrendingUp, Shield, AlertCircle } from 'lucide-react';

export interface SuggestionData {
  rights_suggestions?: {
    can_claim_rights: string[];
    legal_basis?: string[];
    rights_analysis?: string;
  };
  amount_suggestions?: {
    recommended_amount: number | null;
    amount_breakdown?: Record<string, string>;
    amount_analysis?: string;
    max_possible?: string;
    realistic_expectation?: string;
  };
  defense_strategy?: {
    if_defendant: string;
    minimum_acceptable?: string;
    defense_points?: string[];
  };
  risk_assessment?: {
    win_probability: string;
    key_risks: string[];
    evidence_gaps?: string[];
    risk_mitigation?: string[];
  };
  summary_for_user?: string;
}

interface SuggestionCardsProps {
  suggestions: SuggestionData;
  onCalculateAmount?: (amount: number) => void;
}

export function SuggestionCards({ suggestions, onCalculateAmount }: SuggestionCardsProps) {
  if (!suggestions) return null;

  const legalBasis = suggestions.rights_suggestions?.legal_basis ?? [];
  const defensePoints = suggestions.defense_strategy?.defense_points ?? [];
  const evidenceGaps = suggestions.risk_assessment?.evidence_gaps ?? [];
  const riskMitigation = suggestions.risk_assessment?.risk_mitigation ?? [];

  return (
    <div className="space-y-3">
      {/* 权利建议 */}
      {suggestions.rights_suggestions && (
        <Card className="bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-700 dark:text-green-400 flex items-center gap-1">
              <Scale className="h-3.5 w-3.5" />
              建议主张的权利
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 space-y-1">
              {suggestions.rights_suggestions.can_claim_rights.map((r, i) => (
                <li key={i} className="text-sm">{r}</li>
              ))}
            </ul>
            {legalBasis.length > 0 && (
              <div className="mt-2 pt-2 border-t border-green-200 dark:border-green-800">
                <p className="text-xs text-green-600 dark:text-green-500 font-medium">法律依据</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {legalBasis.join('；')}
                </p>
              </div>
            )}
            {suggestions.rights_suggestions.rights_analysis && (
              <p className="mt-2 text-xs text-muted-foreground">
                {suggestions.rights_suggestions.rights_analysis}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 金额建议 */}
      {suggestions.amount_suggestions && (
        <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-blue-700 dark:text-blue-400 flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5" />
              建议主张金额
            </CardTitle>
          </CardHeader>
          <CardContent>
            {suggestions.amount_suggestions.recommended_amount != null && (
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  ¥{Number(suggestions.amount_suggestions.recommended_amount).toLocaleString()}
                </p>
                {onCalculateAmount && (
                  <button
                    type="button"
                    className="text-xs text-blue-600 underline-offset-2 hover:underline"
                    onClick={() =>
                      onCalculateAmount(Number(suggestions.amount_suggestions?.recommended_amount ?? 0))
                    }
                  >
                    使用
                  </button>
                )}
                {suggestions.amount_suggestions.realistic_expectation && (
                  <span className="text-xs text-blue-500">
                    ({suggestions.amount_suggestions.realistic_expectation})
                  </span>
                )}
              </div>
            )}
            {suggestions.amount_suggestions.amount_breakdown && (
              <div className="mt-2 space-y-1">
                {Object.entries(suggestions.amount_suggestions.amount_breakdown).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{key}</span>
                    <span className="font-medium">{value}</span>
                  </div>
                ))}
              </div>
            )}
            {suggestions.amount_suggestions.max_possible && (
              <p className="mt-2 text-xs text-muted-foreground">
                最高可主张：{suggestions.amount_suggestions.max_possible}
              </p>
            )}
            {suggestions.amount_suggestions.amount_analysis && (
              <p className="mt-2 text-xs text-muted-foreground">
                {suggestions.amount_suggestions.amount_analysis}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* 被告防守建议 */}
      {suggestions.defense_strategy && (
        <Card className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-amber-700 dark:text-amber-400 flex items-center gap-1">
              <Shield className="h-3.5 w-3.5" />
              被告防守建议
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{suggestions.defense_strategy.if_defendant}</p>
            {suggestions.defense_strategy.minimum_acceptable && (
              <div className="mt-2 pt-2 border-t border-amber-200 dark:border-amber-800">
                <p className="text-xs text-amber-600 dark:text-amber-500 font-medium">最低可接受</p>
                <p className="text-sm font-medium mt-0.5">
                  {suggestions.defense_strategy.minimum_acceptable}
                </p>
              </div>
            )}
            {defensePoints.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-muted-foreground font-medium">防守要点</p>
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  {defensePoints.map((point, i) => (
                    <li key={i} className="text-xs text-muted-foreground">{point}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 风险评估 */}
      {suggestions.risk_assessment && (
        <Card className="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-700 dark:text-red-400 flex items-center gap-1">
              <AlertCircle className="h-3.5 w-3.5" />
              风险评估
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">胜诉概率</span>
              <span className="text-lg font-bold text-red-600">{suggestions.risk_assessment.win_probability}</span>
            </div>
            {suggestions.risk_assessment.key_risks.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-muted-foreground font-medium">主要风险</p>
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  {suggestions.risk_assessment.key_risks.map((risk, i) => (
                    <li key={i} className="text-xs text-muted-foreground">{risk}</li>
                  ))}
                </ul>
              </div>
            )}
            {evidenceGaps.length > 0 && (
              <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-800">
                <p className="text-xs text-red-600 dark:text-red-500 font-medium">证据缺口</p>
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  {evidenceGaps.map((gap, i) => (
                    <li key={i} className="text-xs text-muted-foreground">{gap}</li>
                  ))}
                </ul>
              </div>
            )}
            {riskMitigation.length > 0 && (
              <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-800">
                <p className="text-xs text-green-600 dark:text-green-500 font-medium">风险缓解</p>
                <ul className="list-disc pl-5 mt-1 space-y-0.5">
                  {riskMitigation.map((mit, i) => (
                    <li key={i} className="text-xs text-muted-foreground">{mit}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 给用户的总结 */}
      {suggestions.summary_for_user && (
        <Card>
          <CardContent className="p-3">
            <p className="text-sm font-medium">给您的建议</p>
            <p className="text-sm text-muted-foreground mt-1">{suggestions.summary_for_user}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default SuggestionCards;
