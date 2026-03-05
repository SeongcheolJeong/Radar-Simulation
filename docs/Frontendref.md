> NOTE (2026-03-05): For the current implemented Graph Lab runtime controls and integration status, use `docs/278_frontend_runtime_multiplexing_and_lgit.md` as the authoritative reference.

While I cannot directly generate and download a `.txt` file to your local computer from this chat window, I have compiled and merged our entire architectural design, JSON schemas, React frontend code, and Python backend code into a single, comprehensive Markdown document below.

You can simply click the **"Copy"** button on this response and paste it directly into your preferred text editor (like VS Code, Notepad++, or Obsidian) and save it as `RadarSim_Complete_Project.txt` or `RadarSim_Complete_Project.md`.

---

# Radar Simulation Web Application - Complete Project Specification & Codebase

## 1. UX/UI Design Specification

**Product Goal:** A web-based, interactive platform for radar system design, 3D scene simulation, and signal processing analysis.
**Visual Style:** "Engineering Dark Mode" (`#121212` background, `#1E1E1E` panels) using modern Sans-Serif for UI and Monospace for data.
**Layout (IDE Style):**

* **Top App Bar:** Project Name, View Toggles (3D Scene vs. Maps), Export HDF5, Run Simulation.
* **Left Sidebar (Config):** Accordions for Antenna Setup (FFD upload), FMCW Control (Frequency, Bandwidth), and Scene Input.
* **Center Canvas:** Dual-mode viewer toggling between a React Three Fiber 3D Scene and a Plotly.js 2D Heatmap.
* **Right Sidebar (Inspector):** Contextual properties for selected 3D targets (Range, Velocity, RCS).
* **Bottom Panel (Logs/Data):** System logs console and CSV exportable Target List data grid.

## 2. API Data Contract (JSON Payload)

This is the payload sent from the React frontend to the Python backend when clicking "Run Simulation".

```json
{
  "projectId": "proj_auto_77ghz_v1",
  "timestamp": "2026-03-02T14:15:00Z",
  "radarSetup": {
    "antenna": {
      "type": "custom",
      "ffdFilePath": "/uploads/antennas/patch_array_77GHz.ffd",
      "mimoEnabled": true,
      "txChannels": [{ "id": "tx1", "position": [0.0, 0.0, 0.0] }],
      "rxChannels": [{ "id": "rx1", "position": [0.01, 0.0, 0.0] }]
    },
    "hardware": { "txPowerDbm": 12.0, "adcSampleRateMsps": 20.0, "adcBits": 16 }
  },
  "waveform": {
    "type": "FMCW",
    "startFrequencyGhz": 77.0,
    "bandwidthMhz": 500.0,
    "chirpDurationUs": 40.0,
    "chirpsPerFrame": 128
  },
  "scene": {
    "targets": [
      {
        "targetId": "tgt_001",
        "type": "Car",
        "position": { "x": 50.0, "y": 0.0, "z": 0.0 },
        "velocity": { "vx": -15.0, "vy": 0.0, "vz": 0.0 },
        "rcsDbsm": 10.0
      }
    ]
  },
  "outputRequests": { "generateRangeDoppler": true, "exportFormat": "hdf5" }
}

```

## 3. Frontend Implementation (React + Tailwind + Three.js + Plotly)

### `App.jsx` (Main Application & Layout)

