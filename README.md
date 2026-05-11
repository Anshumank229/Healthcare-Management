
# 🏥 Healthcare Management Platform

## 📋 Overview
A comprehensive healthcare management system with patient management, appointment scheduling, **fully integrated WhatsApp notifications**, and AI-powered analytics.

---

## ✨ Features

### ✅ Implemented (Live)

| Module | Description |
|--------|-------------|
| **Authentication** | JWT-based, role-based access (Admin, Doctor, Staff, Patient) |
| **Patient Management** | Full CRUD, medical records, emergency contacts |
| **Appointment System** | Booking, conflict detection, availability check |
| **WhatsApp Integration** | ✅ Send reminders ✅ Receive confirmations ✅ Real-time replies |
| **Role-Based Access** | Patient/Doctor/Staff/Admin with different permissions |
| **Webhook Receiver** | Auto-process patient replies (CONFIRM / CANCEL) |

### 🚀 Planned
- n8n Automation Workflows
- AI Prediction Models (No-show, Churn)
- Revenue Forecasting

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy ORM |
| Auth | JWT + bcrypt |
| Validation | Pydantic |
| Messaging | **WhatsApp Cloud API** |
| Tunneling | ngrok (webhook development) |
| Automation | n8n (self-hosted) |

---

## 📁 Project Structure


healthcare-platform/
├── backend/
│ ├── app/
│ │ ├── auth/ # JWT authentication
│ │ ├── patients/ # Patient CRUD
│ │ ├── appointments/ # Booking system
│ │ ├── whatsapp/ # Webhook handler
│ │ ├── services/ # WhatsApp service
│ │ ├── models/ # Database models
│ │ ├── schemas/ # Pydantic schemas
│ │ ├── core/ # DB connection
│ │ └── main.py # FastAPI entry
│ └── requirements.txt
├── .gitignore
└── README.md



---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- ngrok (for webhook testing)

### 1. Clone the repo
```bash
git clone https://github.com/Anshumank229/Healthcare-Management.git
cd Healthcare-Management



Set up virtual environment
bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows



Install dependencies
bash
pip install -r requirements.txt


Configure PostgreSQL
bash
sudo -u postgres psql          # or `psql -U postgres`
CREATE DATABASE healthcare_db;


Environment variables (create .env file)
text
DATABASE_URL=postgresql://postgres:password@localhost/healthcare_db
SECRET_KEY=your-secret-key

WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_WABA_ID=your_waba_id



 Create database tables
bash
python -m app.create_tables



Start the server
bash
uvicorn app.main:app --reload


Start ngrok (for WhatsApp webhook)
bash
ngrok http 8000


Open API docs
👉 http://localhost:8000/docs


WhatsApp Integration – How It Works
Appointment is booked → Auto-send reminder via WhatsApp

Patient replies → Webhook receives message

System processes reply → Updates appointment status

Confirmation message → Sent back to patient



Example patient flow
text
📨 Reminder: Your appointment with Dr. Smith is tomorrow at 10 AM.
👤 Patient replies:  CONFIRM
✅ Webhook: Appointment confirmed → status updated
📊 API Endpoints
Method	Endpoint	Description	Auth
POST	/auth/signup	Register user	❌
POST	/auth/login	Get JWT token	❌
GET	/auth/me	Current user info	✅
POST	/patients/	Create patient	✅
GET	/patients/	List patients	✅
POST	/appointments/	Book appointment	✅
GET	/appointments/	List appointments	✅
GET	/appointments/doctor/{id}/availability	Check slots	✅
GET	/notifications/	View notifications	✅
🔐 Security
JWT tokens with expiration

bcrypt password hashing

Role-based endpoint protection

.env excluded from version control

WhatsApp tokens never exposed

📈 Database Schema
Table	Purpose
users	Authentication & roles
patients	Medical records
appointments	Booking details
notifications	Scheduled reminders
🧪 Testing the Webhook Locally
bash
curl -X GET "https://your-ngrok-url/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=healthcare_webhook_2024&hub.challenge=123456"
# Expected response: 123456
Then send a WhatsApp message to +1 555 645 8925 → check your FastAPI terminal.

👨‍💻 Author
Anshuman

GitHub: @Anshumank229

⭐ Star the repo
If you find this project useful, please give it a star — it helps others discover it.

📌 Live WhatsApp integration · Auto reminders · Patient confirmation handling

text

---

## ✅ What changed from your previous README:

- ✅ **WhatsApp moved from "In Progress" → implemented**  
- ✅ Added **webhook explanation** – shows how patient replies work  
- ✅ Added **WhatsApp environment variables** to the `.env` section  
- ✅ Added **ngrok step** (necessary for webhook testing)  
- ✅ Added **Example patient flow** – makes it clear to recruiters  
- ✅ Added **Webhook test command**  

---

## 🔁 How to update your repository README

Run the following commands **from your project root**:

```bash
cd "D:\Placements\Placements Ready Work\Projects\healthcare-platform"
git add README.md
git commit -m "docs: update README with completed WhatsApp integration and webhook flow"
git push origin main
