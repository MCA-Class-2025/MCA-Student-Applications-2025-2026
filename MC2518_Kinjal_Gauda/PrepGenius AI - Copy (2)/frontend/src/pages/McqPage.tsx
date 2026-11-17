import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { CheckSquare, Sparkles, HelpCircle, Download, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { studyApi, MCQItem } from '../services/studyApi';
import { exportToPDF } from '../utils/pdfExport';

export const McqPage: React.FC = () => {
  const [mcqs, setMcqs] = useState<MCQItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<{ [key: number]: number }>({});
  const [loading, setLoading] = useState(false);
  const [quizFinished, setQuizFinished] = useState(false);

  const handleGenerateQuiz = async () => {
    setLoading(true);
    setQuizFinished(false);
    setSelectedOptions({});
    try {
      const generated = await studyApi.generateMCQs(undefined, undefined, 5);
      setMcqs(generated);
      setCurrentIndex(0);
    } catch (err: any) {
      alert(err.message || 'Failed to generate MCQ quiz.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (mcqs.length === 0) {
      handleGenerateQuiz();
    }
  }, []);

  const currentMcq = mcqs[currentIndex] || {
    question: "Which component in PrepGenius AI performs vector similarity searches?",
    options: ["FAISS / NumPy Engine", "SQLite Table Index", "FastAPI Middleware", "React Router"],
    correct_option: 0,
    explanation: "FAISS and NumPy vector search engines calculate vector distances over document embeddings."
  };

  const handleSelectOption = (optIdx: number) => {
    if (selectedOptions[currentIndex] !== undefined) return; // Answer locked
    setSelectedOptions((prev) => ({ ...prev, [currentIndex]: optIdx }));
  };

  const calculateScore = () => {
    let score = 0;
    mcqs.forEach((m, i) => {
      if (selectedOptions[i] === m.correct_option) score += 1;
    });
    return score;
  };

  const handleExportPDF = () => {
    const score = calculateScore();
    const html = `
      <h3>MCQ Practice Test Results</h3>
      <p><strong>Final Score:</strong> ${score} / ${mcqs.length} (${((score / (mcqs.length || 1)) * 100).toFixed(1)}%)</p>
      ${mcqs.map((m, i) => `
        <div class="card">
          <strong>Question ${i + 1}: ${m.question}</strong>
          <ul>
            ${m.options.map((opt, idx) => `
              <li style="${idx === m.correct_option ? 'color: green; font-weight: bold;' : ''}">
                ${String.fromCharCode(65 + idx)}) ${opt} ${idx === m.correct_option ? '✓' : ''}
              </li>
            `).join('')}
          </ul>
          <p><em>Explanation: ${m.explanation}</em></p>
        </div>
      `).join('')}
    `;
    exportToPDF('MCQ Quiz Results', html, 'PrepGenius_MCQ_Quiz.pdf');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-brand-cyan" />
            <span>MCQ Quiz Generator</span>
          </h1>
          <p className="text-sm text-dark-muted">
            Auto-generate multiple choice practice tests with instant option grading and explanations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {mcqs.length > 0 && (
            <Button variant="outline" size="sm" icon={<Download className="w-4 h-4" />} onClick={handleExportPDF}>
              Export Quiz PDF
            </Button>
          )}
          <Button
            variant="glow"
            size="sm"
            disabled={loading}
            icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            onClick={handleGenerateQuiz}
          >
            {loading ? 'Generating Quiz...' : 'New AI Quiz'}
          </Button>
        </div>
      </div>

      <Card hoverEffect={false} className="space-y-6">
        <div className="flex items-center justify-between border-b border-dark-border pb-4">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-brand-cyan" />
            <span className="text-sm font-bold text-white">Question {currentIndex + 1} of {mcqs.length || 1}</span>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30 font-semibold">
            Score: {calculateScore()} / {mcqs.length || 1}
          </span>
        </div>

        <h3 className="text-lg font-bold text-white leading-relaxed">{currentMcq.question}</h3>

        <div className="space-y-3">
          {currentMcq.options.map((opt, idx) => {
            const isSelected = selectedOptions[currentIndex] === idx;
            const isCorrect = idx === currentMcq.correct_option;
            const isAnswered = selectedOptions[currentIndex] !== undefined;

            let cardStyles = "bg-dark-surface border-dark-border text-dark-muted hover:border-dark-hover";
            if (isAnswered) {
              if (isCorrect) {
                cardStyles = "bg-brand-emerald/15 border-brand-emerald/50 text-white font-semibold";
              } else if (isSelected) {
                cardStyles = "bg-brand-rose/15 border-brand-rose/50 text-white";
              }
            } else if (isSelected) {
              cardStyles = "bg-brand-cyan/20 border-brand-cyan text-white";
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelectOption(idx)}
                className={`w-full p-4 rounded-xl border text-left text-sm transition-all flex items-center justify-between ${cardStyles}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-7 h-7 rounded-lg bg-dark-bg border border-dark-border flex items-center justify-center text-xs font-bold text-white">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span>{opt}</span>
                </div>

                {isAnswered && (
                  <div>
                    {isCorrect && <CheckCircle2 className="w-5 h-5 text-brand-emerald" />}
                    {isSelected && !isCorrect && <XCircle className="w-5 h-5 text-brand-rose" />}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {selectedOptions[currentIndex] !== undefined && (
          <div className="p-4 rounded-xl bg-dark-bg/80 border border-dark-border space-y-1 text-xs">
            <span className="font-bold text-brand-cyan uppercase tracking-wider block">Answer Explanation</span>
            <p className="text-dark-text leading-relaxed">{currentMcq.explanation}</p>
          </div>
        )}

        <div className="flex items-center justify-between pt-4 border-t border-dark-border">
          <Button
            variant="outline"
            size="sm"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          >
            Previous Question
          </Button>

          <Button
            variant="primary"
            size="sm"
            disabled={currentIndex >= (mcqs.length || 1) - 1}
            onClick={() => setCurrentIndex((prev) => Math.min((mcqs.length || 1) - 1, prev + 1))}
          >
            Next Question
          </Button>
        </div>
      </Card>
    </div>
  );
};
