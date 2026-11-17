import api from './api';

export interface FlashcardItem {
  id: number;
  question: string;
  answer: string;
  difficulty: 'easy' | 'medium' | 'hard' | string;
}

export interface MCQItem {
  id: number;
  question: string;
  options: string[];
  correct_option: number;
  explanation: string;
}

export interface AnalyticsData {
  uploaded_notes_count: number;
  total_characters_processed: number;
  questions_asked_count: number;
  study_time_hours: number;
  quiz_accuracy_percentage: number;
  exam_readiness_score: number;
}

export const studyApi = {
  summarize: async (documentIds?: number[], rawText?: string, summaryMode: string = 'quick', language: string = 'English') => {
    const response = await api.post<{ summary: string; mode: string; language: string }>('/study/summarize', {
      document_ids: documentIds,
      raw_text: rawText,
      summary_mode: summaryMode,
      language: language,
    });
    return response.data;
  },

  generateFlashcards: async (documentIds?: number[], rawText?: string, count: number = 5): Promise<FlashcardItem[]> => {
    const response = await api.post<FlashcardItem[]>('/study/flashcards', {
      document_ids: documentIds,
      raw_text: rawText,
      count: count,
    });
    return response.data;
  },

  generateMCQs: async (documentIds?: number[], rawText?: string, count: number = 5): Promise<MCQItem[]> => {
    const response = await api.post<MCQItem[]>('/study/mcqs', {
      document_ids: documentIds,
      raw_text: rawText,
      count: count,
    });
    return response.data;
  },

  generateRevisionNotes: async (documentIds?: number[], rawText?: string, language: string = 'English') => {
    const response = await api.post<{ notes: string; language: string }>('/study/revision-notes', {
      document_ids: documentIds,
      raw_text: rawText,
      language: language,
    });
    return response.data;
  },

  generatePlanner: async (documentIds?: number[], daysUntilExam: number = 7) => {
    const response = await api.post('/study/planner', {
      document_ids: documentIds,
      days_until_exam: daysUntilExam,
    });
    return response.data;
  },

  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await api.get<AnalyticsData>('/study/analytics');
    return response.data;
  },
};
