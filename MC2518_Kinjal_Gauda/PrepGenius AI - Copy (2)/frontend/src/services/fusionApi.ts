import api from './api';
import { WideFusedStudentProfile } from '../types';

export const fusionApi = {
  /**
   * Fetch single student dynamic wide fused profile from GET /api/v1/fusion/students/{student_id}/wide
   */
  async getWideProfile(studentId: string): Promise<WideFusedStudentProfile> {
    const response = await api.get<WideFusedStudentProfile>(`/fusion/students/${studentId}/wide`);
    return response.data;
  },

  /**
   * Trigger dynamic Excel download for a student from GET /api/v1/fusion/students/{student_id}/export-excel
   */
  async exportExcel(studentId: string): Promise<void> {
    const response = await api.get(`/fusion/students/${studentId}/export-excel`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `PrepGenius_Fused_${studentId}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Trigger complete 16-sheet master Data Fusion Excel download from GET /api/v1/fusion/export-master-excel
   */
  async exportMasterExcel(): Promise<void> {
    const response = await api.get('/fusion/export-master-excel', {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'PrepGenius_COMPLETE_DATA_FUSION.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

