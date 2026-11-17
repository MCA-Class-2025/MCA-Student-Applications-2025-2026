import api from './api';

export interface ChatSessionItem {
  id: number;
  title: string;
  created_at: string;
  message_count: number;
}

export interface SourceCitation {
  filename: string;
  chunk_index: number;
  relevance_score: number;
  snippet: string;
}

export interface ChatMessageItem {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  citations?: SourceCitation[];
}

export const chatApi = {
  createSession: async (title?: string): Promise<ChatSessionItem> => {
    const response = await api.post<ChatSessionItem>('/chat/sessions', { title });
    return response.data;
  },

  getSessions: async (): Promise<ChatSessionItem[]> => {
    const response = await api.get<ChatSessionItem[]>('/chat/sessions');
    return response.data;
  },

  getSessionMessages: async (sessionId: number): Promise<ChatMessageItem[]> => {
    const response = await api.get<ChatMessageItem[]>(`/chat/sessions/${sessionId}/messages`);
    return response.data;
  },

  deleteSession: async (sessionId: number): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },

  streamQuery: async (
    sessionId: number,
    query: string,
    onCitations: (citations: SourceCitation[]) => void,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: string) => void
  ) => {
    const token = localStorage.getItem('prepgenius_token');
    try {
      const response = await fetch('/api/v1/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ session_id: sessionId, query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      if (!reader) throw new Error('Response body is null');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.replace(/^data:\s*/, '').trim();
            if (!jsonStr) continue;

            try {
              const data = JSON.parse(jsonStr);
              if (data.type === 'citations') {
                onCitations(data.citations);
              } else if (data.type === 'token') {
                onToken(data.token);
              } else if (data.type === 'done') {
                onDone();
              }
            } catch (err) {
              console.error('Failed to parse SSE line:', line);
            }
          }
        }
      }
      onDone();
    } catch (err: any) {
      onError(err.message || 'RAG query stream failed');
    }
  },
};
