"""
SmartWaste AI - Intelligent Waste Management System
Main Streamlit application entry point.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import database as db
import prediction as pred
from waste_classifier import classify_waste, get_all_items, get_categories
from chatbot import ask_waste_assistant, QUICK_QUESTIONS

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="SmartWaste AI",
    page_icon="🗑️",
    layout="wide",
)

# -------------------- INIT DB --------------------
db.init_db()

# -------------------- SESSION STATE --------------------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# -------------------- SIDEBAR NAVIGATION --------------------
st.sidebar.title("🗑️ SmartWaste AI")
st.sidebar.caption("Intelligent Waste Management System")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "📊 Bin Monitoring",
        "🤖 AI Waste Assistant",
        "🔮 Pickup Prediction",
        "♻️ Waste Classification",
        "🌍 SDG Impact Dashboard",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**SDG Goals**")
st.sidebar.markdown("- SDG 11: Sustainable Cities\n- SDG 12: Responsible Consumption\n- SDG 13: Climate Action")

# ======================================================
# HOME PAGE
# ======================================================
if page == "🏠 Home":
    st.title("🗑️ SmartWaste AI")
    st.subheader("Intelligent Waste Management System")
    st.write(
        "SmartWaste AI helps municipalities monitor waste bins, predict overflow, "
        "optimize collection schedules, and promote sustainable waste management."
    )

    col1, col2, col3 = st.columns(3)
    bins_df = db.get_all_bins()
    with col1:
        st.metric("Total Bins Monitored", len(bins_df))
    with col2:
        avg_fill = round(bins_df["fill_level"].mean(), 1) if not bins_df.empty else 0
        st.metric("Average Fill Level", f"{avg_fill}%")
    with col3:
        overflow_count = len(bins_df[bins_df["fill_level"] >= pred.OVERFLOW_THRESHOLD])
        st.metric("Bins Near Overflow", overflow_count)

    st.markdown("### Key Features")
    st.markdown(
        "- **Smart Bin Monitoring** — live fill levels and overflow warnings\n"
        "- **AI Waste Assistant** — chat-based sustainability guidance\n"
        "- **Pickup Prediction** — forecasts when bins will be full\n"
        "- **Waste Classification** — sorts items into Recyclable, Organic, E-waste, Hazardous\n"
        "- **SDG Impact Dashboard** — tracks landfill diversion, CO₂ reduction, recycling rate"
    )

# ======================================================
# BIN MONITORING PAGE
# ======================================================
elif page == "📊 Bin Monitoring":
    st.title("📊 Smart Bin Monitoring")

    bins_df = db.get_all_bins()

    if bins_df.empty:
        st.warning("No bin data available.")
    else:
        # Overflow warnings
        overflow_bins = bins_df[bins_df["fill_level"] >= pred.OVERFLOW_THRESHOLD]
        if not overflow_bins.empty:
            st.error(f"⚠️ {len(overflow_bins)} bin(s) are near overflow!")
            for _, row in overflow_bins.iterrows():
                st.warning(f"Bin {row['bin_id']} at {row['location']} — {row['fill_level']}% full")

        st.markdown("### Bin Fill Levels")

        # Bar chart of fill levels
        fig = px.bar(
            bins_df, x="bin_id", y="fill_level", color="fill_level",
            color_continuous_scale=["green", "yellow", "red"],
            labels={"fill_level": "Fill Level (%)", "bin_id": "Bin ID"},
            title="Current Fill Levels by Bin",
        )
        fig.add_hline(y=pred.OVERFLOW_THRESHOLD, line_dash="dash", line_color="red",
                       annotation_text="Overflow Threshold")
        st.plotly_chart(fig, use_container_width=True)

        # Individual bin progress bars
        st.markdown("### Bin Details")
        for _, row in bins_df.iterrows():
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{row['bin_id']}** — {row['location']} ({row['waste_type']})")
                st.progress(min(int(row["fill_level"]), 100) / 100)
            with c2:
                st.write(f"{row['fill_level']}%")
                if st.button(f"Mark Collected", key=f"collect_{row['bin_id']}"):
                    db.mark_bin_collected(row["bin_id"])
                    st.rerun()

        st.markdown("### Raw Data")
        st.dataframe(bins_df, use_container_width=True)

# ======================================================
# AI WASTE ASSISTANT PAGE
# ======================================================
elif page == "🤖 AI Waste Assistant":
    st.title("🤖 AI Waste Assistant")
    st.write("Ask me anything about waste reduction, recycling, or sustainability!")

    st.markdown("**Quick Questions:**")
    cols = st.columns(len(QUICK_QUESTIONS))
    for i, q in enumerate(QUICK_QUESTIONS):
        if cols[i].button(q, key=f"quick_{i}"):
            st.session_state.chat_messages.append({"role": "user", "content": q})
            response = ask_waste_assistant(q, st.session_state.chat_messages[:-1])
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            db.log_chat(q, response)

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask a sustainability question...")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        response = ask_waste_assistant(user_input, st.session_state.chat_messages[:-1])
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
        db.log_chat(user_input, response)

# ======================================================
# PICKUP PREDICTION PAGE
# ======================================================
elif page == "🔮 Pickup Prediction":
    st.title("🔮 Pickup Prediction")
    st.write("Predicts when each bin will become full and prioritizes collection.")

    bins_df = db.get_all_bins()

    if bins_df.empty:
        st.warning("No bin data available.")
    else:
        priority_df = pred.get_priority_collection_list(bins_df)

        urgency_colors = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        st.markdown("### Collection Priority List")
        for _, row in priority_df.iterrows():
            icon = urgency_colors.get(row["urgency"], "⚪")
            st.write(f"{icon} **{row['bin_id']}** ({row['location']}) — {row['message']}")

        st.markdown("### Predicted Days to Full")
        fig = px.bar(
            priority_df, x="bin_id", y="days_to_full", color="urgency",
            color_discrete_map={"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "gold", "LOW": "green"},
            labels={"days_to_full": "Days to Full", "bin_id": "Bin ID"},
            title="Predicted Time Until Each Bin is Full",
        )
        st.plotly_chart(fig, use_container_width=True)

        if st.button("Generate Collection Alerts"):
            urgent = priority_df[priority_df["urgency"].isin(["CRITICAL", "HIGH"])]
            for _, row in urgent.iterrows():
                db.log_alert(row["bin_id"], row["message"])
            st.success(f"{len(urgent)} alert(s) generated and logged.")

        st.markdown("### Full Prediction Table")
        st.dataframe(priority_df, use_container_width=True)

# ======================================================
# WASTE CLASSIFICATION PAGE
# ======================================================
elif page == "♻️ Waste Classification":
    st.title("♻️ Waste Classification")
    st.write("Select or type a waste item to find out how to dispose of it correctly.")

    col1, col2 = st.columns(2)
    with col1:
        selected_item = st.selectbox("Choose a known item", [""] + get_all_items())
    with col2:
        custom_item = st.text_input("Or type your own item")

    item_to_classify = custom_item.strip() if custom_item.strip() else selected_item

    if st.button("Classify Item") and item_to_classify:
        result = classify_waste(item_to_classify)
        db.log_classification(result["item"], result["category"])

        category_icons = {
            "Recyclable": "♻️", "Organic": "🌱", "E-waste": "💻",
            "Hazardous": "☣️", "General Waste": "🗑️",
        }
        icon = category_icons.get(result["category"], "🗑️")

        st.success(f"{icon} **{result['item']}** → **{result['category']}**")
        st.info(result["tip"])

    st.markdown("### Classification Categories")
    for cat in get_categories():
        st.write(f"- {cat}")

    st.markdown("### Recent Classification History")
    history_df = db.get_classification_history()
    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.caption("No classifications logged yet.")

# ======================================================
# SDG IMPACT DASHBOARD PAGE
# ======================================================
elif page == "🌍 SDG Impact Dashboard":
    st.title("🌍 SDG Impact Dashboard")
    st.write("Tracking SmartWaste AI's contribution to sustainability goals.")

    bins_df = db.get_all_bins()
    history_df = db.get_classification_history(limit=1000)

    # --- Simple illustrative metrics ---
    # Assume each collected/classified recyclable/organic item diverts ~0.5 kg from landfill
    diverted_items = 0
    if not history_df.empty:
        diverted_items = len(history_df[history_df["category"].isin(["Recyclable", "Organic"])])
    waste_diverted_kg = round(diverted_items * 0.5, 1)

    # CO2 reduction estimate: ~1.2 kg CO2 saved per kg of waste diverted from landfill (illustrative factor)
    co2_reduced_kg = round(waste_diverted_kg * 1.2, 1)

    # Recycling rate: recyclable classifications / total classifications
    recycling_rate = 0
    if not history_df.empty:
        recyclable_count = len(history_df[history_df["category"] == "Recyclable"])
        recycling_rate = round((recyclable_count / len(history_df)) * 100, 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Waste Diverted from Landfill", f"{waste_diverted_kg} kg")
    col2.metric("CO₂ Emissions Reduced", f"{co2_reduced_kg} kg")
    col3.metric("Recycling Rate", f"{recycling_rate}%")

    st.markdown("---")
    st.markdown("### Waste Category Breakdown")
    if not history_df.empty:
        cat_counts = history_df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.pie(cat_counts, names="category", values="count",
                     title="Classified Waste by Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Classify some items on the Waste Classification page to see this chart.")

    st.markdown("### SDG Alignment")
    st.markdown(
        "- **SDG 11 (Sustainable Cities):** Optimized collection reduces overflow and street litter.\n"
        "- **SDG 12 (Responsible Consumption):** Correct classification increases recycling and composting.\n"
        "- **SDG 13 (Climate Action):** Diverting waste from landfill reduces methane and CO₂ emissions."
    )

    st.caption("Note: Impact figures are illustrative estimates based on logged activity, "
               "intended to demonstrate the dashboard concept.")
