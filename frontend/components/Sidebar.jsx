'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Video,
  FileVideo,
  CreditCard,
  AlertTriangle,
  BarChart3,
  Sliders,
  Award,
  ShieldCheck,
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/live', label: 'Live Monitoring', icon: Video, badge: 'Live' },
  { href: '/video', label: 'Video Analysis', icon: FileVideo },
  { href: '/records', label: 'Plate Records', icon: CreditCard },
  { href: '/violations', label: 'Violations', icon: AlertTriangle },
  { href: '/analytics', label: 'Deep Analytics', icon: BarChart3 },
  { href: '/evaluation', label: 'Model Evaluation', icon: Award },
  { href: '/settings', label: 'Settings', icon: Sliders },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0f1523] border-r border-slate-800/80 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 gap-3 border-b border-slate-800/80">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center text-black font-bold shadow-lg shadow-emerald-500/20">
            <ShieldCheck className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white">ANPR SENTINEL</h1>
            <p className="text-[10px] text-emerald-400 font-mono font-medium tracking-wider">AI TRAFFIC VISION</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/15 to-transparent text-emerald-400 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* System Footer Info */}
      <div className="p-4 border-t border-slate-800/80">
        <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-800">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-400 font-medium">Model Inference</span>
            <span className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block"></span>
              Active
            </span>
          </div>
          <p className="text-[11px] text-slate-300 font-mono truncate">YOLOv8 + EasyOCR CRNN</p>
          <div className="mt-2 text-[10px] text-slate-400 flex justify-between">
            <span>B.Tech Project</span>
            <span className="text-slate-400">v1.0.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
