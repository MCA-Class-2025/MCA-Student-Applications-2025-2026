import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Calendar, Clock, CheckCircle, Sparkles, Download, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { studyApi } from '../services/studyApi';
import { exportToPDF } from '../utils/pdfExport';

export const PlannerPage: React.FC = () => {
  const [days, setDays] = useState(7);
  const [planner, setPlanner] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGeneratePlanner = async () => {
    setLoading(true);
    try {
      const res = await studyApi.generatePlanner(undefined, days);
      setPlanner(res);
    } catch (err: any) {
      alert(err.message || 'Failed to generate study plan.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleGeneratePlanner();
  }, []);

  const handleExportPDF = () => {
    if (!planner) return;
    const html = `
      <h3>Smart Study & Revision Plan (${days} Days Until Exam)</h3>
      <h4>Daily Schedule</h4>
      ${planner.daily_plan?.map((d: any) => `
        <div class="card">
          <strong>${d.time}</strong> - ${d.task} (<em>${d.type}</em>)
        </div>
      `).join('')}

      <h4>Weekly Topic Breakdown</h4>
      ${planner.weekly_plan?.map((w: any) => `
        <div class="card">
          <strong>${w.day}: ${w.focus_topic}</strong>
          <ul>
            ${w.goals?.map((g: string) => `<li>${g}</li>`).join('')}
          </ul>
        </div>
      `).join('')}
    `;
    exportToPDF(`Study Planner (${days} Days)`, html, 'PrepGenius_Study_Plan.pdf');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-brand-indigo" />
            <span>Smart AI Study Planner</span>
          </h1>
          <p className="text-sm text-dark-muted">
            Daily & weekly automated revision schedules crafted by AI based on your exam deadline and syllabus.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {planner && (
            <Button variant="outline" size="sm" icon={<Download className="w-4 h-4" />} onClick={handleExportPDF}>
              Export Plan PDF
            </Button>
          )}
          <Button
            variant="glow"
            size="sm"
            disabled={loading}
            icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            onClick={handleGeneratePlanner}
          >
            {loading ? 'Calculating...' : 'Recalculate Schedule'}
          </Button>
        </div>
      </div>

      {/* Exam Deadline Selector Bar */}
      <div className="flex items-center justify-between p-4 rounded-2xl bg-dark-card border border-dark-border">
        <div className="flex items-center gap-3">
          <Clock className="w-5 h-5 text-brand-indigo" />
          <div>
            <div className="text-xs font-bold text-white">Target Exam Deadline</div>
            <div className="text-[11px] text-dark-muted">Adjust days to auto-scale study workload</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {[3, 7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                days === d
                  ? 'bg-brand-indigo text-white shadow-md shadow-brand-indigo/30'
                  : 'bg-dark-surface text-dark-muted hover:text-white'
              }`}
            >
              {d} Days
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Daily Plan */}
        <Card hoverEffect={false} className="space-y-4">
          <div className="flex items-center justify-between border-b border-dark-border pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Today's Daily Plan</h3>
            <span className="text-xs text-brand-indigo font-bold">{planner?.daily_plan?.length || 3} Tasks</span>
          </div>

          <div className="space-y-3">
            {planner?.daily_plan?.map((t: any, i: number) => (
              <div key={i} className="p-3.5 rounded-xl bg-dark-surface/60 border border-dark-border space-y-1 text-xs">
                <div className="flex items-center justify-between text-dark-muted font-mono text-[10px]">
                  <span>{t.time}</span>
                  <span className="uppercase font-bold text-brand-indigo">{t.type}</span>
                </div>
                <div className="text-white font-semibold leading-snug">{t.task}</div>
              </div>
            ))}
          </div>
        </Card>

        {/* Weekly Plan */}
        <Card hoverEffect={false} className="md:col-span-2 space-y-4">
          <div className="border-b border-dark-border pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Weekly Revision Schedule</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {planner?.weekly_plan?.map((w: any, idx: number) => (
              <div key={idx} className="p-4 rounded-xl bg-dark-surface/60 border border-dark-border space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold">
                  <span className="text-brand-indigo">{w.day}</span>
                  <span className="text-white">{w.focus_topic}</span>
                </div>

                <ul className="space-y-1 text-dark-muted text-[11px] list-disc list-inside">
                  {w.goals?.map((g: string, i: number) => (
                    <li key={i}>{g}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
