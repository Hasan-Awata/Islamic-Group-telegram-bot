# Islamic Group Manager Telegram Bot 📖

A robust, asynchronous Telegram bot designed to manage and track group Quran readings (Khetma). Built with Python and PostgreSQL, this bot features real-time inline keyboard updates, Arabic language pattern matching, and a clean, event-driven backend architecture.

## 📜 Backstory & Context
In Islam, a **Khetma** is a group Quran reading session where participants distribute the 30 parts (Juz') of the book among themselves. Every participant takes one or more parts, reads them, and then notifies the group when they are finished. When all 30 parts are completed, the Khetma is considered finished.

This is a deeply valued act of worship in the Islamic faith. This solution was created to serve the community by automating the tracking of these sessions, completely removing the need for manual record-keeping in group chats.

**Note:** The Quran "Part" (Juz') is referred to as "Chapter" in the codebase for easier standard maintenance.

## 🚀 Features

### 1. Khetma (Group Reading Session)
* **Real-Time State Management:** Users can reserve, free up, or finish parts with instant visual feedback via dynamically updating inline keyboards.
* **Arabic Pattern Matching:** Users can simply type natural Arabic phrases like `"تم 1 و 2"` or `"تم أجزائي"`. The bot parses the numbers, validates database ownership, and updates the UI automatically.
* **Arabic Numerals-from-text Extraction:** The bot can extract all numbers written in a user's text regardless of format (`"21"`, `"الحادي والعشرون"`, `"٢١"`).
* **Role-Based Access Control (RBAC):** Only authorized group admins can create a Khetma, preventing spam and accidental creations.
* **Concurrency Safety:** Prevents race conditions (e.g., two users trying to reserve the exact same part at the exact same millisecond) using strict database-level constraints and custom Python domain errors.
* **Owner Lookup:** Pressing a reserved chapter button shows who reserved it via a Telegram toast notification, keeping the UI clean.

### 2. Daily Prayers Tracker
* *Coming soon...* ⏳

### 3. Hadith Authenticity Checker
* *Coming soon...* ⏳

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Framework:** `python-telegram-bot` (v20+ Async)
* **Database:** PostgreSQL (via `psycopg2`)
* **Architecture:** Repository Pattern

## 🏗️ Architecture & Design Patterns

This project was built with professional backend engineering principles in mind:
* **Separation of Concerns:** The database layer (`KhetmaStorage`) purely interacts with PostgreSQL and returns custom domain objects. It has zero knowledge of Telegram's UI or text formatting.
* **Custom Error Handling:** Uses domain-specific exceptions (e.g., `ChapterNotOwnedError`, `ChapterFinishedError`) so the presentation layer can gracefully format user-facing error messages without crashing the application.
* **Efficient Database I/O:** Uses bulk SQL updates and prevents the "N+1 query problem" to ensure the bot remains fast and memory-efficient even in large groups.
* **Connection Safety:** Every database operation uses a managed connection context that automatically commits on success and rolls back on failure.

## ⚙️ Local Setup & Installation

1. Clone the repository:
```bash
   git clone https://github.com/Hasan-Awata/Islamic-Group-telegram-bot
```

2. Install the required dependencies:
```bash
   pip install -r requirements.txt
```

3. Set up a PostgreSQL database and create a dedicated user:
```sql
   CREATE DATABASE khetma_bot;
   CREATE USER khetma_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE khetma_bot TO khetma_user;
```

4. Create a `.env` file in the root directory with the following:
```
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql://khetma_user:your_password@localhost:5432/khetma_bot
```

5. Run the bot:
```bash
   python main.py
```

The database tables are created automatically on first startup.