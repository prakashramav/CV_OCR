'use client';

import { useState } from 'react';
import { Sliders, Save, CheckCircle2, Shield, Camera, HardDrive } from 'lucide-react';

export default function SettingsPage() {
  const [vehicleConf, setVehicleConf] = useState(0.45);
  const [plateConf, setPlateConf] = useState(0.35);
  const [ocrConf, setOcrConf] = useState(0.40);
  const [stopLineY, setStopLineY] = useState(0.65);
  const [retentionDays, setRetentionDays] = useState('30');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black tracking-tight text-white">System Settings & Calibration</h1>
        <p className="text-sm text-slate-400 mt-1">
          Adjust model confidence thresholds, virtual violation boundaries, and data retention rules
        </p>
      </div>

      <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800 space-y-6">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Sliders className="w-4 h-4 text-emerald-400" />
          Model Inference Thresholds
        </h2>

        {/* Vehicle Detection Threshold */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Vehicle Detection Confidence</span>
            <span className="font-mono text-emerald-400 font-bold">{Math.round(vehicleConf * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={vehicleConf}
            onChange={(e) => setVehicleConf(parseFloat(e.target.value))}
            className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
          />
          <p className="text-[11px] text-slate-500">Lower values increase recall for distant vehicles; higher values eliminate spurious false positives.</p>
        </div>

        {/* Plate Detection Threshold */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">License Plate Detector Confidence</span>
            <span className="font-mono text-emerald-400 font-bold">{Math.round(plateConf * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={plateConf}
            onChange={(e) => setPlateConf(parseFloat(e.target.value))}
            className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
          />
        </div>

        {/* OCR Confidence Threshold */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">OCR Character Confidence Floor</span>
            <span className="font-mono text-emerald-400 font-bold">{Math.round(ocrConf * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={ocrConf}
            onChange={(e) => setOcrConf(parseFloat(e.target.value))}
            className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
          />
        </div>
      </div>

      {/* Traffic Violation Calibration */}
      <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800 space-y-6">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Shield className="w-4 h-4 text-rose-400" />
          Virtual Stop-Line Geometry
        </h2>

        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Stop Line Y-Ratio (Frame Height Percentage)</span>
            <span className="font-mono text-rose-400 font-bold">{Math.round(stopLineY * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.3"
            max="0.9"
            step="0.05"
            value={stopLineY}
            onChange={(e) => setStopLineY(parseFloat(e.target.value))}
            className="w-full accent-rose-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
          />
          <p className="text-[11px] text-slate-500">
            Defines the virtual line across the camera viewport. Any tracked vehicle crossing below this vertical boundary triggers a violation snapshot.
          </p>
        </div>
      </div>

      {/* Privacy & Retention */}
      <div className="bg-[#111827] rounded-2xl p-6 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-cyan-400" />
          Data Governance & Retention
        </h2>

        <div className="flex items-center justify-between text-xs">
          <div>
            <p className="font-medium text-slate-300">Automatic Evidence & Crop Pruning</p>
            <p className="text-[11px] text-slate-500">Purges raw video files and unreferenced plate crops to comply with data protection principles.</p>
          </div>
          <select
            value={retentionDays}
            onChange={(e) => setRetentionDays(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white"
          >
            <option value="7">7 Days</option>
            <option value="30">30 Days</option>
            <option value="90">90 Days</option>
            <option value="0">Indefinite (No purge)</option>
          </select>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-end gap-4">
        {saved && (
          <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium animate-fade-in">
            <CheckCircle2 className="w-4 h-4" />
            Configuration saved to environment!
          </span>
        )}
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-500/20 transition"
        >
          <Save className="w-4 h-4" />
          <span>Save Settings</span>
        </button>
      </div>
    </div>
  );
}
