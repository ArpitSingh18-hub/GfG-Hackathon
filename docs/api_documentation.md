# Conversational BI Dashboard API Documentation

This API powers the Conversational BI Dashboard, allowing users to upload data, query it using natural language, and receive visualization-ready data.

## Base URL
`http://localhost:8000/api`

## Response Format
All responses follow a standard structure:
```json
{
  "success": boolean,
  "data": object | null,
  "error": string | null,
  "meta": object | null
}
```

---

## 1. Data Upload

### `POST /upload`
Upload a CSV file to the system. The file will be processed and stored in a DuckDB table.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (CSV file)

**Sample Request (cURL):**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@sales_data.csv"
```

**Sample Response (Success):**
```json
{
  "success": true,
  "data": {
    "message": "Successfully uploaded sales_data.csv",
    "table_name": "sales_data",
    "rows_loaded": 1500,
    "columns": ["order_date", "region", "product", "sales", "quantity"]
  },
  "error": null,
  "meta": null
}
```

**Sample Response (Error - Invalid File):**
```json
{
  "success": false,
  "data": null,
  "error": "Only CSV files are supported.",
  "meta": null
}
```

---

## 2. Conversational Query

### `POST /query`
Convert natural language to SQL and get back data with chart suggestions.

**Request Body:**
```json
{
  "query": "string",
  "previous_query": "string (optional)",
  "previous_sql": "string (optional)"
}
```

**Sample Request:**
```json
{
  "query": "Show me total sales by region for the last 3 months"
}
```

**Sample Response (Success with Chart Suggestion):**
```json
{
  "success": true,
  "data": {
    "user_query": "Show me total sales by region for the last 3 months",
    "generated_sql": "SELECT region, SUM(sales) as total_sales FROM sales_data WHERE order_date >= '2023-10-01' GROUP BY region",
    "data": [
      { "region": "North", "total_sales": 12500.50 },
      { "region": "South", "total_sales": 9800.20 },
      { "region": "East", "total_sales": 15200.00 }
    ],
    "chart_info": {
      "chart_type": "bar",
      "x_axis": "region",
      "y_axis": ["total_sales"],
      "title": "Total Sales by Region",
      "description": "A bar chart comparing sales performance across different regions.",
      "color_palette": ["#8884d8", "#82ca9d", "#ffc658", "#ff8042"]
    },
    "insight": "The East region is currently leading in sales, outperforming the North by 21%.",
    "summary": {
      "row_count": 3,
      "column_count": 2,
      "columns": ["region", "total_sales"]
    }
  },
  "error": null,
  "meta": null
}
```

**Sample Response (Success with Multi-Column Chart):**
```json
{
  "success": true,
  "data": {
    "user_query": "Compare sales and profit by product category",
    "generated_sql": "SELECT category, SUM(sales) as total_sales, SUM(profit) as total_profit FROM performance_data GROUP BY category",
    "data": [
      { "category": "Electronics", "total_sales": 45000, "total_profit": 12000 },
      { "category": "Furniture", "total_sales": 32000, "total_profit": 5000 }
    ],
    "chart_info": {
      "chart_type": "bar",
      "x_axis": "category",
      "y_axis": ["total_sales", "total_profit"],
      "title": "Sales vs Profit by Category",
      "description": "A multi-bar chart comparing sales and profit metrics.",
      "color_palette": ["#8884d8", "#82ca9d", "#ffc658", "#ff8042"]
    },
    "insight": "Electronics category has a significantly higher profit margin (26.7%) compared to Furniture (15.6%).",
    "summary": {
      "row_count": 2,
      "column_count": 3,
      "columns": ["category", "total_sales", "total_profit"]
    }
  },
  "error": null,
  "meta": null
}
```

**Sample Response (Error - No Data):**
```json
{
  "success": false,
  "data": null,
  "error": "No dataset uploaded. Please upload a CSV first.",
  "meta": null
}
```

**Sample Response (Error - Invalid SQL/Query):**
```json
{
  "success": false,
  "data": {
      "user_query": "What is the meaning of life?",
      "generated_sql": "SELECT meaning FROM life;"
  },
  "error": "Table 'life' does not exist in the database.",
  "meta": null
}
```

---

## 3. Error Handling

The API uses standard HTTP status codes:
- `200 OK`: Successful request.
- `400 Bad Request`: Validation errors (e.g., missing query, wrong file type).
- `404 Not Found`: Resource not found.
- `500 Internal Server Error`: Server-side bugs.
- `502 Bad Gateway`: LLM service issues.

All errors return a JSON body with `success: false` and a descriptive `error` message.

---

## 4. Frontend Integration Tips

### Recharts Example (React)
```javascript
const response = await fetch('/api/query', { ... });
const result = await response.json();

if (result.success) {
  const { data, chart_info } = result.data;
  
  if (chart_info.chart_type === 'bar') {
    return (
      <BarChart data={data}>
        <XAxis dataKey={chart_info.x_axis} />
        <YAxis />
        {chart_info.y_axis.map((yKey, index) => (
          <Bar key={yKey} dataKey={yKey} fill={chart_info.color_palette[index]} />
        ))}
      </BarChart>
    );
  }
}
```

### Chart.js Example
```javascript
const ctx = document.getElementById('myChart');
new Chart(ctx, {
  type: result.data.chart_info.chart_type,
  data: {
    labels: result.data.data.map(row => row[result.data.chart_info.x_axis]),
    datasets: result.data.chart_info.y_axis.map((yKey, index) => ({
      label: yKey,
      data: result.data.data.map(row => row[yKey]),
      backgroundColor: result.data.chart_info.color_palette[index]
    }))
  }
});
```
