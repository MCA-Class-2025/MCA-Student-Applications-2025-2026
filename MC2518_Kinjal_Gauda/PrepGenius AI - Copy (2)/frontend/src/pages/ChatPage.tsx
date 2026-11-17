import React, { useEffect, useState, useRef } from 'react';
import { Card } from '../components/ui/Card';
import { 
  MessageSquare, 
  Upload, 
  Sparkles, 
  Send, 
  Plus, 
  Trash2, 
  FileText, 
  BookOpen, 
  CheckCircle2,
  Bot,
  User,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { DocumentUploader } from '../components/documents/DocumentUploader';
import { DocumentHistoryList } from '../components/documents/DocumentHistoryList';
import { documentApi, DocumentItem } from '../services/documentApi';
import { chatApi, ChatSessionItem, ChatMessageItem, SourceCitation } from '../services/chatApi';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/Button';

export const ChatPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentCitations, setCurrentCitations] = useState<SourceCitation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchDocuments = async () => {
    if (!isAuthenticated) return;
    try {
      const history = await documentApi.getHistory();
      setDocuments(history);
    } catch (err) {
      console.error('Failed to load document history:', err);
    }
  };

  const fetchSessions = async () => {
    if (!isAuthenticated) return;
    try {
      const list = await chatApi.getSessions();
      setSessions(list);
      if (list.length > 0 && !activeSessionId) {
        setActiveSessionId(list[0].id);
      } else if (list.length === 0) {
        handleCreateSession();
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const handleCreateSession = async () => {
    if (!isAuthenticated) return;
    try {
      const newSession = await chatApi.createSession(`Session #${sessions.length + 1}`);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleDeleteSession = async (id: number) => {
    try {
      await chatApi.deleteSession(id);
      const remaining = sessions.filter((s) => s.id !== id);
      setSessions(remaining);
      if (activeSessionId === id) {
        setActiveSessionId(remaining[0]?.id || null);
        setMessages([]);
      }
    } catch (err) {
      alert('Failed to delete session');
    }
  };

  useEffect(() => {
    fetchDocuments();
    fetchSessions();
  }, [isAuthenticated]);

  useEffect(() => {
    const loadMessages = async () => {
      if (activeSessionId && isAuthenticated) {
        try {
          const history = await chatApi.getSessionMessages(activeSessionId);
          setMessages(history);
        } catch (err) {
          console.error('Failed to load session messages:', err);
        }
      }
    };
    loadMessages();
  }, [activeSessionId, isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSendQuery = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || !activeSessionId || isStreaming) return;

    const query = inputQuery.trim();
    setInputQuery('');
    setCurrentCitations([]);

    // Append User Message to local state
    const userMsg: ChatMessageItem = {
      id: Date.now(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    // Placeholder for Assistant streaming token response
    const assistantMsgId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
      },
    ]);

    let accumulatedText = '';

    await chatApi.streamQuery(
      activeSessionId,
      query,
      (citations) => {
        setCurrentCitations(citations);
      },
      (token) => {
        accumulatedText += token;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: accumulatedText } : msg
          )
        );
      },
      () => {
        setIsStreaming(false);
      },
      (err) => {
        console.error('Streaming error:', err);
        setIsStreaming(false);
      }
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-brand-indigo" />
            <span>AI Tutor Chat & RAG Engine</span>
          </h1>
          <p className="text-sm text-dark-muted">
            Ask context-grounded questions with FAISS semantic search, SentenceTransformers, & Ollama Qwen2.5 streaming.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={handleCreateSession}
          >
            New Session
          </Button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        {/* Left Sidebar: Document Context & Sessions */}
        <Card className="lg:col-span-1 flex flex-col justify-between space-y-4 overflow-y-auto" hoverEffect={false}>
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
              <span>Study Materials ({documents.length})</span>
              <span className="text-[10px] text-brand-indigo font-semibold">FAISS Ready</span>
            </h3>

            {isAuthenticated ? (
              <DocumentUploader onUploadSuccess={() => fetchDocuments()} />
            ) : (
              <div className="p-3 rounded-xl bg-brand-indigo/10 border border-brand-indigo/30 text-brand-indigo text-xs text-center">
                Sign in to upload PDF, DOCX, or TXT notes.
              </div>
            )}

            <div className="border-t border-dark-border pt-3 space-y-2">
              <span className="text-xs font-bold text-dark-muted uppercase tracking-wider block">
                Chat Memory Sessions ({sessions.length})
              </span>

              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => setActiveSessionId(s.id)}
                    className={`p-2.5 rounded-xl border text-xs cursor-pointer flex items-center justify-between transition-all ${
                      activeSessionId === s.id
                        ? 'bg-brand-indigo/20 border-brand-indigo/40 text-white font-semibold'
                        : 'bg-dark-surface/50 border-dark-border text-dark-muted hover:text-white hover:bg-dark-surface'
                    }`}
                  >
                    <div className="truncate max-w-[130px]">{s.title}</div>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.id); }}
                      className="p-1 rounded hover:bg-brand-rose/20 text-dark-muted hover:text-brand-rose"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Right Area: Chat Messages & Citations */}
        <Card className="lg:col-span-3 flex flex-col justify-between" hoverEffect={false}>
          {/* Active Citations Header */}
          {currentCitations.length > 0 && (
            <div className="p-3 mb-3 rounded-2xl bg-brand-indigo/10 border border-brand-indigo/30 space-y-2">
              <div className="text-xs font-bold text-brand-indigo flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5" />
                <span>FAISS Source Citations ({currentCitations.length})</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {currentCitations.map((c, i) => (
                  <div key={i} className="p-2 rounded-xl bg-dark-bg/80 border border-dark-border text-[11px] space-y-0.5">
                    <div className="flex items-center justify-between font-bold text-white">
                      <span className="truncate max-w-[140px]">{c.filename}</span>
                      <span className="text-brand-emerald font-mono">{(c.relevance_score * 100).toFixed(1)}% match</span>
                    </div>
                    <p className="text-dark-muted line-clamp-1 text-[10px]">{c.snippet}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto space-y-4 p-4 rounded-2xl bg-dark-bg/50 border border-dark-border/60">
            {messages.length === 0 ? (
              <div className="text-center py-16 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-indigo to-brand-violet flex items-center justify-center mx-auto text-white shadow-lg">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-white">Start RAG Study Query</h3>
                <p className="text-xs text-dark-muted max-w-md mx-auto">
                  Upload study documents on the left, then ask questions. PrepGenius AI will perform vector search and stream answers.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-indigo to-brand-violet flex items-center justify-center text-white shrink-0 text-xs font-bold shadow">
                      AI
                    </div>
                  )}

                  <div
                    className={`max-w-2xl p-4 rounded-2xl text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-brand-indigo to-brand-violet text-white shadow-md'
                        : 'bg-dark-surface border border-dark-border text-dark-text'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.content || (isStreaming ? 'Thinking & querying vector index...' : '')}</div>
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-dark-surface border border-dark-border flex items-center justify-center text-white shrink-0 text-xs font-bold">
                      <User className="w-4 h-4 text-brand-indigo" />
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <form onSubmit={handleSendQuery} className="mt-4 pt-3 border-t border-dark-border flex items-center gap-3">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask any question about your uploaded PDF/DOCX/TXT study notes..."
              className="flex-1 bg-dark-surface border border-dark-border rounded-xl px-4 py-3 text-sm text-white placeholder-dark-muted focus:outline-none focus:border-brand-indigo/60"
              disabled={isStreaming}
            />
            <Button
              type="submit"
              variant="glow"
              size="md"
              disabled={isStreaming || !inputQuery.trim()}
              icon={isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            >
              {isStreaming ? 'Streaming...' : 'Ask AI'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};
