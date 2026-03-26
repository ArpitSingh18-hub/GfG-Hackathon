import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# -----------------------------
# API endpoints
# -----------------------------

API_QUERY = "http://127.0.0.1:8000/api/query"
API_UPLOAD = "http://127.0.0.1:8000/api/upload"


# -----------------------------
# Page config
# -----------------------------

st.set_page_config(
    page_title="DataWhisper.ai",
    page_icon="🤖",
    layout="wide"
)


# -----------------------------
# Session State
# -----------------------------

if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False

if "history" not in st.session_state:
    st.session_state.history = []


# -----------------------------
# Header
# -----------------------------

st.title("🤖 DataWhisper.ai")

st.markdown(
"""
### Conversational AI for Data Analytics  

Upload a dataset and ask questions in **natural language**.  
DataWhisper will automatically generate **SQL, charts, and insights**.
"""
)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:

    st.header("📁 Dataset Manager")

    uploaded_file = st.file_uploader(
        "Upload CSV Dataset",
        type=["csv"]
    )

    if uploaded_file:

        if st.button("Upload Dataset"):

            files = {"file": uploaded_file}

            try:

                r = requests.post(API_UPLOAD, files=files)

                if r.status_code == 200:

                    st.success("Dataset uploaded successfully")

                    st.session_state.dataset_loaded = True

                    preview_df = pd.read_csv(uploaded_file)

                    st.session_state.dataset_preview = preview_df.head(20)

                else:
                    st.error("Upload failed")

            except:
                st.error("Backend not reachable")


    st.divider()

    st.subheader("⚙ System Status")

    if st.session_state.dataset_loaded:
        st.success("Dataset Ready")
    else:
        st.warning("Upload dataset first")


    st.divider()

    st.subheader("📜 Query History")

    for q in st.session_state.history[-5:]:
        st.write("•", q)


# -----------------------------
# Dataset Preview
# -----------------------------

if "dataset_preview" in st.session_state:

    st.subheader("Dataset Preview")

    st.dataframe(st.session_state.dataset_preview)


# -----------------------------
# Query Input
# -----------------------------

st.subheader("💬 Ask Your Data")

query = st.text_input(
    "Enter a natural language query",
    placeholder="Example: Average fare by passenger class"
)

run_query = st.button("Run Analysis")


# -----------------------------
# Run Query
# -----------------------------

if run_query:

    if not st.session_state.dataset_loaded:
        st.error("Upload dataset first")
        st.stop()

    if not query:
        st.warning("Enter a query")
        st.stop()

    with st.spinner("DataWhisper analyzing your data..."):

        try:

            response = requests.post(API_QUERY, json={"query": query})

        except:
            st.error("Backend not running")
            st.stop()

        if response.status_code != 200:
            st.error("Backend error")
            st.stop()

        result = response.json()

        if not result["success"]:
            st.error("Query failed")
            st.stop()

        data = result["data"]["data"]
        chart = result["data"]["chart_info"]
        sql = result["data"]["generated_sql"]
        insight = result["data"]["insight"]

        df = pd.DataFrame(data)

        st.session_state.history.append(query)


# -----------------------------
# Layout
# -----------------------------

    col1, col2 = st.columns([2, 1])


# -----------------------------
# Chart Section
# -----------------------------

    with col1:

        st.subheader("📊 Visualization")

        chart_type = chart.get("chart_type", "table")

        try:

            if chart_type == "bar":

                fig = px.bar(
                    df,
                    x=chart["x_axis"],
                    y=chart["y_axis"][0],
                    title=chart.get("title", "Chart"),
                    color_discrete_sequence=chart.get("color_palette", None)
                )

                st.plotly_chart(fig, use_container_width=True)


            elif chart_type == "line":

                fig = px.line(
                    df,
                    x=chart["x_axis"],
                    y=chart["y_axis"][0],
                    title=chart.get("title", "Chart")
                )

                st.plotly_chart(fig, use_container_width=True)


            elif chart_type == "scatter":

                fig = px.scatter(
                    df,
                    x=chart["x_axis"],
                    y=chart["y_axis"][0],
                    title=chart.get("title", "Chart")
                )

                st.plotly_chart(fig, use_container_width=True)


            elif chart_type == "pie":

                fig = px.pie(
                    df,
                    names=chart["x_axis"],
                    values=chart["y_axis"][0],
                    title=chart.get("title", "Chart")
                )

                st.plotly_chart(fig, use_container_width=True)


            elif chart_type == "number":

                value = df.iloc[0][chart["y_axis"][0]]

                st.metric(
                    label=chart.get("title", "Value"),
                    value=value
                )

            else:

                st.dataframe(df)

        except:

            st.warning("Chart rendering failed — showing table instead")

            st.dataframe(df)


# -----------------------------
# Insight + SQL
# -----------------------------

    with col2:

        st.subheader("💡 AI Insight")

        st.info(insight)

        st.subheader("🧠 Generated SQL")

        st.code(sql, language="sql")


# -----------------------------
# Data Table
# -----------------------------

    st.subheader("📋 Query Result")

    st.dataframe(df) 