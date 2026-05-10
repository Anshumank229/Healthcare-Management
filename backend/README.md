echo "# 🏥 Healthcare Management Platform

## 📋 Overview
A comprehensive healthcare management system with patient management, appointment scheduling, WhatsApp notifications, and AI-powered analytics.

## ✨ Features

### ✅ Implemented
- **Authentication System** (JWT-based, role-based access control)
- **Patient Management** (CRUD operations, medical records)
- **Appointment System** (Booking, conflict detection, availability check)
- **Notification System** (Scheduled reminders, WhatsApp integration ready)
- **Role-Based Access** (Admin, Doctor, Staff, Patient)

### 🚀 In Progress
- WhatsApp Cloud API Integration
- n8n Automation Workflows
- AI Prediction Models (No-show, Churn)

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Auth | JWT + bcrypt |
| Validation | Pydantic |
| Automation | n8n (self-hosted) |
| Messaging | WhatsApp Cloud API |

## 📁 Project Structure

\`\`\`
healthcare-platform/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT authentication
│   │   ├── patients/      # Patient CRUD
│   │   ├── appointments/  # Booking system
│   │   ├── notifications/ # Reminder system
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── core/          # DB connection
│   │   └── main.py        # FastAPI entry
│   └── requirements.txt
└── .gitignore
\`\`\`

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git

### Installation

1. **Clone repository**
   \`\`\`bash
   git clone https://github.com/Anshumank229/Healthcare-Management.git
   cd Healthcare-Management
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   \`\`\`

3. **Install dependencies**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Configure database**
   \`\`\`bash
# Create PostgreSQL database
psql -U postgres
CREATE DATABASE healthcare_db;
\`\`\`

5. **Run migrations**
   \`\`\`bash
   python -c \"from app.core.database import engine, Base; from app.models.user import User; from app.models.patient import Patient; from app.models.appointment import Appointment; from app.models.notification import Notification; Base.metadata.create_all(bind=engine)\"
   \`\`\`

6. **Start server**
   \`\`\`bash
   uvicorn app.main:app --reload
   \`\`\"

7. **Access API docs**
   Open http://localhost:8000/docs

## 📊 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /auth/signup | User registration | ❌ |
| POST | /auth/login | Get JWT token | ❌ |
| GET | /auth/me | Current user | ✅ |
| POST | /patients/ | Create patient | ✅ |
| GET | /patients/ | List patients | ✅ |
| POST | /appointments/ | Book appointment | ✅ |
| GET | /appointments/ | List appointments | ✅ |
| GET | /appointments/doctor/{id}/availability | Check slots | ✅ |
| GET | /notifications/ | View notifications | ✅ |

## 🔐 Environment Variables

Create \`.env\` file:

\`\`\`env
DATABASE_URL=postgresql://postgres:password@localhost/healthcare_db
SECRET_KEY=your-secret-key-here
\`\`\`

## 📈 Database Schema

- **users** - Authentication & roles
- **patients** - Medical records
- **appointments** - Booking details
- **notifications** - Scheduled reminders

## 🤝 Contributing
This is a personal project for learning and demonstration.

## 📝 License
MIT

## 👨‍💻 Author
**Anshuman**
- GitHub: [@Anshumank229](https://github.com/Anshumank229)

---
⭐ Star this repo if you find it helpful!
" > README.md