import { useMutation } from '@tanstack/react-query';
import { useEvidenceGuide, answerGuideQuestion } from '@/api/evidence-guide.api';

export function useEvidenceGuideHook(caseId: string) {
  return useEvidenceGuide(caseId);
}

export function useAnswerGuideQuestion() {
  return useMutation({
    mutationFn: ({ caseId, questionId, answer }: { caseId: string; questionId: string; answer: string }) =>
      answerGuideQuestion(caseId, questionId, answer),
  });
}
