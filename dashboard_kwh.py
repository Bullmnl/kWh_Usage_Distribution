import streamlit as st
st.set_page_config(page_title="kWh Usage Distribution", layout="wide")  # Must be the first command

import pandas as pd
import plotly.express as px

# -------------------------
# Load and Prepare the Data
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_excel('Raw_Session.xlsx', engine='openpyxl')
    
    # Rename columns for easier handling and convert start time to datetime
    df.rename(columns={'Start Time TH': 'start_time'}, inplace=True)
    df['start_time'] = pd.to_datetime(df['start_time'])
    
    # Ensure Kwh is numeric
    df['Kwh'] = pd.to_numeric(df['Kwh'], errors='coerce')
    
    # Extract month name from start_time for filtering
    df['month_name'] = df['start_time'].dt.month_name()
    
    # Map cities to regions in Thailand.
    region_mapping = {
        "Bangkok": "Metropolitan",
        "Nonthaburi": "Metropolitan",
        "Pathum Thani": "Metropolitan",
        "Samut Prakan": "Metropolitan",
        "Nakhon Pathom": "Central",
        "Phra Nakhon Si Ayutthaya": "Central",
        "Chiang Mai": "North",
        "Chiang Rai": "North",
        "Lampang": "North",
        "Nakhon Ratchasima": "North East",
        "Khon Kaen": "North East",
        "Udon Thani": "North East",
        "Nakhon Si Thammarat": "South",
        "Phuket": "South",
        "Krabi": "South",
        "Songkhla": "South",
        "Rayong": "East",
        "Chonburi": "East",
        "Ratchaburi": "West",
        "Kanchanaburi": "West",
        "Nonthaburi": "Metropolitan",
        "Samut Prakan": "Metropolitan",
        "45000": "North East",
        "Ang Thong": "Central",
        "BANGKOK": "Metropolitan",
        "Buriram": "North East",
        "Chachoengsao": "East",
        "Chai Nat": "Central",
        "Chiang Mai": "North",
        "ChiangMai": "North",
        "Chon Buri": "East",
        "Chumphon": "South",
        "KW.KHLONGTOEI NUEA KT.WATTHANA BANGKOK": "Metropolitan",
        "Kalasin": "North East",
        "Kamphaeng Phet": "North",
        "Lamphun": "North",
        "Loei": "North East",
        "Lop Buri": "Central",
        "Lumphini, Bangkok": "Metropolitan",
        "Maha Sarakham": "North East",
        "Mueang Khon Kaen": "North East",
        "Nakhon Nayok": "Central",
        "Nakhon Phanom": "North East",
        "Nakhon Sawan": "Central",
        "Nakhon sawan": "Central",
        "Nakhonratchasima": "North East",
        "Nakhonsithammarat": "South",
        "Narathiwat": "South",
        "Pathum thani": "Metropolitan",
        "Pattaya": "East",
        "Phayao": "North",
        "Phetchabun": "North",
        "Phetchaburi": "West",
        "Phichit": "Central",
        "Phitsanulok": "Central",
        "Phrae": "North",
        "Prachinburi": "East",
        "Prachuap Khiri Khan": "South",
        "Prachuapkhirikhan": "South",
        "Ranong": "South",
        "Sa Kaeo": "East",
        "Sakon Nakhon": "North East",
        "Samut Sakhon": "Metropolitan",
        "Samut Songkhram": "Central",
        "Samutprakan": "Metropolitan",
        "Saraburi": "Central",
        "Sethasiri Prachachuen, Tha Sai, Mueang": "Metropolitan",
        "Sing Buri": "Central",
        "Sisaket": "North East",
        "Suphanburi": "Central",
        "Surat Thani": "South",
        "Tak": "North",
        "Trang": "South",
        "Ubon Ratchathani": "North East",
        "Uthai Thani": "Central",
        "กรุงเทพมหานคร": "Metropolitan",
        "ฺBangkok": "Metropolitan"
    }
    df['region'] = df['City'].map(region_mapping).fillna("Other")
    
    return df

df = load_data()

# -------------------------
# Streamlit App Title
# -------------------------
st.title("Interactive kWh Usage Distribution")

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("Adjust Filters")

# Dropdown for filtering by Month
unique_months = sorted(df['month_name'].unique(), key=lambda x: pd.to_datetime(x, format='%B').month)
selected_month = st.sidebar.selectbox("Filter by Month", options=["All"] + unique_months)

