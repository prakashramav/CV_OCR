'use client';

import { useState } from 'react';
import { Video, Play, Square, Eye, ShieldAlert, Cpu } from 'lucide-react';
import api from '../../services/api';

export default function LiveMonitoringPage() {
  const [streaming, setStreaming] = useState(true);
  const streamUrl = api.getLiveStreamUrl();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">Live Traffic & ANPR Monitoring</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time video feed with automated vehicle tracking, license plate localization, and OCR
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setStreaming(!streaming)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider transition ${
              streaming
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30'
                : 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/20'
            }`}
          >
            {streaming ? (
              <>
                <Square className="w-4 h-4 fill-current" />
                <span>Stop Stream</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Start Stream</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Video Stream Player Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 bg-[#111827] rounded-2xl border border-slate-800 overflow-hidden shadow-2xl relative">
          <div className="bg-slate-900/90 border-b border-slate-800 px-5 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping inline-block"></span>
              <span className="text-xs font-mono font-bold text-white tracking-wider">CAM-01: TRAFFIC INTERSECTION FEED</span>
            </div>
            <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded">
              MJPEG STREAM 640x480 @ 25 FPS
            </span>
          </div>

          <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
            {streaming ? (
              <img
                src={streamUrl}
                alt="Live ANPR Stream"
                className="w-full h-full object-contain"
                onError={(e) => {
                  console.warn('Live stream feed error:', e);
                }}
              />
            ) : (
              <div className="text-center p-8">
                <Video className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-sm font-medium text-slate-400">Stream paused by administrator</p>
                <p className="text-xs text-slate-600 mt-1">Click Start Stream to resume real-time AI inference</p>
              </div>
            )}
          </div>
        </div>

        {/* Live Controls & Guide */}
        <div className="space-y-5">
          <div className="bg-[#111827] rounded-2xl p-5 border border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Eye className="w-4 h-4 text-emerald-400" />
              Stream Intelligence
            </h3>
            <div className="space-y-3 text-xs text-slate-400">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-white font-medium block mb-1">Adaptive Camera Source</span>
                <span>
                  Automatically binds to connected hardware webcam. When running headlessly, streams high-fidelity synthetic test traffic.
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-white font-medium block mb-1">Bounding Box Styling</span>
                <span className="flex items-center gap-2 mt-1">
                  <span className="w-2 h-2 rounded-full bg-sky-400 inline-block"></span> Blue/Cyan: Car / Vehicle
                </span>
                <span className="flex items-center gap-2 mt-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block"></span> Gold: License Plate Crop
                </span>
                <span className="flex items-center gap-2 mt-1">
                  <span className="w-2 h-2 rounded-full bg-rose-500 inline-block"></span> Crimson: Traffic Violation
                </span>
              </div>
            </div>
          </div>

          <div className="bg-[#111827] rounded-2xl p-5 border border-slate-800">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Violation Monitor
            </h3>
            <p className="text-xs text-slate-400">
              The horizontal dashed line represents the calibrated virtual stop-line. Any vehicle vector crossing into the restricted zone triggers an instant evidentiary capture.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
