export interface LawItem {
  id: string;
  law_name: string;
  article_number: string;
  title?: string;
  category?: string;
  chapter?: string;
  effective_date?: string;
  content_preview?: string;
  content_length?: number;
  content?: string;
  is_valid?: boolean;
  source?: string;
}

export interface InterpretationItem {
  id: string;
  title: string;
  doc_number?: string;
  effective_date?: string;
  content_preview?: string;
  content?: string;
  is_valid?: boolean;
}

export interface GuidingCaseItem {
  id: string;
  title: string;
  case_number: string;
  case_type?: string;
  court?: string;
  publish_date?: string;
  summary_preview?: string;
  summary?: string;
  full_text?: string;
  keywords?: string[];
  related_articles?: string[];
  source?: string;
}

export interface LegalStats {
  total_laws: number;
  total_interpretations: number;
  total_guiding_cases: number;
  total_litigation_costs: number;
  total_document_templates: number;
  total_contract_templates: number;
}

export interface SearchResult {
  results: {
    laws: Array<{ id: string; law_name: string; article_number: string; title: string; type: string; preview: string }>;
    interpretations: Array<{ id: string; title: string; type: string; preview: string }>;
    cases: Array<{ id: string; title: string; type: string; preview: string }>;
  };
  total: number;
}
