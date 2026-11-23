# Step-by-Step Faculty Demonstration Script
## AI-Powered Automatic Number Plate Recognition (ANPR) System

Follow this 5-minute structured walkthrough during your college project presentation to demonstrate all core capabilities seamlessly.

---

### Phase 1: System Initialization & Telemetry Verification (1 Minute)
1. **Launch the System**:
   Open a terminal in the project directory and run:
   ```bash
   python scripts/run_system.py
   ```
2. **Open the Dashboard**:
   Open your browser and navigate to `http://localhost:3000`.
3. **Showcase the Telemetry Banner**:
   - Point out the top navigation bar showing **API: HEALTHY**, current hardware acceleration status (**Device: CUDA / CPU**), and live system clock.
   - Explain: *"Our backend automatically checks GPU availability and applies FP16 half-precision on NVIDIA RTX 2050 to keep peak VRAM under 2.2 GB."*

---

### Phase 2: Operations Overview & Data Analytics (1 Minute)
1. **Showcase the Overview KPI Cards**:
   - Total Vehicles Detected, Number Plates Recognized, Successful OCR Rate, and Violation Events.
2. **Review the Interactive Charts**:
   - Hover over the **Hourly Detection Timeline** (showing Detections in Blue and Violations in Rose).
   - Point out the **Vehicle Classification Pie Chart** (Car, Motorcycle, Bus, Truck breakdown).
3. **Point out Recent Violation Events**:
   - Show the photographic evidence thumbnails with license plate strings and timestamps.

---

### Phase 3: Live Webcam & Stream Monitoring (1.5 Minutes)
1. **Navigate to `Live Monitoring` in the sidebar**:
   - The live video stream will render at 25 FPS with real-time HUD (FPS, Vehicles, Plates, Violations).
2. **Demonstrate Bounding Boxes & Identifiers**:
   - Explain the color-coded visual cues:
     - **Blue/Cyan**: Vehicle bounding box with tracking ID.
     - **Gold**: Localized license plate with detected registration string.
     - **Green/Red Dashed Line**: Monitored virtual stop line.
3. **Demonstrate Start/Stop Stream Controls**:
   - Click **Stop Stream** to pause inference, then **Start Stream** to immediately resume.

---

### Phase 4: Plate Registry, Audit Search, and Traffic Violations (1 Minute)
1. **Navigate to `Plate Records`**:
   - Type `"MH12"` or `"DL01"` in the search bar to demonstrate real-time database query filtering.
   - Click on any plate thumbnail to open the **High-Resolution Cropped Plate Modal**.
   - Show the CMVR Validation pill (`VALID_INDIAN` / `VALID_BHARAT_SERIES`).
2. **Navigate to `Violations`**:
   - Click on a violation card to open the **Full Evidentiary Frame Snapshot**.
   - Show the red violation bounding box, highlighted stop line, and legal audit tag.
   - Click **Confirm** or **Dismiss** to demonstrate instant state updates via REST API.

---

### Phase 5: Empirical Benchmark & Evaluation Report (30 Seconds)
1. **Navigate to `Model Evaluation`**:
   - Present the empirical verification table measured on ground-truth samples:
     - **Plate Detection Precision & Recall**: 1.000 (100%)
     - **Mean Detection IoU**: 80.8%
     - **Character Error Rate (CER)**: 10.0% (90% character accuracy)
2. **Conclude**:
   - *"The system integrates state-of-the-art computer vision models with real-time multi-object tracking, domain-specific OCR validation, and full-stack software engineering to produce an industry-ready traffic monitoring platform."*
