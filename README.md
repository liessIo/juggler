# Juggler - Self-Hosted Multi-Model AI Chat

![Project Status: v2 Restart - Under Active Development](https://img.shields.io/badge/status-v2_restart-orange)

Juggler is a self-hosted multi-model AI chat system designed for small teams and organizations. This repository contains the complete restart of the project (v2) with a focus on simplicity, stability, and a clear architecture.

## Core Concepts (v2)

* **Single Tenant, Multiple Users**: The system is designed for a single organization, but supports multiple user accounts to keep chat histories separate.
* **Shared API Keys**: All users share the same set of API keys, which are configured centrally via environment variables.
* **Simple Architecture**: A clear and maintainable FastAPI backend and a modern Vue.js 3 frontend.
* **Focus on Essentials**: The primary goal is to provide a reliable, multi-provider chat experience without over-engineering.

## Tech Stack

* **Backend**: FastAPI (Python), SQLAlchemy
* **Frontend**: Vue.js 3 with TypeScript, Pinia, Tailwind CSS
* **AI Providers**: Designed to be extensible, with initial support for Ollama, Groq, and Gemini.

## Getting Started

> **Note**: This project is currently in the initial setup phase. These instructions will be updated as the components become functional.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/liessIo/juggler.git](https://github.com/liessIo/juggler.git)
    cd juggler
    ```

2.  **Set up the Backend:**
    ```bash
    # Navigate to the backend directory
    cd backend

    # Create a Python virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    * Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    * Edit the `.env` file and add your `SECRET_KEY` and the necessary API keys for the providers you want to use.

4.  **Run the application (coming soon):**
    ```bash
    # (Instructions to start the FastAPI server will be added here)
    ```

## Project Goals

The main goal of v2 is to build a stable and maintainable application by following a clear, step-by-step implementation plan and adhering to a strict API contract between the frontend and backend.