export default function StatCard({ title, value, unit, icon: Icon, color = 'emerald', changeText }) {
  const colorMap = {
    emerald: {
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      iconBg: 'bg-emerald-500/10 text-emerald-400',
      glow: 'shadow-emerald-500/5',
    },
    cyan: {
      border: 'border-cyan-500/20 hover:border-cyan-500/40',
      iconBg: 'bg-cyan-500/10 text-cyan-400',
      glow: 'shadow-cyan-500/5',
    },
    amber: {
      border: 'border-amber-500/20 hover:border-amber-500/40',
      iconBg: 'bg-amber-500/10 text-amber-400',
      glow: 'shadow-amber-500/5',
    },
    rose: {
      border: 'border-rose-500/20 hover:border-rose-500/40',
      iconBg: 'bg-rose-500/10 text-rose-400',
      glow: 'shadow-rose-500/5',
    },
  };

  const scheme = colorMap[color] || colorMap.emerald;

  return (
    <div className={`bg-[#111827] rounded-2xl p-5 border ${scheme.border} shadow-lg ${scheme.glow} transition-all`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        <div className={`p-2 rounded-xl ${scheme.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-3xl font-extrabold text-white tracking-tight">{value}</span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>
      {changeText && (
        <p className="mt-2 text-xs text-slate-400 flex items-center gap-1">
          <span className="text-emerald-400 font-medium">●</span> {changeText}
        </p>
      )}
    </div>
  );
}
