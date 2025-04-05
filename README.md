# VoiceMorph – Personalized Voice Changer Platform

VoiceMorph is a modular, AI-powered voice conversion platform that allows users to record and send their own voice, train a model based on a target speaker, and transform new voice inputs into the target voice. 

The system routes conversion tasks to external rvc APIs (currently [Replicate](https://replicate.com/)), prioritizes them based on user subscription tier, and will eventually migrate to an in-house, cost-efficient inference service.

---

## 🔧 Tech Stack

- **FastAPI** for API server  
- **Beanie** for MongoDB ODM  
- **Docker / Docker Compose** for containerization  
- **fastapi-mongo-base Python framework** (published on PyPI) for scaffolding and development structure  
- **Replicate** (temporary) for voice conversion backend  
- **Modular app structure** supporting task-based execution  

---

## 📁 Project Structure

```
.
├── app/
│   ├── apps/
│   │   ├── neda/          # voice conversion logic
│   │   └── voice/         # voice-related APIs
│   ├── server/            # App server and configuration
│   ├── utils/             # Utilities: finance logic, media handling, etc.
│   └── Dockerfile
├── docker-compose.yml
├── README.md
└── sample.env
```

---

## 🧠 Core Components

- `apps.voice`:  
  Handles management of available target voice models.  
  - `schemas.py`: Data structures for request/response validation  
  - `models.py`: MongoDB voice model definitions  
  - `services.py`: Business logic for managing voice models  
  - `routes.py`: REST endpoints for adding and listing models  

- `apps.neda`:  
  Contains the core voice conversion APIs.  
  - Accepts voice conversion requests from users  
  - Sends tasks to the external RVC backend (Replicate)  
  - Selects the appropriate target voice model  

- `utils.finance`:  
  Connects to an external finance microservice  
  - Fetches user subscription info  
  - Prioritizes tasks based on subscription tier  

- `server.worker`:  
  Manages periodic background checks on tasks  
  - Detects and retries incomplete conversions  
  - Handles failure recovery in case of webhook errors  

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-org/voicemorph.git
cd voicemorph
```

### 2. Configure environment
Copy the example environment file and fill in required values:
```bash
cp sample.env .env
```

### 3. Run with Docker
```bash
docker-compose up --build
```

The app should be available at `http://localhost:8000`.

---

## 📌 Future Roadmap

- 🔄 Migrate from Replicate to self-hosted GPU inference
- 📊 Add user dashboard for voice model and task management

---

## 📄 License

MIT License
