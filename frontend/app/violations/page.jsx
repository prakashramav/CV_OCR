'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Eye, Clock, ShieldCheck, X } from 'lucide-react';
import api from '../../services/api';

export default function ViolationsPage() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeModalImg, setActiveModalImg] = useState(null);

  const fetchViolations = async () => {
    try {
      setLoading(true);
      const res = await api.getViolations();
      setViolations(res.data.items);
    } catch (e) {
      console.error('Failed to load violations:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchViolations();
  }, []);

  const handleUpdateStatus = async (id, newStatus) => {
    try {
      await api.updateViolationStatus(id, newStatus);
      setViolations((prev) =>
        prev.map((v) => (v.id === id ? { ...v, verification_status: newStatus } : v))
      );
    } catch (e) {
      console.error('Failed to update status:', e);
      alert('Could not update status.');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-white">Traffic Violation Management</h1>
        <p className="text-sm text-slate-400 mt-1">
          Review, verify, and cite automated stop-line crossing and restricted-zone entry incidents
        </p>
      </div>

      {/* Grid of Violations */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {violations.map((vio) => (
          <div
            key={vio.id}
            className="bg-[#111827] rounded-2xl border border-slate-800 overflow-hidden shadow-xl flex flex-col justify-between"
          >
            <div>
              {/* Evidence Frame Preview with Click to Enlarge */}
              <div
                onClick={() => setActiveModalImg(api.getImageUrl(vio.evidence_image_path))}
                className="relative aspect-video bg-black cursor-pointer group overflow-hidden border-b border-slate-800"
              >
                <img
                  src={api.getImageUrl(vio.evidence_image_path)}
                  alt="Evidence Frame"
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                />
                <div className="absolute top-3 left-3 bg-rose-500/90 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded">
                  {vio.violation_type}
                </div>
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 text-white text-xs font-medium">
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Full Evidence</span>
                  </div>
                </div>
              </div>

              {/* Incident Details */}
              <div className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-black text-white px-2.5 py-1 bg-slate-900 border border-slate-700 rounded-lg">
                    {vio.plate_number}
                  </span>
                  <span
                    className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${
                      vio.verification_status === 'CONFIRMED'
                        ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                        : vio.verification_status === 'DISMISSED'
                        ? 'bg-slate-800 border-slate-700 text-slate-400'
                        : 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                    }`}
                  >
                    {vio.verification_status}
                  </span>
                </div>

                <div className="space-y-1 text-xs text-slate-400">
                  <p className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>{new Date(vio.event_timestamp).toLocaleString()}</span>
                  </p>
                  <p className="text-[11px] font-mono text-slate-500">Track ID: #{vio.tracking_id}</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 bg-slate-900/60 border-t border-slate-800 flex items-center gap-2">
              <button
                onClick={() => handleUpdateStatus(vio.id, 'CONFIRMED')}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 text-xs font-bold border border-emerald-500/30 transition"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Confirm</span>
              </button>
              <button
                onClick={() => handleUpdateStatus(vio.id, 'DISMISSED')}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Dismiss</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {violations.length === 0 && !loading && (
        <div className="p-16 text-center text-slate-500 text-xs">No traffic violations recorded.</div>
      )}

      {/* Enlarged Evidence Modal */}
      {activeModalImg && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#111827] rounded-2xl border border-slate-700 p-6 max-w-4xl w-full relative">
            <button
              onClick={() => setActiveModalImg(null)}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-base font-bold text-white mb-3">Evidentiary Frame Snapshot</h3>
            <div className="rounded-xl overflow-hidden bg-black border border-slate-800">
              <img src={activeModalImg} alt="Evidence Enlarged" className="w-full max-h-[75vh] object-contain" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
