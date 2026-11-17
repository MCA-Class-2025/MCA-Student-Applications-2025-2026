import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { documentApi, DocumentItem } from '../../services/documentApi';

interface DocumentUploaderProps {
  onUploadSuccess: (doc: DocumentItem) => void;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'txt'].includes(ext)) {
      setError('Invalid file format. Please upload a PDF, DOCX, or TXT file.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setError('File size exceeds maximum allowed size of 25MB.');
      return;
    }

    setError(null);
    setSuccessMsg(null);
    setUploading(true);

    try {
      const doc = await documentApi.uploadDocument(file);
      setSuccessMsg(`Successfully uploaded "${doc.filename}" (${doc.char_count.toLocaleString()} characters extracted)`);
      onUploadSuccess(doc);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
          isDragging
            ? 'border-brand-indigo bg-brand-indigo/10 scale-[1.01]'
            : 'border-dark-border hover:border-brand-indigo/50 bg-dark-bg/40 hover:bg-dark-surface/40'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {uploading ? (
          <div className="space-y-3 py-2">
            <Loader2 className="w-8 h-8 text-brand-indigo animate-spin mx-auto" />
            <div className="text-xs font-semibold text-white">Extracting document text & processing metadata...</div>
            <p className="text-[10px] text-dark-muted">Parsing PDF / DOCX / TXT structure</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-brand-indigo/10 border border-brand-indigo/30 flex items-center justify-center mx-auto text-brand-indigo">
              <Upload className="w-6 h-6" />
            </div>
            <div className="text-sm font-bold text-white">Drop study files here or browse</div>
            <p className="text-xs text-dark-muted">Supports PDF, DOCX, TXT (Up to 25MB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-brand-rose text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 rounded-xl bg-brand-emerald/10 border border-brand-emerald/30 text-brand-emerald text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
