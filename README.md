# 💬 Django Chat Application 

This is a **real-time chat application** built with **Django** and **Django Channels**.
The app allows users to sign up, log in, join chat rooms, and exchange real-time messages.

---

## 🚀 Features

- **Custom User Authentication**
  - User signup, login, and logout
  - User profile auto-created on signup

- **Real-time Chat**
  - WebSockets powered by Django Channels
  - Persistent 1 to 1 chat, with multiple participants
  - Messages stored in PostgreSQL / SQLite DB

- **Chat Rooms**
  - Create and join chat rooms
  - See active participants
  - Messages ordered by timestamps

- **Backend-First Focus**
  - API-ready backend logic (can be extended with Django REST Framework)
  - Frontend kept minimal (HTML, JS, CSS)

---

## 🛠️ Tech Stack

- **Backend Framework:** Django 5.x
- **WebSockets:** Django Channels
- **Database:** SQLite (default) / PostgreSQL (recommended)
- **ASGI Server:** Daphne
- **Frontend (minimal):** HTML, CSS, JS

---



