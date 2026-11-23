'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, CreditCard, CheckCircle2, AlertCircle, Eye, X } from 'lucide-react';
import api from '../../services/api';

export default function PlateRecordsPage() {
  const [plates, setPlates] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeModalImg, setActiveModalImg] = useState(null);

  const fetchPlates = async () => {
    try {
      setLoading(true);
      const params = {};
      if (search.trim()) params.query = search.trim();
      if (statusFilter) params.validation_status = statusFilter;

      const res = await api.getPlates(params);
      setPlates(res.data.items);
      setTotal(res.data.total);
    } catch (e) {
      console.error('Failed to load plates:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlates();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchPlates();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">License Plate Registry & Audit</h1>
          <p className="text-sm text-slate-400 mt-1">
            Searchable historical records of all localized plates, OCR confidences, and format verifications
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search registration (e.g. MH12)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-[#111827] border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50 w-64"
            />
          </form>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#111827] border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50"
          >
            <option value="">All Validation Statuses</option>
            <option value="VALID_INDIAN">Valid Indian Standard</option>
            <option value="VALID_BHARAT_SERIES">Valid Bharat (BH)</option>
            <option value="SUSPICIOUS_PARTIAL">Suspicious / Partial</option>
            <option value="INVALID">Invalid Format</option>
          </select>
        </div>
      </div>

      {/* Plate Records Table */}
      <div className="bg-[#111827] rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Plate Crop</th>
                <th className="py-3.5 px-6">Registration String</th>
                <th className="py-3.5 px-6">Raw OCR String</th>
                <th className="py-3.5 px-6">Vehicle Type</th>
                <th className="py-3.5 px-6">OCR Confidence</th>
                <th className="py-3.5 px-6">CMVR Validation</th>
                <th className="py-3.5 px-6">Detected At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {plates.length > 0 ? (
                plates.map((plate) => {
                  const isValid =
                    plate.validation_status === 'VALID_INDIAN' ||
                    plate.validation_status === 'VALID_BHARAT_SERIES';

                  return (
                    <tr key={plate.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-6">
                        {plate.plate_image_path ? (
                          <div
                            onClick={() => setActiveModalImg(api.getImageUrl(plate.plate_image_path))}
                            className="w-24 h-9 rounded bg-slate-900 border border-slate-700/80 overflow-hidden cursor-pointer hover:border-emerald-500 transition relative group"
                          >
                            <img
                              src={api.getImageUrl(plate.plate_image_path)}
                              alt="Plate Crop"
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                              <Eye className="w-4 h-4 text-white" />
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-600 font-mono text-[10px]">NO_CROP</span>
                        )}
                      </td>
                      <td className="py-3 px-6">
                        <span className="font-mono font-bold text-sm text-white tracking-wider bg-slate-900/90 border border-slate-700/60 px-2 py-0.5 rounded">
                          {plate.normalized_text || 'UNREADABLE'}
                        </span>
                      </td>
                      <td className="py-3 px-6 font-mono text-slate-400">{plate.raw_text}</td>
                      <td className="py-3 px-6 capitalize text-slate-300 font-medium">
                        {plate.vehicle_type}
                        {plate.tracking_id && <span className="text-slate-500 text-[10px] ml-1">#{plate.tracking_id}</span>}
                      </td>
                      <td className="py-3 px-6">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                plate.ocr_confidence > 0.8
                                  ? 'bg-emerald-400'
                                  : plate.ocr_confidence > 0.6
                                  ? 'bg-amber-400'
                                  : 'bg-rose-400'
                              }`}
                              style={{ width: `${Math.round(plate.ocr_confidence * 100)}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-slate-300 font-medium">
                            {(plate.ocr_confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-6">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-medium text-[11px] border ${
                            isValid
                              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                              : 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                          }`}
                        >
                          {isValid ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                          {plate.validation_status}
                        </span>
                      </td>
                      <td className="py-3 px-6 text-slate-400 font-mono text-[11px]">
                        {new Date(plate.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 text-xs">
                    {loading ? 'Loading number plate audit records...' : 'No license plate detections match query.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Image Preview Modal */}
      {activeModalImg && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111827] rounded-2xl border border-slate-700 p-5 max-w-lg w-full relative">
            <button
              onClick={() => setActiveModalImg(null)}
              className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-sm font-bold text-white mb-3">Cropped License Plate Region</h3>
            <div className="rounded-xl overflow-hidden bg-black border border-slate-800 flex items-center justify-center p-2">
              <img src={activeModalImg} alt="Plate Enlarged" className="max-h-72 object-contain" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
