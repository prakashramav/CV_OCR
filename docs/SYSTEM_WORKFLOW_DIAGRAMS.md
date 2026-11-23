# System Workflow & Architecture Diagrams
## AI-Powered Automatic Number Plate Recognition (ANPR) System

---

## 1. Multi-Tier System Architecture

```mermaid
flowchart TD
    subgraph UI ["Presentation Layer (Next.js 14 + Tailwind CSS)"]
        Dashboard["Executive Dashboard"]
        LiveView["Live Webcam Stream View"]
        VideoSuite["Video Analysis Suite"]
        Records["Searchable Plate Records"]
        Violations["Violation Evidence Viewer"]
        Eval["Model Evaluation View"]
    end

    subgraph API ["Application & Routing Layer (FastAPI)"]
        Router["API Gateway (/api/v1)"]
        StreamEndpoint["MJPEG Frame Streaming Generator"]
        JobManager["Background Worker & Job Queue"]
        DBLayer["SQLAlchemy ORM (SQLite / PostgreSQL)"]
    end

    subgraph Vision ["Computer Vision & AI Inference Pipeline"]
        VehicleModel["Vehicle Detector (YOLOv8n)"]
        MOT["Multi-Object Tracker (ByteTrack / Kalman)"]
        PlateModel["Dedicated License Plate Detector (YOLOv8n-Plate)"]
        CV_Engine["OpenCV Preprocessing (CLAHE, Bilateral, Resize)"]
        OCREngine["OCR Engine (EasyOCR CRAFT + CRNN)"]
        CMVRValidator["CMVR Syntax & State Directory Validator"]
        ViolationEngine["Traffic Violation Detector (Stop-Line Vector Crossing)"]
    end

    subgraph Storage ["Persistence Layer"]
        Database[("SQLite Database (WAL Mode)")]
        DiskStore["File Store (Plate Crops, Evidence Frames, Videos)"]
    end

    Dashboard & Records & Violations & Eval <-->|REST JSON| Router
    LiveView <-->|MJPEG Stream| StreamEndpoint
    VideoSuite -->|Async Upload| Router

    Router --> JobManager
    StreamEndpoint --> VehicleModel
    JobManager --> VehicleModel

    VehicleModel --> MOT
    MOT --> PlateModel
    PlateModel --> CV_Engine
    CV_Engine --> OCREngine
    OCREngine --> CMVRValidator
    MOT & CMVRValidator --> ViolationEngine

    CMVRValidator --> DBLayer
    ViolationEngine --> DBLayer
    DBLayer --> Database
    PlateModel -.-> DiskStore
    ViolationEngine -.-> DiskStore
```

---

## 2. Computer Vision Pipeline Data Flow Diagram (DFD Level-1)

```mermaid
sequenceDiagram
    autonumber
    actor User as Traffic Camera / Video Source
    participant VDet as Vehicle Detector (YOLOv8n)
    participant Tracker as Vehicle Tracker (ByteTrack)
    participant PDet as Plate Detector (YOLOv8n-Plate)
    participant CV as OpenCV Preprocessor
    participant OCR as EasyOCR Engine
    participant Vio as Violation Detector
    participant DB as SQLite DB

    User->>VDet: Ingests 2D Video Frame
    VDet->>VDet: Detects Car, Motorcycle, Bus, Truck
    VDet->>Tracker: Bounding Boxes + Confidence
    Tracker->>Tracker: Computes IoU & Associates Track ID
    Tracker->>PDet: Vehicle ROIs + Track ID
    PDet->>PDet: Localizes License Plate Region
    PDet->>CV: Plate Crop Region
    CV->>CV: Bicubic Scale + Bilateral Filter + CLAHE
    CV->>OCR: Enhanced Image Matrix
    OCR->>OCR: CRAFT Heatmap + ResNet CRNN Decoding
    OCR->>Tracker: Text + Confidence + CMVR Status
    Tracker->>Tracker: Majority Voting (Best Candidate)
    Tracker->>Vio: Vehicle Trajectory Vector
    Vio->>Vio: Check Directional Stop-Line Crossing
    alt Stop Line Crossed
        Vio->>Vio: Generate Evidence Snapshot Image
        Vio->>DB: Record Violation Incident
    end
    Tracker->>DB: Persist Vehicle & Plate Record
```

---

## 3. Entity-Relationship (ER) Database Diagram

```mermaid
erDiagram
    VEHICLE_DETECTION ||--o{ LICENSE_PLATE : "contains"
    LICENSE_PLATE ||--o{ VIOLATION : "cited_in"
    PROCESSING_JOB ||--o{ VEHICLE_DETECTION : "processes"

    VEHICLE_DETECTION {
        int id PK
        int tracking_id
        string vehicle_type
        float vehicle_confidence
        datetime detected_at
        string source_type
        string source_name
    }

    LICENSE_PLATE {
        int id PK
        int vehicle_detection_id FK
        string raw_text
        string normalized_text
        float ocr_confidence
        float plate_confidence
        string validation_status
        string plate_image_path
        datetime created_at
    }

    VIOLATION {
        int id PK
        int license_plate_id FK
        int tracking_id
        string violation_type
        datetime event_timestamp
        string evidence_image_path
        string verification_status
    }

    PROCESSING_JOB {
        string id PK
        string filename
        string status
        int total_frames
        int processed_frames
        int total_vehicles
        int total_plates
        string output_video_path
        datetime started_at
        datetime completed_at
    }
```
