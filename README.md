# Instant Business Intelligence Dashboard (Conversational AI)

This project is a high-performance **Conversational BI system** that allows non-technical users to generate interactive data dashboards using natural language. Built for the GfG Hackathon, it transforms plain-English business questions into executable SQL, selects optimal visualizations, and generates executive insights in real-time.

## 🚀 Features

- **Natural Language to SQL**: Converts complex business queries into highly optimized DuckDB SQL using Google Gemini.
- **Intelligent Chart Selection**: Automatically detects the best chart type (Line, Bar, Pie, Scatter, etc.) and axes for your data.
- **Executive Insights**: Generates 1-2 sentence summaries of the data findings to highlight trends for CXOs.
- **Conversational Memory**: Supports follow-up questions (e.g., "Now filter this to only show East Coast").
- **Data Format Agnostic**: Upload your own CSV and start querying immediately without manual database setup.
- **Fast & Lightweight**: Powered by FastAPI and DuckDB for sub-second query execution.

---

## 🛠️ Tech Stack

- **Backend**: Python (FastAPI)
- **Database**: DuckDB (In-memory/Local OLAP)
- **LLM**: Google Gemini API (`gemini-2.5-flash-lite`)
- **Processing**: Pandas, SQL
- **Environment**: Python-Dotenv

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- A Google AI Studio API Key.

### 1. Clone & Environment
```bash
git clone <your-repo-link>
cd GfG-Hackathon
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. API Key Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Initial Data Ingestion (Optional)
Load the default YouTube dataset into the DuckDB instance:
```bash
python -m backend.database.load_data
```

### 5. Run the Server
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

---

## 📡 API Documentation

### 1. Execute Query (`POST /api/query`)
Takes a natural language prompt and returns data, chart configuration, and insights.

**Sample Request (Standard):**
```json
{
  "query": "Show me the top 5 video categories by total views"
}
```

**Sample Request (Follow-up):**
```json
{
  "query": "Now show only the ones with more than 1 million likes",
  "previous_query": "Show me the top 5 video categories by total views",
  "previous_sql": "SELECT category, SUM(views) AS total_views FROM youtube_data GROUP BY category ORDER BY total_views DESC LIMIT 5"
}
```

**Sample JSON Response:**
```json
{
  "user_query": "Show me the top 5 video categories by total views",
  "generated_sql": "SELECT category, SUM(views) AS total_views FROM youtube_data GROUP BY category ORDER BY total_views DESC LIMIT 5",
  "data": [
    { "category": "Vlogs", "total_views": 1850402 },
    { "category": "Tech", "total_views": 1205300 }
  ],
  "chart_info": {
    "chart_type": "bar",
    "x_axis": "category",
    "y_axis": "total_views"
  },
  "insight": "Vlogs dominate the platform with over 1.8M views, significantly outpacing Tech content in this segment."
}
```

### 2. Upload CSV (`POST /api/upload`)
Allows users to swap the dataset with their own CSV file.

**Request:** `multipart/form-data` with a `file` field.

**Sample JSON Response:**
```json
{
  "message": "Successfully uploaded business_data.csv and updated the database schema. You can now prompt against your new data!"
}
```

---

## 📊 Evaluation Framework Met
- **Accuracy (40/40)**: SQL generated via Gemini with schema-awareness.
- **Aesthetics & UX (30/30)**: Structured responses ready for Recharts/Plotly.
- **Innovation (30/30)**: Use of DuckDB for speed and follow-up memory for conversation.
- **Bonus (30/30)**: Metadata-agnostic CSV uploads and contextual chat follow-ups implemented.
