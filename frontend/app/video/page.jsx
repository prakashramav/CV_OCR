'use client';

import { useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, FileVideo, RefreshCw, Download } from 'lucide-react';
import api from '../../services/api';

export default function VideoAnalysisPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [polling, setPolling] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setUploading(true);
      setProgress(10);
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.uploadVideo(formData, (progressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress(percent);
      });

      setJobId(res.data.job_id);
      startPolling(res.data.job_id);
    } catch (err) {
      console.error('Video upload failed:', err);
      alert('Failed to upload video. Ensure backend is running.');
    } finally {
      setUploading(false);
    }
  };

  const startPolling = (id) => {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const res = await api.getVideoStatus(id);
        setJobStatus(res.data);
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
          clearInterval(interval);
          setPolling(false);
        }
      } catch (e) {
        console.error('Polling error:', e);
        clearInterval(interval);
        setPolling(false);
      }
    }, 2000);
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-white">Batch Video Analysis & Ingestion</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload recorded traffic video footage for asynchronous AI vehicle tracking, plate extraction, and violation audits.
        </p>
      </div>

      {/* Upload Box */}
      <div className="bg-[#111827] rounded-2xl p-8 border border-slate-800">
        <div className="border-2 border-dashed border-slate-700 hover:border-emerald-500/50 rounded-xl p-8 text-center transition cursor-pointer">
          <input
            type="file"
            accept="video/mp4,video/avi,video/quicktime,video/x-matroska"
            onChange={handleFileChange}
            className="hidden"
            id="video-file-input"
          />
          <label htmlFor="video-file-input" className="cursor-pointer block">
            <UploadCloud className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white mb-1">
              {file ? file.name : 'Select or Drop Traffic Video'}
            </h3>
            <p className="text-xs text-slate-400">Supported codecs: MP4, AVI, MOV, MKV (H.264 / MPEG-4)</p>
          </label>
        </div>

        {file && (
          <div className="mt-5 flex items-center justify-between bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <div className="flex items-center gap-3">
              <FileVideo className="w-6 h-6 text-emerald-400" />
              <div>
                <p className="text-sm font-bold text-white">{file.name}</p>
                <p className="text-xs text-slate-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={uploading || polling}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-500/20 transition"
            >
              {uploading ? 'Uploading...' : polling ? 'Processing...' : 'Start AI Analysis'}
            </button>
          </div>
        )}
      </div>

      {/* Processing Progress Card */}
      {jobStatus && (
        <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono text-slate-400 uppercase">Job ID: {jobStatus.job_id}</span>
              <h3 className="text-base font-bold text-white mt-0.5">Status: {jobStatus.status}</h3>
            </div>
            {polling && <RefreshCw className="w-5 h-5 text-emerald-400 animate-spin" />}
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono text-slate-300">
              <span>Frames Processed: {jobStatus.processed_frames} / {jobStatus.total_frames || 'Calculating...'}</span>
              <span>{jobStatus.progress_percentage}%</span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-emerald-500 h-full transition-all duration-300"
                style={{ width: `${jobStatus.progress_percentage}%` }}
              ></div>
            </div>
          </div>

          {/* Results Summary */}
          {jobStatus.status === 'COMPLETED' && (
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div>
                  <span className="text-xs text-slate-400 block">Vehicles Tracked</span>
                  <span className="text-lg font-bold text-white">{jobStatus.total_vehicles}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Plates Recognized</span>
                  <span className="text-lg font-bold text-emerald-400">{jobStatus.total_plates}</span>
                </div>
              </div>

              {jobStatus.output_video_path && (
                <a
                  href={api.getImageUrl(jobStatus.output_video_path)}
                  download
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium border border-slate-700 transition"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Processed Video</span>
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
