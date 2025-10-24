import docker
import requests
import streamlit as st

st.set_page_config(page_title="Debug UI", layout="wide")

# state for query results
st.session_state.setdefault("query_result", [])

# Connect to Docker
client = docker.from_env()
containers = {c.name: c for c in client.containers.list()}


# Docker Info tab
with st.expander("🐳 Docker Containers"):
    for c in containers.values():
        st.write(f"**{c.name}** — {c.status}")
        st.json(c.attrs["NetworkSettings"]["Ports"])


# Sidebar
st.sidebar.header("🔎 Endpoint Inspector")
default_endpoints = {
    "Loki Labels": "http://loki:3100/loki/api/v1/labels",
    "Prometheus Targets": "http://prometheus:9090/api/v1/targets",
    "Grafana Health": "http://grafana:3000/api/health",
}
choice = st.sidebar.selectbox("Select Endpoint", list(default_endpoints.keys()))
url = st.sidebar.text_input("URL", value=default_endpoints[choice])
method = st.sidebar.selectbox("Method", ["GET", "POST"])
send = st.sidebar.button("Query")

# Query
if send:
    try:
        r = requests.request(method, url, timeout=5)
        st.session_state.query_result.append(r)
    except Exception as e:
        st.error(f"Error: {e}")


def display_response(r: requests.Response):
    st.code(f"{r.request.method} {r.request.url} {r.status_code} {r.reason}")
    content_type = r.headers.get("Content-Type", "")
    if "application/json" in content_type:
        st.json(r.json())
    else:
        st.text(r.text)


# Display query results
with st.expander("📡 Query Results", expanded=True):
    for r in st.session_state.query_result[::-1]:
        display_response(r)
        st.markdown("---")