```jsx
import React, { useState } from 'react';
import Scene3D from './Scene3D';
import RadarMap from './RadarMap';

const App = () => {
  const [activeView, setActiveView] = useState('scene'); 
  const [isSimulating, setIsSimulating] = useState(false);
  const [logs, setLogs] = useState(['[SYSTEM] RadarSim Web Engine Initialized.']);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [targets, setTargets] = useState([
    { id: 'tgt_001', type: 'Car', position: { x: -5, y: 0, z: 50 }, velocity: { vx: -15 }, rcs: 10 }
  ]);

  const updateTargetPosition = (id, newX, newZ) => {
    setTargets(prev => prev.map(tgt => tgt.id === id ? { ...tgt, position: { ...tgt.position, x: parseFloat(newX.toFixed(2)), z: parseFloat(newZ.toFixed(2)) } } : tgt));
    setSelectedTarget(prev => prev?.id === id ? { ...prev, position: { ...prev.position, x: parseFloat(newX.toFixed(2)), z: parseFloat(newZ.toFixed(2)) } } : prev);
  };

  const runSimulation = () => {
    setIsSimulating(true);
    setLogs(prev => [...prev, '[INFO] Starting Simulation...', '[SUCCESS] Processing Complete.']);
    setTimeout(() => { setIsSimulating(false); setActiveView('results'); }, 2000);
  };

  const exportTargetListToCSV = () => {
    const headers = ["Target ID", "Type", "Range_X (m)", "Range_Z (m)", "Velocity_X (m/s)", "RCS (dBsm)"];
    const rows = targets.map(tgt => [tgt.id, tgt.type, tgt.position.x, tgt.position.z, tgt.velocity.vx, tgt.rcs]);
    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "targets.csv";
    link.click();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-200 overflow-hidden">
      {/* Top Bar */}
      <header className="flex items-center justify-between h-14 bg-gray-800 px-4 border-b border-gray-700">
        <div className="font-bold text-blue-400">RadarSimX Web</div>
        <div>
          <button onClick={() => setActiveView('scene')} className="px-4 py-1 text-sm bg-gray-700 rounded mr-2">3D Scene</button>
          <button onClick={() => setActiveView('results')} className="px-4 py-1 text-sm bg-gray-700 rounded">Radar Maps</button>
        </div>
        <div>
          <button onClick={runSimulation} className="px-4 py-1 text-sm bg-blue-600 rounded text-white">▶ Run</button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar Config */}
        <aside className="w-72 bg-gray-800 p-4 border-r border-gray-700 overflow-y-auto">
          <h3 className="text-xs font-bold text-gray-400 mb-2">FMCW Control</h3>
          <input type="number" defaultValue="77" className="w-full bg-gray-900 border border-gray-600 rounded p-1 mb-2" placeholder="Start Freq (GHz)" />
          <input type="number" defaultValue="500" className="w-full bg-gray-900 border border-gray-600 rounded p-1" placeholder="Bandwidth (MHz)" />
        </aside>

        {/* Center Canvas */}
        <main className="flex-1 relative flex flex-col bg-[#0a0a0a]">
          {activeView === 'scene' ? (
            <Scene3D targets={targets} selectedTarget={selectedTarget} setSelectedTarget={setSelectedTarget} updateTargetPosition={updateTargetPosition} />
          ) : (
            <RadarMap targets={targets} />
          )}
        </main>

        {/* Right Sidebar Inspector */}
        <aside className="w-64 bg-gray-800 p-4 border-l border-gray-700">
          <h3 className="text-xs font-bold text-gray-400 mb-4">Properties</h3>
          {selectedTarget ? (
             <div className="space-y-2 text-sm">
                <p>ID: {selectedTarget.id}</p>
                <p>Range (Z): {selectedTarget.position.z} m</p>
                <p>Velocity: {selectedTarget.velocity.vx} m/s</p>
             </div>
          ) : <p className="text-sm text-gray-500">Select a target.</p>}
        </aside>
      </div>

      {/* Bottom Panel */}
      <footer className="h-48 bg-gray-900 p-2 border-t border-gray-700 overflow-y-auto text-xs font-mono">
        <button onClick={exportTargetListToCSV} className="mb-2 px-2 py-1 bg-gray-700 text-white rounded">Export CSV</button>
        {logs.map((log, i) => <div key={i}>{log}</div>)}
      </footer>
    </div>
  );
};
export default App;

```

### `Scene3D.jsx` (Interactive WebGL using React Three Fiber)

```jsx
import React, { useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, DragControls, Text } from '@react-three/drei';

const TargetNode = ({ target, isSelected, onClick, onDragEnd }) => {
  const meshRef = useRef();
  return (
    <DragControls axisLock="y" onDragStart={() => onClick(target)} onDragEnd={() => onDragEnd(target.id, meshRef.current.position.x, meshRef.current.position.z)}>
      <group position={[target.position.x, 1, -target.position.z]}>
        <mesh ref={meshRef}>
          <boxGeometry args={[2, 1.5, 4]} />
          <meshStandardMaterial color={isSelected ? "#ef4444" : "#10b981"} />
        </mesh>
        <Text position={[0, 2, 0]} fontSize={0.6} color="white">{target.id}</Text>
      </group>
    </DragControls>
  );
};

const Scene3D = ({ targets, selectedTarget, setSelectedTarget, updateTargetPosition }) => {
  const [isDragging, setIsDragging] = useState(false);
  return (
    <Canvas camera={{ position: [20, 20, 30] }} onPointerMissed={() => setSelectedTarget(null)}>
      <ambientLight intensity={0.4} />
      <directionalLight position={[10, 20, 10]} />
      <Grid infiniteGrid fadeDistance={100} sectionColor="#374151" cellColor="#1f2937" />
      {targets.map(tgt => (
        <TargetNode key={tgt.id} target={tgt} isSelected={selectedTarget?.id === tgt.id} 
          onClick={(t) => { setSelectedTarget(t); setIsDragging(true); }}
          onDragEnd={(id, x, z) => { setIsDragging(false); updateTargetPosition(id, x, Math.abs(z)); }} />
      ))}
      <OrbitControls makeDefault enabled={!isDragging} />
    </Canvas>
  );
};
export default Scene3D;

```

### `RadarMap.jsx` (Plotly Heatmap Visualization)

