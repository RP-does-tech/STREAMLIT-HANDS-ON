from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Interactive Visualization",
    layout="wide",
)

st.title("Interactive Visualization")
st.caption(
    "Demonstration of filtering, selection, zoom/pan, tooltips, "
    "brushing and linking, drill-down, and parameter controls."
)

df = pd.read_csv("interactivedummydata.csv")

month_order = ["Aug", "Sep", "Oct", "Nov"]
df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

if st.sidebar.button("Reset controls"):
    for key in [
        "faculty_filter", "programme_filter", "year_filter",
        "score_threshold", "drill_faculty", "drill_programme"
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.sidebar.header("1. Filtering")

faculty_options = sorted(df["Faculty"].unique())
selected_faculties = st.sidebar.multiselect(
    "Faculty",
    faculty_options,
    default=faculty_options,
    key="faculty_filter",
)

faculty_subset = df[df["Faculty"].isin(selected_faculties)].copy()
programme_options = sorted(faculty_subset["Programme"].unique())

selected_programmes = st.sidebar.multiselect(
    "Programme",
    programme_options,
    default=programme_options,
    key="programme_filter",
)

year_options = sorted(df["Year_Level"].unique())
selected_years = st.sidebar.multiselect(
    "Year level",
    year_options,
    default=year_options,
    key="year_filter",
)

st.sidebar.header("2. Parameter Control")
score_threshold = st.sidebar.slider(
    "High-performance threshold",
    min_value=60,
    max_value=90,
    value=80,
    step=1,
    key="score_threshold",
)

filtered = df[
    (df["Faculty"].isin(selected_faculties))
    & (df["Programme"].isin(selected_programmes))
    & (df["Year_Level"].isin(selected_years))
].copy()

filtered["Performance_Class"] = filtered["Assessment_Score"].apply(
    lambda x: "High" if x >= score_threshold else "Other"
)

st.subheader("Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Visible records", len(filtered))
c2.metric(
    "Mean score",
    f"{filtered['Assessment_Score'].mean():.1f}" if len(filtered) else "N/A",
)
c3.metric(
    "Mean attendance",
    f"{filtered['Attendance_Rate_pct'].mean():.1f}%" if len(filtered) else "N/A",
)
high_count = int((filtered["Performance_Class"] == "High").sum()) if len(filtered) else 0
c4.metric(f"High performers (>= {score_threshold})", high_count)

if filtered.empty:
    st.warning("The current filters return no records. Change the filters or reset the controls.")
    st.stop()

st.subheader("Selection, Zoom/Pan and Tooltips")
st.write(
    "Hover over points for tooltips. Use the Plotly toolbar to zoom or pan. "
    "Use point, box or lasso selection. The linked views below respond to the selection."
)

scatter = px.scatter(
    filtered,
    x="Study_Hours_per_Week",
    y="Assessment_Score",
    color="Performance_Class",
    size="LMS_Logins",
    hover_name="Record_ID",
    hover_data={
        "Faculty": True,
        "Programme": True,
        "Year_Level": True,
        "District": True,
        "Attendance_Rate_pct": ":.1f",
        "LMS_Logins": True,
        "Satisfaction_Rating": True,
        "Study_Hours_per_Week": ":.1f",
        "Assessment_Score": ":.1f",
    },
    custom_data=["Record_ID"],
    title="Study Hours vs Assessment Score",
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
    linked_data = filtered[filtered["Record_ID"].isin(selected_ids)].copy()
    st.success(f"{len(linked_data)} record(s) selected. Linked views use this selection.")
else:
    linked_data = filtered.copy()
    st.caption("No points selected. Linked views currently use all filtered records.")

st.subheader("Brushing and Linking")
left, right = st.columns([1.1, 1])

programme_summary = (
    linked_data
    .groupby("Programme", observed=True, as_index=False)
    .agg(
        Mean_Score=("Assessment_Score", "mean"),
        Records=("Record_ID", "count"),
    )
    .sort_values("Mean_Score", ascending=True)
)

linked_bar = px.bar(
    programme_summary,
    x="Mean_Score",
    y="Programme",
    orientation="h",
    hover_data=["Records"],
    title="Mean Score for the Current Selection",
)
left.plotly_chart(linked_bar, use_container_width=True, config={"displaylogo": False})

right.write("**Details on demand: current records**")
right.dataframe(
    linked_data[
        [
            "Record_ID", "Faculty", "Programme", "Year_Level",
            "District", "Study_Hours_per_Week",
            "Attendance_Rate_pct", "Assessment_Score"
        ]
    ].sort_values("Assessment_Score", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Drill-Down")
st.write("Move from a faculty-level overview to programme-level detail.")

faculty_summary = (
    filtered
    .groupby("Faculty", observed=True, as_index=False)
    .agg(
        Mean_Score=("Assessment_Score", "mean"),
        Records=("Record_ID", "count"),
    )
)

faculty_bar = px.bar(
    faculty_summary,
    x="Faculty",
    y="Mean_Score",
    hover_data=["Records"],
    title="Faculty-Level Overview",
)
st.plotly_chart(faculty_bar, use_container_width=True, config={"displaylogo": False})

drill_faculty = st.selectbox(
    "Choose a faculty to drill down",
    sorted(filtered["Faculty"].unique()),
    key="drill_faculty",
)

faculty_detail = filtered[filtered["Faculty"] == drill_faculty].copy()

drill_programme = st.selectbox(
    "Choose a programme",
    sorted(faculty_detail["Programme"].unique()),
    key="drill_programme",
)

programme_detail = faculty_detail[
    faculty_detail["Programme"] == drill_programme
].copy()

monthly = (
    programme_detail
    .groupby("Month", observed=True, as_index=False)
    .agg(
        Mean_Score=("Assessment_Score", "mean"),
        Mean_Attendance=("Attendance_Rate_pct", "mean"),
    )
    .sort_values("Month")
)

line = px.line(
    monthly,
    x="Month",
    y="Mean_Score",
    markers=True,
    title=f"Programme Detail: {drill_programme}",
)
st.plotly_chart(line, use_container_width=True, config={"displaylogo": False})

st.subheader("What This Application Demonstrates")
st.markdown(
    """
- **Filtering:** Faculty, programme and year-level controls change the visible subset.
- **Selection:** Select individual points or use box/lasso selection.
- **Zoom and pan:** Use Plotly's toolbar and mouse controls.
- **Tooltips:** Hover over marks to reveal exact values and metadata.
- **Brushing and linking:** Selecting points updates the linked bar chart and data table.
- **Drill-down:** Move from faculty level to programme-level detail.
- **Parameter controls:** Change the high-performance threshold and observe the classification change.
- **Details on demand:** Exact record information appears only when requested.
"""
)

st.caption("The dataset is synthetic and intended only for demonstration purposes only.")
