'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Car,
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Clock,
  ShieldAlert,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import StatCard from '../components/StatCard';
import api from '../services/api';

const PIE_COLORS = ['#38bdf8', '#34d399', '#f43f5e', '#fbbf24'];

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const res = await api.getOverview();
        setData(res.data);
      } catch (err) {
        console.error('Failed to load overview data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const metrics = data?.metrics || {
    total_vehicles: 0,
    total_plates: 0,
    successful_ocr_percentage: 0,
    total_violations: 0,
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Title & Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">System Operations Overview</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time telemetrics, detection volumes, and safety alerts</p>
        </div>
        <Link
          href="/live"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-black font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-500/20 transition-all"
        >
          <span>Launch Live Monitor</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          title="Total Vehicles Detected"
          value={metrics.total_vehicles}
          icon={Car}
          color="cyan"
          changeText="Tracked across active sessions"
        />
        <StatCard
          title="Number Plates Recognized"
          value={metrics.total_plates}
          icon={CreditCard}
          color="emerald"
          changeText="Localized via dedicated YOLO"
        />
        <StatCard
          title="Successful OCR Rate"
          value={`${metrics.successful_ocr_percentage}%`}
          icon={CheckCircle2}
          color="amber"
          changeText="Format validated (CMVR standards)"
        />
        <StatCard
          title="Violation Events"
          value={metrics.total_violations}
          icon={AlertTriangle}
          color="rose"
          changeText="Evidence snapshots captured"
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hourly Trend Chart */}
        <div className="lg:col-span-2 bg-[#111827] rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Detection Activity Timeline</h2>
              <p className="text-xs text-slate-400">Hourly vehicle detection and violation incidence</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block"></span> Detections
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block"></span> Violations
              </span>
            </div>
          </div>

          <div className="h-64">
            {data?.hourly_trends?.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.hourly_trends}>
                  <defs>
                    <linearGradient id="colorDet" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorVio" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="hour" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  />
                  <Area type="monotone" dataKey="detections" stroke="#38bdf8" strokeWidth={2} fill="url(#colorDet)" />
                  <Area type="monotone" dataKey="violations" stroke="#f43f5e" strokeWidth={2} fill="url(#colorVio)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No timeline activity logged yet
              </div>
            )}
          </div>
        </div>

        {/* Vehicle Classification Breakdown */}
        <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Vehicle Classification</h2>
            <p className="text-xs text-slate-400 mb-4">COCO traffic target distributions</p>

            <div className="h-44">
              {data?.vehicle_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.vehicle_distribution}
                      dataKey="count"
                      nameKey="vehicle_type"
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={70}
                      paddingAngle={4}
                    >
                      {data.vehicle_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-500">
                  No vehicle distribution recorded
                </div>
              )}
            </div>
          </div>

          <div className="space-y-2 mt-4 pt-4 border-t border-slate-800">
            {data?.vehicle_distribution?.map((v, i) => (
              <div key={v.vehicle_type} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 capitalize text-slate-300">
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block"
                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                  ></span>
                  {v.vehicle_type}
                </span>
                <span className="font-mono font-bold text-white">{v.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Violation Incident Feed */}
      <div className="bg-[#111827] rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Recent Violation Events</h2>
              <p className="text-xs text-slate-400">Indisputable photographic evidence triggers</p>
            </div>
          </div>
          <Link href="/violations" className="text-xs text-emerald-400 hover:text-emerald-300 font-medium">
            View All Violations →
          </Link>
        </div>

        <div className="divide-y divide-slate-800/80">
          {data?.recent_violations?.length > 0 ? (
            data.recent_violations.map((vio) => (
              <div key={vio.id} className="p-4 px-6 flex items-center justify-between hover:bg-slate-800/30 transition">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-10 rounded-lg overflow-hidden bg-slate-900 border border-slate-800 shrink-0">
                    <img
                      src={api.getImageUrl(vio.evidence_image_path)}
                      alt="Violation Evidence"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-white">{vio.plate_number}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                        {vio.violation_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <Clock className="w-3 h-3" />
                      {vio.timestamp}
                    </p>
                  </div>
                </div>

                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                    vio.verification_status === 'CONFIRMED'
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {vio.verification_status}
                </span>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">No violations recorded. System operational.</div>
          )}
        </div>
      </div>
    </div>
  );
}
