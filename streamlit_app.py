import streamlit as st
import pandas as pd
import plotly.express as px

# Load the dataset
@st.cache_data
def load_outbreak_data():
    df = pd.read_csv('./globalDiseaseOutbreaks/Outbreaks.csv').drop(columns='Unnamed: 0')
    df['date'] = pd.to_datetime(df['Year'].astype(str) + "-01-01")  # Convert year to datetime
    return df

@st.cache_data
def load_infectious_cases_data():
    return pd.read_csv('infectiouscases.csv')

# Define a function to calculate infectious case trends
def calculate_infectious_cases_trends(df, entity, start_date, end_date, disease_condition):
    start_year = int(pd.to_datetime(start_date).year)
    end_year = int(pd.to_datetime(end_date).year)
    df['date'] = pd.to_datetime(df['Year'].astype(str) + "-01-01")

    df_filtered = df[(df['Entity'] == entity) & (df['date'] >= start_date) & (df['date'] <= end_date)]

    if disease_condition:
        if disease_condition not in df_filtered.columns:
            raise ValueError(f"Disease condition '{disease_condition}' not found in the dataset.")
        total_cases_per_disease = {disease_condition: df_filtered[disease_condition].sum(skipna=True)}
        total_cases_overall = total_cases_per_disease[disease_condition]
        missing_data_per_disease = {disease_condition: df_filtered[disease_condition].isna().sum()}
    else:
        total_cases_per_disease = df_filtered.iloc[:, 3:].sum(numeric_only=True, skipna=True).to_dict()
        total_cases_overall = sum(total_cases_per_disease.values())
        missing_data_per_disease = df_filtered.iloc[:, 3:].isna().sum().to_dict()

    all_years = set(range(start_year, end_year + 1))
    missing_years = all_years.difference(set(df_filtered['Year']))
    missing_data_flag = len(missing_years) > 0

    if disease_condition:
        yearly_disease_trends = df_filtered.groupby('Year')[disease_condition].sum().to_dict()
    else:
        yearly_disease_trends = df_filtered.groupby('Year').sum(numeric_only=True).to_dict(orient='index')

    return {
        "total_cases_per_disease": total_cases_per_disease,
        "total_cases_overall": total_cases_overall,
        "missing_data_flag": missing_data_flag,
        "missing_years": list(missing_years),
        "missing_data_per_disease": missing_data_per_disease,
        "yearly_disease_trends": yearly_disease_trends
    }

# Load data
outbreaks_df = load_outbreak_data()
infectiouscases = load_infectious_cases_data()

# Set up tabs in Streamlit
st.set_page_config(
    page_title='Infectious Disease Analysis',
    page_icon=':microbe:',
)

tab1, tab2 = st.tabs(["Global Outbreak Dashboard", "Infectious Disease Trend Analysis"])

# --------------------------------------------------------------------
# Tab 1: Global Outbreak Dashboard
with tab1:
    st.title(":microbe: Infectious Disease Outbreak Dashboard")
    st.markdown("""
        This dashboard displays data on infectious disease outbreaks globally. 
        You can filter by country and time range to explore trends and visualize data over time.
    """)

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
    else:
        outbreak_stats = calculate_outbreak_trends(
            outbreaks_df, 
            countries=selected_countries, 
            start_date=f"{start_year}-01-01", 
            end_date=f"{end_year}-12-31"
        )

        yearly_trend_df = pd.DataFrame({
            "Year": list(outbreak_stats['yearly_outbreak_trend'].keys()),
            "Outbreaks": list(outbreak_stats['yearly_outbreak_trend'].values())
        })

        st.header("Outbreak Trend Over Time")
        st.line_chart(yearly_trend_df, x='Year', y='Outbreaks')

        cols = st.columns(4)

        with cols[0]:
            st.metric("Total Unique Outbreaks", outbreak_stats["total_unique_outbreaks"])
        
        with cols[1]:
            st.metric("ICD-10 Categories", outbreak_stats["icd10_categories_count"])
        
        with cols[2]:
            st.metric("ICD-11 Categories", outbreak_stats["icd11_categories_count"])

        with cols[3]:
            st.metric("Countries Selected", len(selected_countries))

        country_outbreak_counts = outbreaks_df.groupby("Country").size().reset_index(name='Outbreaks')
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

        st.header("Frequency of Each Disease")
        disease_counts_df = pd.DataFrame(list(outbreak_stats["frequency_of_each_disease (years)"].items()), columns=["Disease", "Count"])
        st.dataframe(disease_counts_df)

# --------------------------------------------------------------------
# Tab 2: Infectious Disease Trend Analysis
with tab2:
    st.title("Infectious Disease Trend Analysis")
    st.write("Select parameters to analyze trends for infectious diseases.")

    entity = st.selectbox("Select Entity", options=infectiouscases['Entity'].unique(), index=0)
    start_date = st.date_input("Select Start Date", value=pd.to_datetime("1920-01-01"))
    end_date = st.date_input("Select End Date", value=pd.to_datetime("2020-12-31"))
    disease_condition = st.selectbox("Select Disease Condition", options=['All'] + [
        'polio', 'guinea worm', 'rabies', 'malaria', 'hiv/aids', 'tuberculosis', 'smallpox', 'cholera'
    ])

    if st.button("Analyze"):
        selected_disease = None if disease_condition == 'All' else disease_condition
        try:
            result = calculate_infectious_cases_trends(infectiouscases, entity, start_date, end_date, selected_disease)

            st.subheader("Analysis Results")
            if result['missing_data_flag']:
                st.warning("Data contains missing years. These are estimated values and may not be reflective of true statistics due to missing data.")

            st.write("### Total Cases Overall")
            st.write(result['total_cases_overall'])

            st.write("### Total Cases per Disease")
            st.write(result['total_cases_per_disease'])

            st.write("### Yearly Trends")
            st.line_chart(pd.DataFrame(result['yearly_disease_trends']).transpose())
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
