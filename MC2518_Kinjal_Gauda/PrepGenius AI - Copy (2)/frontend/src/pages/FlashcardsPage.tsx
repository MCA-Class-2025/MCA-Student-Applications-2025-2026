import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Layers, RotateCw, Sparkles, ArrowLeft, ArrowRight, Check, X, Download, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { studyApi, FlashcardItem } from '../services/studyApi';
import { useAuth } from '../contexts/AuthContext';
import { exportToPDF } from '../utils/pdfExport';

export const FlashcardsPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [cards, setCards] = useState<FlashcardItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [masteredCount, setMasteredCount] = useState(0);

  const handleGenerateDeck = async () => {
    setLoading(true);
    try {
      const generated = await studyApi.generateFlashcards(undefined, undefined, 5);
      setCards(generated);
      setCurrentIndex(0);
      setIsFlipped(false);
      setMasteredCount(0);
    } catch (err: any) {
      alert(err.message || 'Failed to generate flashcards deck.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (cards.length === 0) {
      handleGenerateDeck();
    }
  }, []);

  const currentCard = cards[currentIndex] || {
    question: "What is Retrieval-Augmented Generation (RAG)?",
    answer: "RAG combines vector retrieval of document chunks (FAISS) with LLM generation (Ollama Qwen2.5) for accurate answers.",
    difficulty: "medium"
  };

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % (cards.length || 1));
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + (cards.length || 1)) % (cards.length || 1));
  };

  const handleMarkMastered = () => {
    setMasteredCount((prev) => prev + 1);
    handleNext();
  };

  const handleExportPDF = () => {
    const html = `
      <h3>Flashcard Study Deck (${cards.length} Cards)</h3>
      ${cards.map((c, i) => `
        <div class="card">
          <strong>Card #${i + 1} [${c.difficulty.toUpperCase()}]</strong>
          <p><strong>Q:</strong> ${c.question}</p>
          <p><strong>A:</strong> ${c.answer}</p>
        </div>
      `).join('')}
    `;
    exportToPDF('Flashcard Study Deck', html, 'PrepGenius_Flashcards.pdf');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-brand-emerald" />
            <span>Interactive Flashcard Generator</span>
          </h1>
          <p className="text-sm text-dark-muted">
            Auto-generate spaced repetition flashcard decks from your study materials powered by Ollama Qwen2.5.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {cards.length > 0 && (
            <Button variant="outline" size="sm" icon={<Download className="w-4 h-4" />} onClick={handleExportPDF}>
              Export Deck PDF
            </Button>
          )}
          <Button
            variant="glow"
            size="sm"
            disabled={loading}
            icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            onClick={handleGenerateDeck}
          >
            {loading ? 'Generating Deck...' : 'Generate New Deck'}
          </Button>
        </div>
      </div>

      {/* 3D Flippable Card Demo Area */}
      <div className="flex flex-col items-center justify-center py-8 space-y-6">
        <div 
          onClick={() => setIsFlipped(!isFlipped)}
          className="w-full max-w-xl h-80 cursor-pointer perspective-1000"
        >
          <div className={`relative w-full h-full rounded-3xl p-8 glass-card border border-brand-emerald/40 shadow-2xl flex flex-col justify-between transition-transform duration-500 transform ${isFlipped ? 'rotate-y-180' : ''}`}>
            <div className="flex items-center justify-between text-xs text-dark-muted">
              <span>Card {currentIndex + 1} of {cards.length || 1}</span>
              <span className="flex items-center gap-1 text-brand-emerald font-semibold">
                <RotateCw className="w-3.5 h-3.5" />
                <span>Click card to flip</span>
              </span>
            </div>

            <div className="text-center py-6">
              {!isFlipped ? (
                <div className="space-y-3">
                  <span className="text-xs font-semibold uppercase text-brand-emerald tracking-wider">Question</span>
                  <h3 className="text-xl font-bold text-white leading-relaxed">{currentCard.question}</h3>
                </div>
              ) : (
                <div className="space-y-3">
                  <span className="text-xs font-semibold uppercase text-brand-cyan tracking-wider">Answer Explanation</span>
                  <p className="text-sm text-dark-text leading-relaxed font-sans">{currentCard.answer}</p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between text-[11px] text-dark-muted border-t border-dark-border/50 pt-2">
              <span className="capitalize font-semibold text-brand-indigo">Difficulty: {currentCard.difficulty}</span>
              <span>{isFlipped ? 'Answer View' : 'Question View'}</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-4">
          <Button variant="outline" size="md" icon={<ArrowLeft className="w-4 h-4" />} onClick={handlePrev}>
            Previous
          </Button>
          <button
            onClick={handleNext}
            title="Needs Review"
            className="p-3 rounded-2xl bg-brand-rose/20 text-brand-rose hover:bg-brand-rose/30 border border-brand-rose/30 transition-colors flex items-center gap-2 text-xs font-bold"
          >
            <X className="w-4 h-4" />
            <span>Need Review</span>
          </button>
          <button
            onClick={handleMarkMastered}
            title="Got It Right"
            className="p-3 rounded-2xl bg-brand-emerald/20 text-brand-emerald hover:bg-brand-emerald/30 border border-brand-emerald/30 transition-colors flex items-center gap-2 text-xs font-bold"
          >
            <Check className="w-4 h-4" />
            <span>Got It Right (+1)</span>
          </button>
          <Button variant="outline" size="md" icon={<ArrowRight className="w-4 h-4" />} onClick={handleNext}>
            Next
          </Button>
        </div>

        {/* Stats */}
        <div className="text-xs text-dark-muted">
          Mastered this session: <span className="font-bold text-brand-emerald">{masteredCount}</span> / {cards.length || 1}
        </div>
      </div>
    </div>
  );
};
