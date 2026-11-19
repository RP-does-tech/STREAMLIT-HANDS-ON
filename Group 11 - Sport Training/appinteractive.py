import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="GROUP 11 SPORT TRAINING",
    layout="wide",
)

st.title("GROUP 11 SPORT TRAINING")
st.caption(
    "Demonstration of filtering, selection, zoom/pan, tooltips, "
    "brushing and linking, drill-down, and parameter controls."
)

df = pd.read_csv("group11sporttraining.csv", skiprows=3)
df = df.dropna(how="all")
df["Injury_Flag"] = df["Injury_Flag"].astype(int)
df["Injury_Status"] = df["Injury_Flag"].map({0: "No injury", 1: "Injured"})

if st.sidebar.button("Reset controls"):
    for key in [
        "sport_filter", "injury_filter",
        "score_threshold", "drill_sport"
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.sidebar.header("1. Filtering")

sport_options = sorted(df["Sport"].unique())
selected_sports = st.sidebar.multiselect(
    "Sport",
    sport_options,
    default=sport_options,
    key="sport_filter",
)

injury_options = ["No injury", "Injured"]
selected_injury = st.sidebar.multiselect(
    "Injury status",
    injury_options,
    default=injury_options,
    key="injury_filter",
)

st.sidebar.header("2. Parameter Control")
score_threshold = st.sidebar.slider(
    "High-performance threshold",
    min_value=60,
    max_value=95,
    value=80,
    step=1,
    key="score_threshold",
)

filtered = df[
    (df["Sport"].isin(selected_sports))
    & (df["Injury_Status"].isin(selected_injury))
].copy()

filtered["Performance_Class"] = filtered["Performance_Score"].apply(
    lambda x: "High" if x >= score_threshold else "Other"
)

st.subheader("Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Visible athletes", len(filtered))
c2.metric(
    "Mean performance score",
    f"{filtered['Performance_Score'].mean():.1f}" if len(filtered) else "N/A",
)
c3.metric(
    "Mean sleep hours",
    f"{filtered['Sleep_Hours_per_Night'].mean():.1f}" if len(filtered) else "N/A",
)
high_count = int((filtered["Performance_Class"] == "High").sum()) if len(filtered) else 0
c4.metric(f"High performers (>= {score_threshold})", high_count)

if filtered.empty:
    st.warning("The current filters return no athletes. Change the filters or reset the controls.")
    st.stop()

st.subheader("Selection, Zoom/Pan and Tooltips")
st.write(
    "Hover over points for tooltips. Use the Plotly toolbar to zoom or pan. "
    "Use point, box or lasso selection. The linked views below respond to the selection."
)

scatter = px.scatter(
    filtered,
    x="Training_Hours_per_Week",
    y="Performance_Score",
    color="Performance_Class",
    size="Sleep_Hours_per_Night",
    hover_name="Athlete_ID",
    hover_data={
        "Sport": True,
        "Sleep_Hours_per_Night": ":.1f",
        "Rest_Days_per_Week": True,
        "Injury_Status": True,
        "Training_Hours_per_Week": ":.1f",
        "Performance_Score": ":.1f",
    },
    custom_data=["Athlete_ID"],
    title="Training Hours vs Performance Score",
)
scatter.update_layout(dragmode="select", legend_title_text="Performance class")

event = st.plotly_chart(
    scatter,
    use_container_width=True,
    config={"displaylogo": False, "scrollZoom": True},
    on_select="rerun",
    selection_mode=("points", "box", "lasso"),
    key="main_scatter",
)

selected_ids = []
try:
    selected_points = event.selection.points
except Exception:
    try:
        selected_points = event["selection"]["points"]
    except Exception:
        selected_points = []

for point in selected_points:
    try:
        custom = point["customdata"]
        if custom:
            selected_ids.append(custom[0])
    except Exception:
        pass

if selected_ids:
    linked_data = filtered[filtered["Athlete_ID"].isin(selected_ids)].copy()
    st.success(f"{len(linked_data)} athlete(s) selected. Linked views use this selection.")
else:
    linked_data = filtered.copy()
    st.caption("No points selected. Linked views currently use all filtered athletes.")

st.subheader("Brushing and Linking")
left, right = st.columns([1.1, 1])

sport_summary = (
    linked_data
    .groupby("Sport", observed=True, as_index=False)
    .agg(
        Mean_Score=("Performance_Score", "mean"),
        Athletes=("Athlete_ID", "count"),
    )
    .sort_values("Mean_Score", ascending=True)
)

linked_bar = px.bar(
    sport_summary,
    x="Mean_Score",
    y="Sport",
    orientation="h",
    hover_data=["Athletes"],
    title="Mean Performance Score for the Current Selection",
)
left.plotly_chart(linked_bar, use_container_width=True, config={"displaylogo": False})

right.write("**Details on demand: current athletes**")
right.dataframe(
    linked_data[
        [
            "Athlete_ID", "Sport", "Training_Hours_per_Week",
            "Sleep_Hours_per_Night", "Rest_Days_per_Week",
            "Injury_Status", "Performance_Score"
        ]
    ].sort_values("Performance_Score", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Drill-Down")
st.write("Move from a sport-level overview to athlete-level detail.")

sport_overview = (
    filtered
    .groupby("Sport", observed=True, as_index=False)
    .agg(
        Mean_Score=("Performance_Score", "mean"),
        Athletes=("Athlete_ID", "count"),
    )
)

sport_bar = px.bar(
    sport_overview,
    x="Sport",
    y="Mean_Score",
    hover_data=["Athletes"],
    title="Sport-Level Overview",
)
st.plotly_chart(sport_bar, use_container_width=True, config={"displaylogo": False})

drill_sport = st.selectbox(
    "Choose a sport to drill down",
    sorted(filtered["Sport"].unique()),
    key="drill_sport",
)

sport_detail = (
    filtered[filtered["Sport"] == drill_sport]
    .copy()
    .sort_values("Athlete_ID")
)

detail_bar = px.bar(
    sport_detail,
    x="Athlete_ID",
    y="Performance_Score",
    color="Injury_Status",
    hover_data={
        "Training_Hours_per_Week": ":.1f",
        "Sleep_Hours_per_Night": ":.1f",
        "Rest_Days_per_Week": True,
        "Injury_Status": True,
        "Performance_Score": ":.1f",
    },
    title=f"Athlete Detail: {drill_sport}",
)
st.plotly_chart(detail_bar, use_container_width=True, config={"displaylogo": False})

st.subheader("What This Application Demonstrates")
st.markdown(
    """
- **Filtering:** Sport and injury-status controls change the visible subset.
- **Selection:** Select individual points or use box/lasso selection.
- **Zoom and pan:** Use Plotly's toolbar and mouse controls.
- **Tooltips:** Hover over marks to reveal exact values and metadata.
- **Brushing and linking:** Selecting points updates the linked bar chart and data table.
- **Drill-down:** Move from sport level to athlete-level detail.
- **Parameter controls:** Change the high-performance threshold and observe the classification change.
- **Details on demand:** Exact athlete information appears only when requested.
"""
)

st.caption("The dataset is synthetic and intended only for demonstration purposes only.")
