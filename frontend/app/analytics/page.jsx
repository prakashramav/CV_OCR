'use client';

import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';
import api from '../../services/api';

const COLORS = ['#38bdf8', '#34d399', '#f43f5e', '#fbbf24'];

export default function AnalyticsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getOverview();
        setData(res.data);
      } catch (e) {
        console.error('Failed to load analytics:', e);
      }
    }
    load();
  }, []);

  const confData = data?.confidence_distribution
    ? Object.entries(data.confidence_distribution).map(([range, count]) => ({ range, count }))
    : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-white">Statistical Analytics & CV Metrics</h1>
        <p className="text-sm text-slate-400 mt-1">
          Deep-dive quantitative distributions of detection confidence, vehicle categories, and temporal traffic density
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OCR Confidence Distribution */}
        <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-1">OCR Confidence Distribution</h2>
          <p className="text-xs text-slate-400 mb-6">Character extraction certainty tiers</p>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="range" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="count" fill="#34d399" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Vehicle Classification Volume */}
        <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Vehicle Classification Density</h2>
          <p className="text-xs text-slate-400 mb-6">Volume per vehicle type category</p>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.vehicle_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="vehicle_type" stroke="#64748b" fontSize={11} className="capitalize" />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="count" fill="#38bdf8" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
