import api from './api';

export interface DocumentItem {
  id: number;
  filename: string;
  file_type: 'pdf' | 'docx' | 'txt' | string;
  file_size: number;
  char_count: number;
  status: string;
  uploaded_at: string;
  extracted_text_preview?: string;
}

export interface DocumentDetail extends DocumentItem {
  extracted_text: string;
  file_path: string;
}

export const documentApi = {
  uploadDocument: async (file: File): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<DocumentItem>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getHistory: async (): Promise<DocumentItem[]> => {
    const response = await api.get<DocumentItem[]>('/documents/history');
    return response.data;
  },

  getDocumentDetails: async (id: number): Promise<DocumentDetail> => {
    const response = await api.get<DocumentDetail>(`/documents/${id}`);
    return response.data;
  },

  deleteDocument: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete<{ success: boolean; message: string }>(`/documents/${id}`);
    return response.data;
  },
};
