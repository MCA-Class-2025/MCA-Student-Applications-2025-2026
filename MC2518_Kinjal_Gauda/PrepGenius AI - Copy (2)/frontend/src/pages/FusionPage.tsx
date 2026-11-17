import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  Download, 
  Database, 
  BookOpen, 
  Video, 
  FileCode, 
  MapPin, 
  GraduationCap, 
  Sparkles,
  AlertCircle,
  FileCheck2
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { fusionApi } from '../services/fusionApi';
import { WideFusedStudentProfile } from '../types';

export const FusionPage: React.FC = () => {
  const [studentIdInput, setStudentIdInput] = useState<string>('ST000001');
  const [activeStudentId, setActiveStudentId] = useState<string>('ST000001');
  const [profile, setProfile] = useState<WideFusedStudentProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [exporting, setExporting] = useState<boolean>(false);
  const [exportingMaster, setExportingMaster] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fusionApi.getWideProfile(id);
      setProfile(data);
      setActiveStudentId(id);
    } catch (err: any) {
      setProfile(null);
      setError(err?.response?.data?.error?.message || err?.response?.data?.message || `Student with Student_ID '${id}' not found.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile('ST000001');
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (studentIdInput.trim()) {
      fetchProfile(studentIdInput.trim());
    }
  };

  const handleExport = async () => {
    if (!profile) return;
    setExporting(true);
    try {
      await fusionApi.exportExcel(profile.Student_ID);
    } catch (err: any) {
      alert(`Export failed: ${err.message || 'Error exporting Excel file'}`);
    } finally {
      setExporting(false);
    }
  };

  const handleExportMaster = async () => {
    setExportingMaster(true);
    try {
      await fusionApi.exportMasterExcel();
    } catch (err: any) {
      alert(`Master Export failed: ${err.message || 'Error exporting master Excel workbook'}`);
    } finally {
      setExportingMaster(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative overflow-hidden rounded-3xl p-8 glass-card border border-brand-indigo/30 bg-gradient-to-r from-brand-indigo/20 via-dark-card to-brand-violet/20"
      >
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-indigo/20 border border-brand-indigo/40 text-brand-indigo text-xs font-semibold">
              <Database className="w-3.5 h-3.5" />
              <span>Stage 5 • Dynamic Data Fusion Engine & Excel Export</span>
            </div>

            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Dynamic Wide Fused <span className="bg-gradient-to-r from-brand-indigo via-brand-violet to-brand-cyan bg-clip-text text-transparent">Student Profiles</span>
            </h1>

            <p className="text-dark-muted text-sm leading-relaxed">
              Dynamically combine student academic metrics, topic classifications, recommended books, YouTube courses, arXiv papers, and synthetic location metadata in real-time.
            </p>
          </div>

          {/* Prominent Export Buttons */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            {profile && (
              <Button
                variant="outline"
                size="md"
                icon={<Download className="w-4 h-4" />}
                disabled={exporting}
                onClick={handleExport}
              >
                {exporting ? 'Saving...' : 'Export Fused Data (.xlsx)'}
              </Button>
            )}

            <Button
              variant="glow"
              size="lg"
              icon={<Download className="w-5 h-5" />}
              disabled={exportingMaster}
              onClick={handleExportMaster}
              className="shadow-lg shadow-brand-indigo/25"
            >
              {exportingMaster ? 'Building Master Excel...' : 'Export Complete Dataset (.xlsx)'}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Student ID Search Bar & Demo Quick Links */}
      <Card hoverEffect glowColor="indigo">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <form onSubmit={handleSearch} className="flex-1 flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-dark-muted" />
              <input
                type="text"
                value={studentIdInput}
                onChange={(e) => setStudentIdInput(e.target.value)}
                placeholder="Enter Student_ID (e.g. ST000001, ST000002, ST000025)..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-dark-surface border border-dark-border text-white text-sm focus:outline-none focus:border-brand-indigo focus:ring-1 focus:ring-brand-indigo"
              />
            </div>
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? 'Searching...' : 'Search Profile'}
            </Button>
          </form>

          {/* Demo Quick Chips */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-dark-muted font-medium">Quick Demo IDs:</span>
            {['ST000001', 'ST000002', 'ST000025', 'ST000050'].map((id) => (
              <button
                key={id}
                onClick={() => {
                  setStudentIdInput(id);
                  fetchProfile(id);
                }}
                className={`px-2.5 py-1 text-xs font-semibold rounded-lg border transition-all ${
                  activeStudentId === id
                    ? 'bg-brand-indigo/30 text-white border-brand-indigo/60'
                    : 'bg-dark-surface text-dark-muted border-dark-border hover:text-white hover:border-brand-indigo/30'
                }`}
              >
                {id}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Error Message Display */}
      {error && (
        <Card glowColor="violet">
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <div>
              <h4 className="font-bold text-sm">Student Record Not Found</h4>
              <p className="text-xs text-dark-muted mt-0.5">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="p-12 text-center space-y-4">
          <div className="w-10 h-10 border-4 border-brand-indigo border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-dark-muted">Dynamically fusing student data, books, videos, papers & location...</p>
        </div>
      )}

      {/* Fused Profile Display Grid */}
      {!loading && profile && (
        <div className="space-y-6">
          {/* Section 1: Student Information & Learning Topic */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Student Core Card */}
            <div className="lg:col-span-2">
              <Card hoverEffect glowColor="indigo">
                <div className="flex items-center justify-between border-b border-dark-border/60 pb-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-brand-indigo/10 text-brand-indigo">
                      <GraduationCap className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-white">Student Core Profile</h3>
                      <p className="text-xs text-dark-muted">ID: {profile.Student_ID} • {profile.University_Year}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-xs font-bold rounded-full border ${
                    profile.Placement_Status === 'Placed'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}>
                    {profile.Placement_Status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Major</span>
                    <p className="text-sm font-semibold text-white">{profile.Major}</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Career Field</span>
                    <p className="text-sm font-semibold text-white">{profile.Career_Field}</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">CGPA</span>
                    <p className="text-sm font-semibold text-white">{profile.CGPA} / 4.0</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Study Hours</span>
                    <p className="text-sm font-semibold text-white">{profile.Study_Hours_Per_Week} hrs/week</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Programming Skill</span>
                    <p className="text-sm font-semibold text-white">{profile.Programming_Skill} / 10</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Projects Completed</span>
                    <p className="text-sm font-semibold text-white">{profile.Projects_Completed}</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Certifications</span>
                    <p className="text-sm font-semibold text-white">{profile.Certifications}</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Attendance</span>
                    <p className="text-sm font-semibold text-white">{profile.Attendance_Percentage}%</p>
                  </div>
                  <div>
                    <span className="text-[11px] text-dark-muted font-medium">Starting Salary</span>
                    <p className="text-sm font-semibold text-emerald-400">${profile.Starting_Salary_USD.toLocaleString()}</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Learning Topic Card */}
            <div>
              <Card hoverEffect glowColor="violet" className="h-full flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-3 border-b border-dark-border/60 pb-4 mb-4">
                    <div className="p-2 rounded-xl bg-brand-violet/10 text-brand-violet">
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-white">Identified Topic</h3>
                      <p className="text-xs text-dark-muted">{profile.topic_id}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <span className="text-[11px] text-dark-muted font-medium">Topic Name</span>
                      <p className="text-base font-extrabold text-brand-violet">{profile.topic_name}</p>
                    </div>
                    <div>
                      <span className="text-[11px] text-dark-muted font-medium">Subject Area</span>
                      <p className="text-sm font-medium text-white">{profile.subject_area}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-dark-border/60 text-[11px] text-dark-muted flex items-center justify-between">
                  <span>Derived Topic Mapping</span>
                  <span className="text-brand-violet font-semibold">Major + Career Match</span>
                </div>
              </Card>
            </div>
          </div>

          {/* Section 2: Resource Recommendations (Book, YouTube, arXiv) */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <FileCheck2 className="w-5 h-5 text-brand-indigo" />
              <span>Topic-First Recommended Learning Resources</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Book Card */}
              <Card hoverEffect glowColor="emerald" className="flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ★ {profile.recommended_book_rating || 'N/A'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-dark-muted font-bold">Recommended Book</span>
                    <h4 className="font-bold text-white text-base line-clamp-2 mt-0.5">
                      {profile.recommended_book_title || 'No relevant book found'}
                    </h4>
                  </div>

                  <div className="text-xs text-dark-muted space-y-1">
                    <p><span className="font-medium text-gray-300">Author:</span> {profile.recommended_book_author || 'N/A'}</p>
                    <p><span className="font-medium text-gray-300">Category:</span> {profile.recommended_book_category || 'N/A'}</p>
                    <p><span className="font-medium text-gray-300">ISBN-13:</span> {profile.recommended_book_isbn13 || 'N/A'}</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-dark-border/60 text-[11px] text-dark-muted">
                  Source: books.csv
                </div>
              </Card>

              {/* YouTube Card */}
              <Card hoverEffect glowColor="cyan" className="flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                      <Video className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {(profile.recommended_video_views || 0).toLocaleString()} views
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-dark-muted font-bold">YouTube Tutorial</span>
                    <h4 className="font-bold text-white text-base line-clamp-2 mt-0.5">
                      {profile.recommended_video_title || 'No relevant video found'}
                    </h4>
                  </div>

                  <div className="text-xs text-dark-muted space-y-1">
                    <p><span className="font-medium text-gray-300">Channel:</span> {profile.recommended_channel || 'N/A'}</p>
                    <p><span className="font-medium text-gray-300">Video ID:</span> {profile.recommended_video_id || 'N/A'}</p>
                    <p><span className="font-medium text-gray-300">Category ID:</span> {profile.recommended_video_category || 'N/A'}</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-dark-border/60 text-[11px] text-dark-muted">
                  Source: yt data.csv
                </div>
              </Card>

              {/* arXiv Card */}
              <Card hoverEffect glowColor="violet" className="flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2 rounded-xl bg-brand-violet/10 text-brand-violet">
                      <FileCode className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-brand-violet/10 text-brand-violet border border-brand-violet/20">
                      {profile.recommended_paper_category_code || 'N/A'}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-dark-muted font-bold">arXiv Paper</span>
                    <h4 className="font-bold text-white text-base line-clamp-2 mt-0.5">
                      {profile.recommended_paper_title || 'No relevant paper found'}
                    </h4>
                  </div>

                  <div className="text-xs text-dark-muted space-y-1">
                    <p><span className="font-medium text-gray-300">Paper ID:</span> {profile.recommended_paper_id || 'N/A'}</p>
                    <p><span className="font-medium text-gray-300">Category:</span> {profile.recommended_paper_category || 'N/A'}</p>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-dark-border/60 text-[11px] text-dark-muted">
                  Source: arXiv_scientific_dataset.csv
                </div>
              </Card>
            </div>
          </div>

          {/* Section 3: Location Metadata & Data Provenance */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Synthetic Location Card */}
            <Card hoverEffect glowColor="indigo">
              <div className="flex items-center gap-3 border-b border-dark-border/60 pb-3 mb-4">
                <div className="p-2 rounded-xl bg-brand-indigo/10 text-brand-indigo">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Demographic Location Assignment</h3>
                  <p className="text-xs text-amber-400 font-semibold">DERIVED / SYNTHETIC (DEMO MAPPING)</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-[11px] text-dark-muted font-medium">Assigned City</span>
                  <p className="text-base font-bold text-white capitalize">{profile.city}</p>
                </div>
                <div>
                  <span className="text-[11px] text-dark-muted font-medium">Latitude</span>
                  <p className="text-sm font-semibold text-white">{profile.latitude}</p>
                </div>
                <div>
                  <span className="text-[11px] text-dark-muted font-medium">Longitude</span>
                  <p className="text-sm font-semibold text-white">{profile.longitude}</p>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-dark-border/60 text-[11px] text-dark-muted">
                Source: cities.xlsx via deterministic hash mapping
              </div>
            </Card>

            {/* Data Provenance Card */}
            <Card hoverEffect glowColor="cyan">
              <div className="flex items-center gap-3 border-b border-dark-border/60 pb-3 mb-4">
                <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-white">Column-Level Data Provenance</h3>
                  <p className="text-xs text-dark-muted">Read-Only Dataset Source Attribution</p>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-dark-muted">Student Profile Core:</span>
                  <span className="text-gray-200 font-mono text-[11px]">{profile.provenance.student_core}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-dark-muted">Location Metadata:</span>
                  <span className="text-gray-200 font-mono text-[11px]">{profile.provenance.location}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-dark-muted">Books Recommendation:</span>
                  <span className="text-gray-200 font-mono text-[11px]">{profile.provenance.book}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-dark-muted">YouTube Video:</span>
                  <span className="text-gray-200 font-mono text-[11px]">{profile.provenance.youtube}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-dark-muted">arXiv Paper:</span>
                  <span className="text-gray-200 font-mono text-[11px]">{profile.provenance.arxiv}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
