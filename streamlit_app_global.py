import streamlit as st
import pandas as pd
import plotly.express as px

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Infectious Disease Dashboard',
    page_icon=':microbe:',  # This is an emoji shortcode. Could be a URL too.
)

# --------------------------------------------------------------------
# Function to load and filter data
@st.cache_data
def load_data():
    """Load and process global infectious disease outbreak data."""
    # Load data
    df = pd.read_csv('./globalDiseaseOutbreaks/Outbreaks.csv').drop(columns='Unnamed: 0')

    # Convert year to datetime for easier filtering
    df['date'] = pd.to_datetime(df['Year'].astype(str) + "-01-01")  # Assume January 1st as date

    return df

def calculate_outbreak_trends(df, countries, start_date, end_date):
    """Calculate statistics on infectious disease outbreaks for selected countries and date range."""
    df_filtered = df[
        (df['Country'].isin(countries)) & 
        (df['date'] >= start_date) & 
        (df['date'] <= end_date)
    ]
    
    # Calculate metrics
    total_unique_outbreaks = df_filtered['Disease'].nunique()
    unique_diseases_list = df_filtered['Disease'].unique()
    frequency_of_each_disease = df_filtered['Disease'].value_counts().to_dict()
    icd10_categories_count = df_filtered['icd10c'].nunique()
    icd11_categories_count = df_filtered['icd11c1'].nunique()
    
    yearly_outbreak_trend = df_filtered.groupby(df_filtered['date'].dt.year).size().to_dict()

    return {
        "total_unique_outbreaks": total_unique_outbreaks,
        "unique_diseases_list": list(unique_diseases_list),
        "frequency_of_each_disease (years)": frequency_of_each_disease,
        "icd10_categories_count": icd10_categories_count,
        "icd11_categories_count": icd11_categories_count,
        "yearly_outbreak_trend": yearly_outbreak_trend
    }

# Load data
outbreaks_df = load_data()

# --------------------------------------------------------------------
# Draw the actual page
st.title(":microbe: Infectious Disease Outbreak Dashboard")

st.markdown("""
This dashboard displays data on infectious disease outbreaks globally. 
You can filter by country and time range to explore trends and visualize data over time.
""")

# --------------------------------------------------------------------
# Interactive widgets for selecting the date range and countries
min_year = int(outbreaks_df['Year'].min())
max_year = int(outbreaks_df['Year'].max())

start_year, end_year = st.slider(
    "Select time range",
    min_value=min_year,
    max_value=max_year,
    value=[min_year, max_year]
)

countries = outbreaks_df['Country'].unique()
selected_countries = st.multiselect(
    "Select countries of interest",
    countries,
    ['Afghanistan', 'Brazil', 'India']
)

if not selected_countries:
    st.warning("Please select at least one country.")

# Filter the data based on user selections
filtered_outbreaks_df = outbreaks_df[
    (outbreaks_df['Country'].isin(selected_countries)) & 
    (outbreaks_df['Year'] >= start_year) & 
    (outbreaks_df['Year'] <= end_year)
]

# Calculate outbreak statistics
if selected_countries:
    outbreak_stats = calculate_outbreak_trends(
        outbreaks_df, 
        countries=selected_countries, 
        start_date=f"{start_year}-01-01", 
        end_date=f"{end_year}-12-31"
    )

    # Create tabs for different views
    tab1, tab2 = st.tabs(["Dashboard View", "Details View"])

    # Tab 1: Dashboard View
    with tab1:
        # Display the yearly outbreak trends as a line chart
        st.header("Outbreak Trend Over Time")
        yearly_trend_df = pd.DataFrame({
            "Year": list(outbreak_stats['yearly_outbreak_trend'].keys()),
            "Outbreaks": list(outbreak_stats['yearly_outbreak_trend'].values())
        })
        st.line_chart(yearly_trend_df, x='Year', y='Outbreaks')

        # Show calculated metrics
        st.header(f"Outbreak Metrics from {start_year} to {end_year}")
        cols = st.columns(4)

        with cols[0]:
            st.metric("Total Unique Outbreaks", outbreak_stats["total_unique_outbreaks"])

        with cols[1]:
            st.metric("ICD-10 Categories", outbreak_stats["icd10_categories_count"])

        with cols[2]:
            st.metric("ICD-11 Categories", outbreak_stats["icd11_categories_count"])

        with cols[3]:
            st.metric("Countries Selected", len(selected_countries))

        # Choropleth visualization using Plotly
        st.header("Outbreaks by Country")
        country_outbreak_counts = filtered_outbreaks_df.groupby("Country").size().reset_index(name='Outbreaks')
        fig = px.choropleth(
            country_outbreak_counts,
            locations="Country",
            locationmode="country names",
            color="Outbreaks",
            hover_name="Country",
            color_continuous_scale="Viridis",
            labels={"Outbreaks": "Number of Outbreaks"}
        )
        st.plotly_chart(fig)

    # Tab 2: Details View
    with tab2:
        st.header("Frequency of Each Disease")
        disease_counts_df = pd.DataFrame(list(outbreak_stats["frequency_of_each_disease (years)"].items()), columns=["Disease", "Count"])
        st.dataframe(disease_counts_df)