# Dropdown for filtering by Region
unique_regions = sorted(df['region'].unique())
selected_region = st.sidebar.selectbox("Filter by Region", options=["All"] + unique_regions)

# Dropdown for filtering by City (updates based on selected region)
if selected_region != "All":
    available_cities = sorted(df[df['region'] == selected_region]['City'].unique())
else:
    available_cities = sorted(df['City'].unique())
selected_city = st.sidebar.selectbox("Filter by City", options=["All"] + available_cities)

# Dropdown for filtering by Charger Type
unique_charger_types = sorted(df['Charger Type'].dropna().unique())
selected_charger_type = st.sidebar.selectbox("Filter by Charger Type", options=["All"] + unique_charger_types)

# Axis range sliders (updated limits)
x_min, x_max = st.sidebar.slider(
    "X-axis range (kWh):",
    min_value=0.0,
    max_value=150.0,
    value=(0.0, 150.0),
    step=1.0,
)
y_min, y_max = st.sidebar.slider(
    "Y-axis range (Session Frequency):",
    min_value=0,
    max_value=50000,
    value=(0, 50000),
    step=10,
)

# Slider to adjust the number of bins (affects bar resolution)
bins_count = st.sidebar.slider(
    "Number of Bins:",
    min_value=10,
    max_value=100,
    value=40,
    step=1,
)

# Radio button for contribution breakdown by Region or City
breakdown_option = st.sidebar.radio("Show Contribution Breakdown by:", options=["Region", "City"])

# -------------------------
# Apply Filters to Data
# -------------------------
df_filtered = df.copy()
if selected_month != "All":
    df_filtered = df_filtered[df_filtered['month_name'] == selected_month]
if selected_region != "All":
    df_filtered = df_filtered[df_filtered['region'] == selected_region]
if selected_city != "All":
    df_filtered = df_filtered[df_filtered['City'] == selected_city]
if selected_charger_type != "All":
    df_filtered = df_filtered[df_filtered['Charger Type'] == selected_charger_type]

# -------------------------
# Calculate and Display Statistics
# -------------------------
total_sessions = df_filtered.shape[0]
mean_kwh = df_filtered['Kwh'].mean()
median_kwh = df_filtered['Kwh'].median()
std_kwh = df_filtered['Kwh'].std()

st.markdown("### kWh Usage Statistics")
st.write(f"**Total Sessions:** {total_sessions}")
st.write(f"**Mean kWh:** {mean_kwh:.2f}")
st.write(f"**Median kWh:** {median_kwh:.2f}")
st.write(f"**Standard Deviation:** {std_kwh:.2f}")

# -------------------------
# Create Interactive Histogram using Plotly Express
# -------------------------
fig = px.histogram(
    df_filtered,
    x="Kwh",
    nbins=bins_count,  # Number of bins based on slider value
    title="kWh Usage Distribution",
    labels={"Kwh": "kWh"},
)

# Update axis ranges based on slider values
fig.update_xaxes(range=[x_min, x_max])
fig.update_yaxes(range=[y_min, y_max])

# Add a thin black stroke for each bar and update hover info to show "Session" count
fig.update_traces(
    marker_line_color='black',
    marker_line_width=1,
    hovertemplate="kWh: %{x}<br>Session: %{y}"
)

# -------------------------
# Display the Interactive Histogram
# -------------------------
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Show Contribution Breakdown
# -------------------------
st.markdown("### Contribution Breakdown")
if breakdown_option == "Region":
    # Aggregate kWh by region
    contrib_df = df_filtered.groupby("region")["Kwh"].sum().reset_index()
    total_kwh = contrib_df["Kwh"].sum()
    contrib_df["Percentage"] = 100 * contrib_df["Kwh"] / total_kwh
    fig_pie = px.pie(contrib_df, values="Kwh", names="region", title="Contribution by Region (in % of total kWh)")
    st.plotly_chart(fig_pie, use_container_width=True)
    st.dataframe(contrib_df)
else:
    # Aggregate kWh by city
    contrib_df = df_filtered.groupby("City")["Kwh"].sum().reset_index()
    total_kwh = contrib_df["Kwh"].sum()
    contrib_df["Percentage"] = 100 * contrib_df["Kwh"] / total_kwh
    fig_pie = px.pie(contrib_df, values="Kwh", names="City", title="Contribution by City (in % of total kWh)")
    st.plotly_chart(fig_pie, use_container_width=True)
    st.dataframe(contrib_df)
