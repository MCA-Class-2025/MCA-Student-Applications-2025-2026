import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { FileText, Volume2, Play, Pause, Download, Sparkles, Copy, Globe, Loader2, Square } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { studyApi } from '../services/studyApi';
import { documentApi, DocumentItem } from '../services/documentApi';
import { useAuth } from '../contexts/AuthContext';
import { useSpeech } from '../hooks/useSpeech';
import { exportToPDF } from '../utils/pdfExport';

export const SummarizerPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { isPlaying, isPaused, speakText, pauseSpeech, resumeSpeech, stopSpeech } = useSpeech();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [rawText, setRawText] = useState('');
  const [summaryType, setSummaryType] = useState('quick');
  const [language, setLanguage] = useState('English');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      documentApi.getHistory().then(setDocuments).catch(console.error);
    }
  }, [isAuthenticated]);

  const summaryModes = [
    { id: 'quick', label: 'Quick Summary' },
    { id: 'detailed', label: 'Detailed Summary' },
    { id: 'bullet', label: 'Bullet Points' },
    { id: 'keypoints', label: 'Key Highlights' },
    { id: 'definitions', label: 'Terms & Definitions' },
  ];

  const languages = ['English', 'Hindi', 'Marathi'];

  const handleGenerate = async () => {
    setLoading(true);
    stopSpeech();
    try {
      const docIds = selectedDocId ? [selectedDocId] : undefined;
      const res = await studyApi.summarize(docIds, rawText, summaryType, language);
      setSummary(res.summary);
    } catch (err: any) {
      alert(err.message || 'Failed to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  const handleAudioToggle = () => {
    if (!summary) return;
    if (isPlaying) {
      if (isPaused) resumeSpeech();
      else pauseSpeech();
    } else {
      speakText(summary, language);
    }
  };

  const handleExportPDF = () => {
    if (!summary) return;
    const html = `<div style="white-space: pre-wrap;">${summary}</div>`;
    exportToPDF(`Smart Summary (${summaryType.toUpperCase()} - ${language})`, html, `PrepGenius_Summary_${summaryType}.pdf`);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-brand-violet" />
            <span>Smart AI Summarizer & Audio Reader</span>
          </h1>
          <p className="text-sm text-dark-muted">
            Generate Quick, Detailed, Bullet, Key Points, or Definitions summaries in English, Hindi, or Marathi with Text-to-Speech audio.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {summary && (
            <Button variant="outline" size="sm" icon={<Download className="w-4 h-4" />} onClick={handleExportPDF}>
              Export PDF
            </Button>
          )}
        </div>
      </div>

      {/* Summary Type Selector Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-2 rounded-2xl bg-dark-card border border-dark-border">
        <div className="flex flex-wrap items-center gap-2">
          {summaryModes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => setSummaryType(mode.id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                summaryType === mode.id
                  ? 'bg-brand-violet text-white shadow-md shadow-brand-violet/30'
                  : 'text-dark-muted hover:text-white hover:bg-dark-surface'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* Multi-language Selector */}
        <div className="flex items-center gap-2 bg-dark-bg px-3 py-1.5 rounded-xl border border-dark-border">
          <Globe className="w-4 h-4 text-brand-indigo" />
          <span className="text-xs text-dark-muted font-medium">Language:</span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-transparent text-xs font-bold text-white focus:outline-none cursor-pointer"
          >
            {languages.map((l) => (
              <option key={l} value={l} className="bg-dark-card text-white">
                {l}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Source Text Input */}
        <Card className="lg:col-span-1 space-y-4" hoverEffect={false}>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Source Material</h3>

          {documents.length > 0 && (
            <div>
              <label className="text-xs text-dark-muted mb-1 block">Select Uploaded Document</label>
              <select
                value={selectedDocId || ''}
                onChange={(e) => {
                  const val = e.target.value ? Number(e.target.value) : null;
                  setSelectedDocId(val);
                }}
                className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-violet"
              >
                <option value="">-- All Uploaded Documents --</option>
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.filename} ({d.char_count} chars)
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="text-xs text-dark-muted mb-1 block">Or Paste Raw Study Text</label>
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste lecture notes, research text, or textbook excerpt here..."
              className="w-full h-48 bg-dark-bg/60 border border-dark-border rounded-xl p-3 text-xs text-white placeholder-dark-muted focus:outline-none focus:border-brand-violet resize-none"
            />
          </div>

          <Button
            variant="glow"
            className="w-full"
            disabled={loading}
            icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            onClick={handleGenerate}
          >
            {loading ? 'Generating AI Summary...' : `Summarize in ${language}`}
          </Button>
        </Card>

        {/* Output & TTS Player */}
        <Card className="lg:col-span-2 space-y-4 flex flex-col justify-between" hoverEffect={false}>
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-dark-border">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Summary Output</h3>
                <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-brand-violet/20 text-brand-violet border border-brand-violet/30">
                  {summaryType.toUpperCase()} • {language}
                </span>
              </div>

              {/* Audio TTS Controls */}
              {summary && (
                <div className="flex items-center gap-2 bg-dark-surface px-3 py-1.5 rounded-xl border border-dark-border">
                  <Volume2 className="w-4 h-4 text-brand-violet" />
                  <button
                    onClick={handleAudioToggle}
                    className="flex items-center gap-1.5 text-xs font-semibold text-white hover:text-brand-violet transition-colors"
                  >
                    {isPlaying && !isPaused ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                    <span>{isPlaying && !isPaused ? 'Pause Audio' : isPaused ? 'Resume' : 'Read Aloud'}</span>
                  </button>

                  {isPlaying && (
                    <button onClick={stopSpeech} title="Stop Audio" className="text-brand-rose hover:text-white pl-2 border-l border-dark-border">
                      <Square className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}
            </div>

            <div className="p-5 rounded-2xl bg-dark-bg/60 border border-dark-border text-sm text-dark-text leading-relaxed font-sans min-h-64 whitespace-pre-wrap">
              {summary || (
                <div className="text-center py-16 text-dark-muted text-xs">
                  Select a document or paste study notes on the left, then click <strong>Summarize</strong>.
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
