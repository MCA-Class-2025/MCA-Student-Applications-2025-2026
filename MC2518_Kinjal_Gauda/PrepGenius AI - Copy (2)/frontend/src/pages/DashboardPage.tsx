import React from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  BookOpen, 
  MessageSquare, 
  BrainCircuit, 
  CheckCircle2, 
  TrendingUp, 
  FileText, 
  ArrowRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { ActiveTab } from '../types';

interface DashboardPageProps {
  setActiveTab: (tab: ActiveTab) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ setActiveTab }) => {
  const quickActions = [
    {
      title: 'AI Tutor Chat (RAG)',
      description: 'Upload PDF, DOCX, or TXT documents and ask questions with stream responses.',
      icon: MessageSquare,
      color: 'indigo',
      tab: 'chat' as ActiveTab,
      badge: 'Multi-file RAG'
    },
    {
      title: 'Smart AI Summarizer',
      description: 'Generate Quick, Detailed, or Bullet summaries with built-in Text-to-Speech.',
      icon: FileText,
      color: 'violet',
      tab: 'summarizer' as ActiveTab,
      badge: 'Voice Audio'
    },
    {
      title: 'Flashcard Generator',
      description: 'Auto-extract key concepts into interactive 3D flippable flashcards.',
      icon: BookOpen,
      color: 'emerald',
      tab: 'flashcards' as ActiveTab,
      badge: 'Spaced Repetition'
    },
    {
      title: 'MCQ Quiz Generator',
      description: 'Generate dynamic multiple choice questions to test your comprehension.',
      icon: CheckCircle2,
      color: 'cyan',
      tab: 'mcqs' as ActiveTab,
      badge: 'Instant Scoring'
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-3xl p-8 glass-card border border-brand-indigo/30 bg-gradient-to-r from-brand-indigo/20 via-dark-card to-brand-violet/20"
      >
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-brand-indigo/20 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 space-y-4 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-indigo/20 border border-brand-indigo/40 text-brand-indigo text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Module 1 Ready • System Active</span>
          </div>

          <h1 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Accelerate Your Learning with <span className="bg-gradient-to-r from-brand-indigo via-brand-violet to-brand-cyan bg-clip-text text-transparent">PrepGenius AI</span>
          </h1>

          <p className="text-dark-muted text-base leading-relaxed">
            Your local AI learning ecosystem powered by Ollama Qwen2.5:3B, vector embeddings, and multi-modal study tools. Ask questions, generate flashcards, listen to audio summaries, and track exam readiness.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Button
              variant="glow"
              size="lg"
              icon={<MessageSquare className="w-5 h-5" />}
              onClick={() => setActiveTab('chat')}
            >
              Launch AI Tutor Chat
            </Button>

            <Button
              variant="outline"
              size="lg"
              icon={<BrainCircuit className="w-5 h-5" />}
              onClick={() => setActiveTab('summarizer')}
            >
              Summarize Notes
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Analytics Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card hoverEffect glowColor="indigo">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-muted">Exam Readiness Score</span>
            <div className="p-2 rounded-xl bg-brand-indigo/10 text-brand-indigo">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">88%</span>
            <span className="text-xs font-semibold text-brand-emerald">+5% this week</span>
          </div>
          <div className="mt-3 w-full bg-dark-surface rounded-full h-1.5 overflow-hidden">
            <div className="bg-gradient-to-r from-brand-indigo to-brand-cyan h-full rounded-full w-[88%]" />
          </div>
        </Card>

        <Card hoverEffect glowColor="violet">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-muted">Documents Processed</span>
            <div className="p-2 rounded-xl bg-brand-violet/10 text-brand-violet">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">0</span>
            <span className="text-xs text-dark-muted">PDF, DOCX, TXT</span>
          </div>
          <p className="text-xs text-dark-muted mt-3">Ready for upload in Module 3</p>
        </Card>

        <Card hoverEffect glowColor="emerald">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-muted">AI Queries Asked</span>
            <div className="p-2 rounded-xl bg-brand-emerald/10 text-brand-emerald">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">0</span>
            <span className="text-xs text-dark-muted">RAG Questions</span>
          </div>
          <p className="text-xs text-dark-muted mt-3">Connected to Ollama Qwen2.5</p>
        </Card>

        <Card hoverEffect glowColor="cyan">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-dark-muted">Active Security</span>
            <div className="p-2 rounded-xl bg-brand-cyan/10 text-brand-cyan">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">JWT Ready</span>
          </div>
          <p className="text-xs text-dark-muted mt-3">Module 2 Auth Integration</p>
        </Card>
      </div>

      {/* Quick Action Feature Grid */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-brand-indigo" />
          <span>Core AI Learning Tools</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {quickActions.map((action, i) => {
            const Icon = action.icon;
            return (
              <Card key={i} hoverEffect glowColor={action.color as any}>
                <div className="flex items-start justify-between">
                  <div className="p-3 rounded-2xl bg-dark-surface border border-dark-border text-brand-indigo">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-dark-surface text-dark-muted border border-dark-border">
                    {action.badge}
                  </span>
                </div>

                <div className="mt-4 space-y-2">
                  <h3 className="text-lg font-bold text-white">{action.title}</h3>
                  <p className="text-sm text-dark-muted leading-relaxed">{action.description}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-dark-border/60 flex items-center justify-between">
                  <span className="text-xs font-medium text-brand-indigo flex items-center gap-1 group">
                    <span>Explore module</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setActiveTab(action.tab)}
                  >
                    Open Tool
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};
