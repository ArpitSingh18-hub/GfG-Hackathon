# Setup Instructions

## Prerequisites
- Python 3.9+
- A Google Gemini API key (for SQL generation via LLM).

## Setup Steps

1. **Clone the repository** (if not already done).

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Load Data**
   Run the data loader script to ingest the dataset into DuckDB. Ensure `data/YouTube Content Creation_clean.csv` exists.
   ```bash
   python -m backend.database.load_data
   ```

6. **Run the Application**
   You can run the FastAPI backend via uvicorn (once `main.py` is fully set up with the FastAPI app instance):
   ```bash
   uvicorn main:app --reload
   ```

   (Note: The application entrypoint in `main.py` might need to be created if not currently implemented, importing the routers from `backend.api.dashboard_api`).
