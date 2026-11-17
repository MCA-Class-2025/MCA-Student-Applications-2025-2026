import React, { useState } from 'react';
import { FileText, Trash2, Eye, File, FileCode, CheckCircle2 } from 'lucide-react';
import { DocumentItem, documentApi, DocumentDetail } from '../../services/documentApi';

interface DocumentHistoryListProps {
  documents: DocumentItem[];
  onRefresh: () => void;
}

export const DocumentHistoryList: React.FC<DocumentHistoryListProps> = ({ documents, onRefresh }) => {
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this document and its extracted text?')) {
      try {
        await documentApi.deleteDocument(id);
        onRefresh();
      } catch (err) {
        alert('Failed to delete document');
      }
    }
  };

  const handleView = async (id: number) => {
    setLoadingDetail(true);
    try {
      const detail = await documentApi.getDocumentDetails(id);
      setSelectedDoc(detail);
    } catch (err) {
      alert('Failed to load document text details.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const getIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf': return <FileText className="w-4 h-4 text-brand-rose" />;
      case 'docx': return <File className="w-4 h-4 text-brand-indigo" />;
      default: return <FileCode className="w-4 h-4 text-brand-cyan" />;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs font-bold text-dark-muted uppercase tracking-wider">
        <span>Uploaded Files History ({documents.length})</span>
        <button onClick={onRefresh} className="hover:text-white transition-colors">Refresh</button>
      </div>

      {documents.length === 0 ? (
        <div className="p-6 rounded-2xl bg-dark-bg/40 border border-dark-border text-center text-xs text-dark-muted">
          No documents uploaded yet. Upload a PDF, DOCX, or TXT file above.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="p-3.5 rounded-xl bg-dark-surface/70 border border-dark-border hover:border-brand-indigo/30 transition-all flex items-center justify-between text-xs group"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2 rounded-lg bg-dark-bg border border-dark-border shrink-0">
                  {getIcon(doc.file_type)}
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-white truncate max-w-[180px] sm:max-w-xs">
                    {doc.filename}
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-dark-muted mt-0.5">
                    <span className="uppercase font-bold text-brand-indigo">{doc.file_type}</span>
                    <span>•</span>
                    <span>{formatSize(doc.file_size)}</span>
                    <span>•</span>
                    <span className="text-brand-emerald">{doc.char_count.toLocaleString()} chars</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => handleView(doc.id)}
                  title="View Extracted Text"
                  className="p-1.5 rounded-lg hover:bg-dark-hover text-dark-muted hover:text-white transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleDelete(doc.id)}
                  title="Delete Document"
                  className="p-1.5 rounded-lg hover:bg-brand-rose/20 text-dark-muted hover:text-brand-rose transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Extracted Text Detail Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="w-full max-w-2xl glass-card rounded-3xl p-6 border border-brand-indigo/40 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-dark-border pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  {getIcon(selectedDoc.file_type)}
                  <span>{selectedDoc.filename}</span>
                </h3>
                <div className="text-xs text-dark-muted">
                  Extracted {selectedDoc.char_count.toLocaleString()} characters from SQLite record
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-3 py-1.5 rounded-xl bg-dark-surface hover:bg-dark-hover text-xs text-white"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 rounded-xl bg-dark-bg border border-dark-border font-mono text-xs text-dark-text whitespace-pre-wrap leading-relaxed">
              {selectedDoc.extracted_text || 'No text extracted from this file.'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
