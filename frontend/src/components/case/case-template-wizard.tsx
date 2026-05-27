import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useCaseTemplate, fillFromTemplate } from '@/hooks/use-case-template';
import { useCaseCreate } from '@/hooks/use-case';
import type { Case } from '@/types/case.types';
import type { CaseTemplate } from '@/types/case-template.types';
import { useNavigate } from 'react-router-dom';
import { Check, Sparkles, FileText } from 'lucide-react';
import { CaseTemplateSelector } from './case-template-selector';
import { CaseTemplateForm } from './case-template-form';
import type { TemplateFormData } from './case-template-form';
import { CaseTemplatePreview } from './case-template-preview';

export type CaseCreationStep = 'select' | 'fill' | 'preview' | 'complete';

interface CaseTemplateWizardProps {
  onClose?: () => void;
  onCaseCreated?: (caseId: string) => void;
}

export function CaseTemplateWizard({ onClose, onCaseCreated }: CaseTemplateWizardProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<CaseCreationStep>('select');
  const [selectedTemplate, setSelectedTemplate] = useState<CaseTemplate | null>(null);
  const [formData, setFormData] = useState<TemplateFormData>({});
  const [useTemplateAutoFill, setUseTemplateAutoFill] = useState(true);
  
  const { data: templates = [], isLoading: templatesLoading } = useCaseTemplate();
  const createCaseMutation = useCaseCreate();

  const handleTemplateSelect = (template: CaseTemplate) => {
    setSelectedTemplate(template);
    
    // Auto-fill from template
    if (useTemplateAutoFill && template.autoFillFields.length > 0) {
      const autoFillData: TemplateFormData = {};
      template.autoFillFields.forEach(field => {
        if (template.fields.find(f => f.key === field)) {
          autoFillData[field] = '';
        }
      });
      setFormData(autoFillData);
    }
    
    setCurrentStep('fill');
  };

  const handleFillComplete = (filledData: TemplateFormData) => {
    setFormData(filledData);
    setCurrentStep('preview');
  };

  const handleCreate = async () => {
    let caseData: TemplateFormData = {
      ...formData,
      templateId: selectedTemplate?.id,
    };

    // Auto-fill with template suggestions
    if (useTemplateAutoFill && selectedTemplate) {
      caseData = fillFromTemplate(selectedTemplate, caseData);
    }

    try {
      const result = await createCaseMutation.mutateAsync(caseData as Partial<Case>);
      setCurrentStep('complete');
      
      if (onCaseCreated) {
        onCaseCreated(result.id);
      } else {
        navigate(`/cases/${result.id}`);
      }
    } catch (error) {
      console.error('Failed to create case:', error);
    }
  };

  const stepConfig = [
    { id: 'select', label: '选择模板', icon: FileText },
    { id: 'fill', label: '填写信息', icon: Sparkles },
    { id: 'preview', label: '确认创建', icon: Check },
  ];

  const currentStepIndex = stepConfig.findIndex(s => s.id === currentStep);

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>新建案件</CardTitle>
          {onClose && (
            <Button variant="ghost" onClick={onClose}>关闭</Button>
          )}
        </div>
        
        {/* Step Indicator */}
        <div className="flex items-center justify-between mt-4">
          {stepConfig.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStepIndex;
            const isCompleted = index < currentStepIndex;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className="flex items-center gap-2">
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center
                    ${isCompleted ? 'bg-green-600 text-white' : ''}
                    ${isActive ? 'bg-primary text-primary-foreground' : ''}
                    ${!isActive && !isCompleted ? 'bg-muted text-muted-foreground' : ''}
                  `}>
                    {isCompleted ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </div>
                  <span className={`text-sm ${isActive ? 'font-medium' : ''}`}>
                    {step.label}
                  </span>
                </div>
                {index < stepConfig.length - 1 && (
                  <div className={`w-16 h-0.5 mx-4 ${
                    index < currentStepIndex ? 'bg-green-600' : 'bg-muted'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </CardHeader>

      <CardContent className="p-6">
        {/* Template Selection */}
        {currentStep === 'select' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">选择案件模板</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  选择一个模板，系统将自动填充相关信息和推荐内容
                </p>
              </div>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={useTemplateAutoFill}
                  onChange={(e) => setUseTemplateAutoFill(e.target.checked)}
                  className="rounded border-input"
                />
                <span>启用自动填充</span>
                <Badge variant="secondary" className="ml-2">推荐</Badge>
              </label>
            </div>
            
            <CaseTemplateSelector
              templates={templates || []}
              onSelect={handleTemplateSelect}
              isLoading={templatesLoading}
            />
          </div>
        )}

        {/* Form Fill */}
        {currentStep === 'fill' && selectedTemplate && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">填写案件信息</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  模板：{selectedTemplate.name} - {selectedTemplate.description}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => setCurrentStep('select')}>
                更换模板
              </Button>
            </div>
            
            <CaseTemplateForm
              template={selectedTemplate}
              initialData={formData}
              onSubmit={handleFillComplete}
              onAutoFill={() => {
                const filled = fillFromTemplate(selectedTemplate, {});
                setFormData(filled);
              }}
              useAutoFill={useTemplateAutoFill}
            />
          </div>
        )}

        {/* Preview */}
        {currentStep === 'preview' && selectedTemplate && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium">确认案件信息</h3>
              <p className="text-sm text-muted-foreground mt-1">
                请确认以下信息，确认无误后点击创建
              </p>
            </div>
            
            <CaseTemplatePreview
              template={selectedTemplate}
              formData={formData}
              onEdit={() => setCurrentStep('fill')}
            />

            <div className="flex flex-col gap-2 pt-4">
              {createCaseMutation.error && (
                <span className="text-sm text-red-500">{String(createCaseMutation.error)}</span>
              )}
              <div className="flex justify-end">
                <Button onClick={handleCreate} disabled={createCaseMutation.isPending}>
                  {createCaseMutation.isPending ? '创建中...' : '创建案件'}
                  {!createCaseMutation.isPending && <Check className="h-4 w-4 ml-2" />}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Complete */}
        {currentStep === 'complete' && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-xl font-medium mb-2">案件创建成功</h3>
            <p className="text-muted-foreground mb-6">案件已成功创建，正在跳转...</p>
            <Button onClick={() => navigate('/cases')}>
              返回案件列表
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
