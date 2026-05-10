# 🏥 Healthcare Management System API

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **production-ready REST API** for managing patients, doctors, and appointments in a healthcare system. Built with modern Python practices and ready for deployment.

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation Guide](#-installation-guide)
- [Database Setup](#-database-setup)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Testing the API](#-testing-the-api)
- [Deployment](#-deployment)
- [Interview Questions](#-interview-questions-answered)
- [Future Improvements](#-future-improvements)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

### Core Features
- ✅ **Complete CRUD operations** for Patients, Doctors, and Appointments
- ✅ **Database relationships** with foreign keys and cascade deletes
- ✅ **Automatic API documentation** (Swagger UI & ReDoc)
- ✅ **Input validation** using Pydantic schemas
- ✅ **Error handling** with proper HTTP status codes
- ✅ **Environment-based configuration** (no hardcoded passwords)

### Technical Features
- ✅ **SQLAlchemy ORM** for database operations
- ✅ **PostgreSQL** for production-ready database
- ✅ **Modular architecture** (Models, Schemas, Routes separation)
- ✅ **Dependency injection** for database sessions
- ✅ **Type hints** throughout the codebase

## 🛠️ Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Programming language | 3.13+ |
| FastAPI | Web framework | 0.104.1 |
| PostgreSQL | Database | 16+ |
| SQLAlchemy | ORM (Object Relational Mapper) | 2.0.23 |
| Pydantic | Data validation | 2.5.0 |
| Uvicorn | ASGI server | 0.24.0 |
| python-dotenv | Environment variables | 1.0.0 |

## 📁 Project Structure


As seeing in Project 

## 💻 Installation Guide

### Prerequisites
- Python 3.13 or higher installed
- PostgreSQL installed and running
- Git installed (optional, for version control)

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/healthcare-management.git
cd healthcare-management


# Windows
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt



DATABASE_URL=postgresql://postgres:your_password@localhost:5432/healthcare_db


CREATE DATABASE healthcare_db;


# Windows (if PostgreSQL is in PATH)
createdb healthcare_db



# Make sure virtual environment is activated
venv\Scripts\activate  # Windows



# Run the FastAPI server
uvicorn app.main:app --reload
