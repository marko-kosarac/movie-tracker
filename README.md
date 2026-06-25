# Movie Tracker

A full-stack web application for tracking movies and TV shows. Browse a curated database, manage your personal watchlist and watched list, and get AI-powered recommendations.

## Features

- Browse movies and TV shows with genre filters, sorting, and search
- Movie and TV show detail pages with cast, description, and backdrop images
- Personal library — watchlist and watched list
- AI chat assistant with agentic RAG (semantic search + database search + direct actions)
- User authentication with JWT tokens
- Avatar selection and password change on profile page

## Tech Stack

**Frontend:** React 18, Vite, React Router  
**Backend:** FastAPI, SQLAlchemy, PostgreSQL  
**AI:** OpenAI GPT-4o-mini, ChromaDB (vector store)  
**Infrastructure:** Docker, Docker Compose, Nginx

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/movie-tracker.git
   cd movie-tracker
   
docker compose up --build

Open http://localhost in your browser.
