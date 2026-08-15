# ComplaintIQ — AI-Powered Smart Complaint Management System

A production-grade **Django REST API** + **Interactive Dashboard** for managing
complaints in apartments, offices, hostels, and organizations.

## About

ComplaintIQ is a full-stack complaint management system designed for
apartments, offices, hostels, and organizations that need a structured
way to log, track, and resolve complaints. It combines a Django REST
Framework backend with a lightweight HTML/JS dashboard, and includes
smart automation like keyword-based priority detection so urgent
complaints don't sit in a queue.

Built as a learning/portfolio project to demonstrate REST API design,
CRUD operations, filtering, and dashboard analytics — with room to grow
into AI-powered modules (voice input, sentiment analysis, chatbot support,
image attachments).

## Features

- **Full CRUD** — Complaints, Departments, Staff, Assignments
- **Auto Priority Detection** — Scans description keywords automatically
- **Complaint Tracking** — Real-time timeline from submission to resolution
- **Advanced Filters** — Filter by status, priority, department, date range
- **Dashboard Stats** — Charts, metrics, department breakdown
- **DashStack UI** — Modern admin dashboard in pure HTML/JS

## Tech Stack

| Layer    | Technology                         |
| -------- | ---------------------------------- |
| Backend  | Django 4.2 + Django REST Framework |
| Filters  | django-filter                      |
| CORS     | django-cors-headers                |
| Frontend | HTML5 + CSS3 + Chart.js            |
| DB       | SQLite (dev) / PostgreSQL (prod)   |

## API Endpoints

| Method         | Endpoint                     | Description               |
| -------------- | ---------------------------- | ------------------------- |
| GET/POST       | /api/complaints/             | List/Create complaints    |
| POST           | /api/complaints/create/      | Create with auto-priority |
| GET/PUT/DELETE | /api/complaints/<id>/        | CRUD single complaint     |
| PATCH          | /api/complaints/<id>/status/ | Update status only        |
| GET            | /api/complaints/<id>/track/  | Timeline tracking         |
| GET/POST       | /api/departments/            | Departments               |
| GET/POST       | /api/staff/                  | Staff members             |
| GET/POST       | /api/assignments/            | Assign complaints         |
| GET            | /api/stats/                  | Dashboard statistics      |

## Setup & Run

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `frontend/index.html` in your browser.
Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

smart-complaint-ai/
├── backend/
│ ├── complaints/ # Main app (models, views, serializers)
│ ├── core/ # Django settings, root URLs
│ └── requirements.txt
├── voice_module/ # Task 1 — Voice input
├── sentiment_module/ # Task 2 — Sentiment analysis
├── ai_support_module/ # Task 3 — AI chatbot support
├── image_module/ # Task 4 — Image attachments
├── frontend/ # HTML dashboard
└── README.md
