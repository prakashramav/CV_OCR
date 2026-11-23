'use client';

import { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function Navbar() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeStr, setTimeStr] = useState('');

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const res = await api.getHealth();
      setHealth(res.data);
    } catch (e) {
      console.warn('Backend currently offline or starting:', e);
      setHealth({ status: 'OFFLINE', compute: { device: 'N/A' } });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const isHealthy = health?.status === 'HEALTHY';

  return (
    <header className="h-16 bg-[#0b0f17]/80 backdrop-blur-md border-b border-slate-800/80 px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <h2 className="text-base font-semibold text-slate-200">Traffic Surveillance & Number Plate Intelligence</h2>
      </div>

      <div className="flex items-center gap-5">
        {/* Hardware & Acceleration Pill */}
        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Device:</span>
          <span className="text-cyan-300 uppercase font-bold">{health?.compute?.device || 'CPU'}</span>
        </div>

        {/* Backend Status Pill */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border ${
            isHealthy
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
          <span>API: {health?.status || 'CONNECTING...'}</span>
        </div>

        {/* Live Clock */}
        <div className="text-xs font-mono text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
          {timeStr || '00:00:00'}
        </div>

        {/* Manual Refresh Button */}
        <button
          onClick={fetchHealth}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          title="Refresh Telemetry"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
        </button>
      </div>
    </header>
  );
}
