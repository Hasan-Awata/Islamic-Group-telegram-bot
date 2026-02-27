# Islamic Group Manager Telegram Bot 📖

A robust, asynchronous Telegram bot designed to manage and track group Quran readings (Khetma). Built with Python and SQLite, this bot features real-time inline keyboard updates, natural language parsing, and a clean, event-driven backend architecture.

## 📜 Backstory & Context
A **Khetma** is a group Quran reading session where participants distribute the 30 parts (Juz') of the book among themselves. Every participant takes one or more parts, reads them, and then notifies the group when they are finished. When all 30 parts are completed, the Khetma is considered finished. 

This is a deeply valued act of worship in the Islamic faith. This solution was created to serve the community by automating the tracking of these sessions, completely removing the need for manual record-keeping in group chats.

**Note:** The Quran "Part" (Juz') is referred to as "Chapter" in the codebase for easier standard maintenance.

## 🚀 Features

### 1. Khetma (Group Reading Session)
* **Real-Time State Management:** Users can reserve, free up, or finish parts with instant visual feedback via dynamically updating inline keyboards.
* **Arabic Pattern Matching:** Users can simply type natural Arabic phrases like `"تم 1 و 2"` or `"تم أجزائي"`. The bot parses the numbers, validates database ownership, and updates the UI automatically.
* **Arabic Numerals-from-text Extraction:** The bot can extract all the numbers written in a user's text no matter what is the way they wrote the numbers in (`"21"`, `"الحادي والعشرون"`, `"٢١"`). 
* **Role-Based Access Control (RBAC):** Only authorized group admins can create or delete a Khetma, preventing spam and accidental deletions.
* **Concurrency Safety:** Prevents race conditions (e.g., two users trying to reserve the exact same part at the exact same millisecond) using strict database-level constraints and custom Python domain errors.

### 2. Hadith Authenticity Checker
* *Coming soon...* ⏳

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Framework:** `python-telegram-bot` (v20+ Async)
* **Database:** SQLite3
* **Architecture:** Repository Pattern

## 🏗️ Architecture & Design Patterns

This project was built with professional backend engineering principles in mind:
* **Separation of Concerns:** The database layer (`KhetmaStorage`) purely interacts with SQLite and returns custom domain objects. It has zero knowledge of Telegram's UI or text formatting.
* **Custom Error Handling:** Uses domain-specific exceptions (e.g., `ChapterNotOwnedError`, `ChapterFinishedError`) so the presentation layer can gracefully format user-facing error messages without crashing the application.
* **Efficient Database I/O:** Uses bulk SQL updates and prevents the "N+1 query problem" to ensure the bot remains lightning fast and memory-efficient even in large groups.

## ⚙️ Local Setup & Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/YourUsername/YourRepoName.git](https://github.com/YourUsername/YourRepoName.git)
   ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    Create a .env file in the root directory and add your Telegram Bot Token:
    ```
3. Create a .env file in the root directory and add your Telegram Bot Token:
    ```bash
    BOT_TOKEN=your_telegram_api_token_here
    Run the bot:
    ```
4. Run the code
    ```bash
    python main.py 
    ```