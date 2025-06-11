import streamlit as st
from pathlib import Path
import sys

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.cognitive_data_provider import CognitiveDataProvider

st.set_page_config(layout="wide")

st.title("🧠 Cognitive Insights")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=30)
def get_insights_data():
    provider = CognitiveDataProvider()
    return {
        "summary": provider.get_cognitive_summary(),
        "recent_thoughts": provider.get_recent_thoughts(limit=100)
    }

data = get_insights_data()
summary = data.get('summary', {})

# --- Summary Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Thoughts", summary.get('thought_summary', {}).get('total_thoughts', 0))
with col2:
    st.metric("Total Memories", summary.get('memory_summary', {}).get('total_memories', 0))
with col3:
    st.metric("Confidence Level", f"{summary.get('system_status', {}).get('confidence_level', 0):.1f}%")

st.markdown("<hr/>", unsafe_allow_html=True)

# --- Recent AI Thoughts ---
st.subheader("Recent AI Thoughts")
thoughts_data = data.get('recent_thoughts', [])
if thoughts_data:
    st.dataframe(thoughts_data, height=500)
else:
    st.info("No recent AI thoughts to display.")

# --- Future Feature: Thought Explorer ---
st.subheader("Thought Explorer")
with st.container():
    st.info("A more advanced thought explorer with search and filtering will be implemented here.")