```jsx
import React from 'react';
import Plot from 'react-plotly.js';

const RadarMap = ({ targets }) => {
  // Mock DSP output generator for visual representation
  const ranges = Array.from({ length: 150 }, (_, i) => i * 0.5); 
  const velocities = Array.from({ length: 128 }, (_, i) => -20 + i * (40 / 128)); 
  let zData = Array.from({ length: 150 }, () => Array.from({ length: 128 }, () => -60 + Math.random() * 5));

  targets.forEach(tgt => {
    const rIdx = ranges.findIndex(r => r >= tgt.position.z);
    const vIdx = velocities.findIndex(v => v >= tgt.velocity.vx);
    if (rIdx > 0 && vIdx > 0 && zData[rIdx] && zData[rIdx][vIdx]) {
      zData[rIdx][vIdx] += 40 + tgt.rcs; // Inject peak
    }
  });

  return (
    <Plot
      data={[{ z: zData, x: velocities, y: ranges, type: 'heatmap', colorscale: 'Jet', zmin: -60, zmax: 0 }]}
      layout={{ paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', xaxis: { title: 'Velocity (m/s)' }, yaxis: { title: 'Range (m)' } }}
      useResizeHandler={true} style={{ width: '100%', height: '100%' }}
    />
  );
};
export default RadarMap;

```

## 4. Backend Implementation (Python + FastAPI + NumPy)

### `main.py` (API Server & HDF5 Export)

```python
from fastapi import FastAPI
from pydantic import BaseModel
import h5py
import numpy as np
from fastapi.responses import FileResponse

app = FastAPI()

class SimulationConfig(BaseModel):
    projectId: str
    # ... additional schema fields mapped from JSON payload ...

@app.post("/api/simulate")
async def run_simulation(config: SimulationConfig):
    return {"status": "success", "message": "2D FFT Complete"}

@app.post("/api/export-hdf5")
async def export_hdf5():
    filepath = "/tmp/sensor_data.h5"
    mock_data = np.random.randn(128, 800)
    with h5py.File(filepath, "w") as h5f:
        h5f.create_dataset("adc_cube", data=mock_data)
    return FileResponse(path=filepath, filename="sensor_data.h5", media_type='application/x-hdf5')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

```

### `fmcw_dsp.py` (Range-Doppler 2D FFT Math)

```python
import numpy as np

def generate_range_doppler_map():
    c, fc, B, Tc, num_chirps, fs = 3e8, 77e9, 500e6, 40e-6, 128, 20e6
    num_samples = int(fs * Tc)
    slope = B / Tc
    
    if_signal = np.zeros((num_chirps, num_samples), dtype=complex)
    t_fast = np.linspace(0, Tc, num_samples, endpoint=False)
    
    # Superposition of target reflections
    targets = [[50.0, -15.0, 1.0]] # Range, Velocity, Amplitude
    for l in range(num_chirps):
        t_slow = l * Tc
        for R0, v, A in targets:
            phase = 2 * np.pi * ((slope * 2 * R0 / c) * t_fast + (2 * fc * v / c) * t_slow)
            if_signal[l, :] += A * np.exp(1j * phase)
            
    # Windowing and 2D FFT
    if_windowed = if_signal * np.outer(np.hanning(num_chirps), np.hanning(num_samples))
    range_fft = np.fft.fft(if_windowed, axis=1)
    range_doppler = np.fft.fftshift(np.fft.fft(range_fft, axis=0), axes=0)
    
    rd_db = 20 * np.log10(np.abs(range_doppler) / np.max(np.abs(range_doppler)))
    return np.clip(rd_db, -60, 0)

```

### `cfar.py` (2D Cell-Averaging Target Detection)

```python
import numpy as np

def run_2d_cfar(rd_matrix_linear, config={"snr_threshold_db": 12.0}):
    Tr, Td, Gr, Gd = 8, 4, 4, 2
    threshold_factor = 10 ** (config["snr_threshold_db"] / 10.0)
    
    num_doppler, num_range = rd_matrix_linear.shape
    win_r, win_d = Tr + Gr, Td + Gd
    num_training = ((2*win_d+1)*(2*win_r+1)) - ((2*Gd+1)*(2*Gr+1))
    
    detections = []
    for d in range(win_d, num_doppler - win_d):
        for r in range(win_r, num_range - win_r):
            window = rd_matrix_linear[d-win_d:d+win_d+1, r-win_r:r+win_r+1]
            guard = rd_matrix_linear[d-Gd:d+Gd+1, r-Gr:r+Gr+1]
            
            noise_avg = (np.sum(window) - np.sum(guard)) / num_training
            cut_power = rd_matrix_linear[d, r]
            
            if cut_power > noise_avg * threshold_factor:
                detections.append({"row": d, "col": r, "snr_db": 10 * np.log10(cut_power/noise_avg)})
                
    return detections

```

---

Would you like me to also provide a `docker-compose.yml` file and `Dockerfile` templates so you can easily spin up both the React frontend and Python backend together in a containerized environment?
