# -*- coding: utf-8 -*-
# ============================================================
# EMPLOYMENT MARKET ANALYZER  v3  (Global Edition)
# Run: streamlit run employment_analyzer.py
# ============================================================

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from bs4 import BeautifulSoup
from collections import Counter
import re
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


ADZUNA_APP_ID  = "c70ac2c9"
ADZUNA_APP_KEY = "3ff22631cf990fd15b765165fec473e9"

# ============================================================
# ALL 27 ADZUNA-SUPPORTED COUNTRIES  (grouped by region)
# ============================================================

COUNTRIES_BY_REGION = {
    "Europe": {
        "United Kingdom":  "gb",
        "Germany":         "de",
        "France":          "fr",
        "Netherlands":     "nl",
        "Austria":         "at",
        "Belgium":         "be",
        "Switzerland":     "ch",
        "Poland":          "pl",
        "Spain":           "es",
        "Italy":           "it",
        "Russia":          "ru",
    },
    "Americas": {
        "United States":   "us",
        "Canada":          "ca",
        "Brazil":          "br",
        "Mexico":          "mx",
        "Argentina":       "ar",
    },
    "Asia Pacific": {
        "India":           "in",
        "Australia":       "au",
        "New Zealand":     "nz",
        "Singapore":       "sg",
        "Japan":           "jp",
        "China":           "cn",
        "South Korea":     "kr",
        "Indonesia":       "id",
    },
    "Middle East & Africa": {
        "South Africa":    "za",
        "Nigeria":         "ng",
        "Kenya":           "ke",
    },
}

# Flat dict for lookup
ALL_COUNTRIES = {}
for region, countries in COUNTRIES_BY_REGION.items():
    ALL_COUNTRIES.update(countries)

# Currency per country
CURRENCY_MAP = {
    "gb": "GBP", "de": "EUR", "fr": "EUR", "nl": "EUR",
    "at": "EUR", "be": "EUR", "ch": "CHF", "pl": "PLN",
    "es": "EUR", "it": "EUR", "ru": "RUB",
    "us": "USD", "ca": "CAD", "br": "BRL", "mx": "MXN",
    "ar": "ARS",
    "in": "INR", "au": "AUD", "nz": "NZD", "sg": "SGD",
    "jp": "JPY", "cn": "CNY", "kr": "KRW", "id": "IDR",
    "za": "ZAR", "ng": "NGN", "ke": "KES",
}

# Country flag emoji
FLAG_MAP = {
    "gb": "🇬🇧", "de": "🇩🇪", "fr": "🇫🇷", "nl": "🇳🇱",
    "at": "🇦🇹", "be": "🇧🇪", "ch": "🇨🇭", "pl": "🇵🇱",
    "es": "🇪🇸", "it": "🇮🇹", "ru": "🇷🇺",
    "us": "🇺🇸", "ca": "🇨🇦", "br": "🇧🇷", "mx": "🇲🇽",
    "ar": "🇦🇷",
    "in": "🇮🇳", "au": "🇦🇺", "nz": "🇳🇿", "sg": "🇸🇬",
    "jp": "🇯🇵", "cn": "🇨🇳", "kr": "🇰🇷", "id": "🇮🇩",
    "za": "🇿🇦", "ng": "🇳🇬", "ke": "🇰🇪",
}

# ============================================================
# SKILLS CONFIG
# ============================================================

SKILL_KEYWORDS = {
    "Programming":  ["python", "sql", "r", "java", "javascript",
                     "scala", "c++", "matlab", "typescript", "go"],
    "Data & BI":    ["power bi", "tableau", "excel", "looker",
                     "qlik", "sap", "data analysis", "statistics",
                     "data visualization"],
    "ML & AI":      ["machine learning", "deep learning", "nlp",
                     "tensorflow", "pytorch", "scikit-learn",
                     "computer vision", "llm", "generative ai",
                     "langchain"],
    "Cloud":        ["aws", "azure", "gcp", "databricks",
                     "spark", "kafka", "airflow", "dbt",
                     "docker", "kubernetes"],
    "Soft Skills":  ["communication", "agile", "scrum",
                     "project management", "stakeholder",
                     "leadership", "presentation", "teamwork"],
}

ALL_SKILLS = [s for group in SKILL_KEYWORDS.values() for s in group]

SENIORITY_PATTERNS = {
    "Junior / Graduate": ["junior", "graduate", "entry", "trainee",
                          "intern", "apprentice", "fresher"],
    "Mid-Level":         ["mid", "medior", "analyst", "specialist",
                          "associate", "consultant"],
    "Senior":            ["senior", "lead", "principal", "staff",
                          "expert", "chapter lead"],
    "Manager / Director":["manager", "director", "head of",
                          "vice president", "vp", "cto", "cdo",
                          "chief"],
}


# ============================================================
# PART 1: DATA FETCHING
# ============================================================

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_jobs(keyword, country_code, location="", pages=3):
    all_jobs = []
    for page in range(1, pages + 1):
        url = ("https://api.adzuna.com/v1/api/jobs/"
               + country_code + "/search/" + str(page))
        params = {
            "app_id":           ADZUNA_APP_ID,
            "app_key":          ADZUNA_APP_KEY,
            "results_per_page": 20,
            "what":             keyword,
            "content-type":     "application/json",
        }
        if location:
            params["where"] = location
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data    = resp.json()
                results = data.get("results", [])
                all_jobs.extend(results)
                if len(results) < 20:
                    break
            else:
                break
        except Exception:
            break
    return all_jobs


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_salary_histogram(keyword, country_code):
    url = ("https://api.adzuna.com/v1/api/jobs/"
           + country_code + "/histogram")
    params = {
        "app_id":       ADZUNA_APP_ID,
        "app_key":      ADZUNA_APP_KEY,
        "what":         keyword,
        "content-type": "application/json",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data    = resp.json()
            buckets = data.get("histogram", {})
            df = pd.DataFrame(list(buckets.items()),
                              columns=["Salary Bucket", "Job Count"])
            df["Salary Bucket"] = pd.to_numeric(
                df["Salary Bucket"], errors="coerce")
            return df.dropna().sort_values("Salary Bucket")
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_top_companies(keyword, country_code):
    url = ("https://api.adzuna.com/v1/api/jobs/"
           + country_code + "/top_companies")
    params = {
        "app_id":       ADZUNA_APP_ID,
        "app_key":      ADZUNA_APP_KEY,
        "what":         keyword,
        "content-type": "application/json",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data        = resp.json()
            leaderboard = data.get("leaderboard", [])
            df = pd.DataFrame(leaderboard)
            if not df.empty and "canonical_name" in df.columns:
                df = df.rename(columns={
                    "canonical_name": "Company",
                    "count":          "Job Postings"
                })
                return df[["Company", "Job Postings"]].head(15)
    except Exception:
        pass
    return pd.DataFrame()


# ============================================================
# PART 2: PROCESSING
# ============================================================

def parse_jobs(raw_jobs, currency):
    records = []
    for job in raw_jobs:
        raw_desc   = job.get("description", "")
        clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text()

        sal_min = job.get("salary_min")
        sal_max = job.get("salary_max")
        sal_avg = (sal_min + sal_max) / 2 if sal_min and sal_max else None

        loc = job.get("location", {})
        location_str = (loc.get("display_name", "Unknown")
                        if isinstance(loc, dict) else str(loc))

        created  = job.get("created", "")
        days_ago = None
        try:
            posted_dt = datetime.strptime(created[:10], "%Y-%m-%d")
            days_ago  = (datetime.now() - posted_dt).days
        except Exception:
            pass

        title_lower = job.get("title", "").lower()
        seniority   = "Mid-Level"
        for level, kws in SENIORITY_PATTERNS.items():
            if any(kw in title_lower for kw in kws):
                seniority = level
                break

        records.append({
            "title":       job.get("title", "Unknown"),
            "company":     job.get("company", {}).get("display_name", "Unknown"),
            "location":    location_str,
            "sal_min":     sal_min,
            "sal_max":     sal_max,
            "sal_avg":     sal_avg,
            "currency":    currency,
            "seniority":   seniority,
            "description": clean_desc,
            "days_ago":    days_ago,
            "url":         job.get("redirect_url", "#"),
        })
    return pd.DataFrame(records)


def extract_skills(df):
    skill_counts = Counter()
    total_jobs   = len(df)
    for desc in df["description"].fillna(""):
        desc_lower = desc.lower()
        for skill in ALL_SKILLS:
            if re.search(r"\b" + re.escape(skill) + r"\b", desc_lower):
                skill_counts[skill] += 1
    if not skill_counts:
        return pd.DataFrame()
    skill_df = pd.DataFrame(skill_counts.most_common(25),
                            columns=["Skill", "Mentions"])
    skill_df["% of Jobs"] = (
        skill_df["Mentions"] / total_jobs * 100).round(1)
    cat_map = {s: c for c, skills in SKILL_KEYWORDS.items() for s in skills}
    skill_df["Category"] = skill_df["Skill"].map(cat_map).fillna("Other")
    return skill_df


def extract_locations(df):
    if "location" not in df.columns:
        return pd.DataFrame()
    counts = df["location"].value_counts().reset_index()
    counts.columns = ["Location", "Job Count"]
    return counts.head(15)


def salary_insights(df, currency):
    sal_df = df.dropna(subset=["sal_avg"])
    if sal_df.empty:
        return None
    return {
        "median":   round(sal_df["sal_avg"].median()),
        "mean":     round(sal_df["sal_avg"].mean()),
        "min":      round(sal_df["sal_avg"].min()),
        "max":      round(sal_df["sal_avg"].max()),
        "currency": currency,
        "count":    len(sal_df),
    }


# ============================================================
# PART 3: CHARTS
# ============================================================

def chart_skills(skill_df):
    fig = px.bar(
        skill_df.head(20), x="% of Jobs", y="Skill",
        orientation="h", color="Category",
        template="plotly_dark",
        title="Top 20 In-Demand Skills (% of job postings)",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_layout(
        height=520,
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def chart_skill_gap(skill_df, my_skills):
    top20    = skill_df.head(20).copy()
    my_lower = [s.lower() for s in my_skills]
    top20["Have"] = top20["Skill"].apply(
        lambda s: "Yes" if s.lower() in my_lower else "No")
    top20 = top20.sort_values("% of Jobs", ascending=True)
    colors = ["#00C851" if x == "Yes" else "#FF4444"
              for x in top20["Have"]]
    fig = go.Figure(go.Bar(
        x=top20["% of Jobs"], y=top20["Skill"],
        orientation="h", marker_color=colors,
        text=top20["Have"], textposition="outside",
    ))
    fig.update_layout(
        title="Skill Gap  |  Green = You Have It  |  Red = You Need It",
        template="plotly_dark", height=520,
        xaxis_title="Appears in % of job postings",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def chart_seniority(df):
    counts = df["seniority"].value_counts().reset_index()
    counts.columns = ["Seniority", "Count"]
    order  = ["Junior / Graduate", "Mid-Level",
               "Senior", "Manager / Director"]
    counts["Seniority"] = pd.Categorical(
        counts["Seniority"], categories=order, ordered=True)
    counts = counts.sort_values("Seniority")
    fig = px.pie(
        counts, names="Seniority", values="Count",
        template="plotly_dark",
        title="Job Openings by Seniority Level",
        color_discrete_sequence=["#00C851","#FFD700",
                                  "#FF8C00","#FF4444"],
        hole=0.45,
    )
    fig.update_traces(textposition="outside",
                      textinfo="percent+label")
    fig.update_layout(height=380,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_salary_histogram(hist_df, currency):
    fig = px.bar(
        hist_df, x="Salary Bucket", y="Job Count",
        template="plotly_dark",
        title="Salary Distribution  |  " + currency + " per year",
        labels={"Salary Bucket": "Annual Salary (" + currency + ")"},
        color="Job Count",
        color_continuous_scale=["#003300","#00C851"],
    )
    fig.update_layout(height=340, showlegend=False,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_salary_by_seniority(df, currency):
    sal_df = df.dropna(subset=["sal_avg"])
    if sal_df.empty:
        return None
    order  = ["Junior / Graduate", "Mid-Level",
               "Senior", "Manager / Director"]
    sal_df = sal_df[sal_df["seniority"].isin(order)]
    fig = px.box(
        sal_df, x="seniority", y="sal_avg",
        category_orders={"seniority": order},
        template="plotly_dark",
        title="Salary Range by Seniority  |  " + currency,
        labels={"seniority": "Seniority", "sal_avg": "Salary"},
        color="seniority",
        color_discrete_sequence=["#00C851","#FFD700",
                                  "#FF8C00","#FF4444"],
    )
    fig.update_layout(height=380, showlegend=False,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_top_companies(comp_df):
    fig = px.bar(
        comp_df.sort_values("Job Postings", ascending=True),
        x="Job Postings", y="Company", orientation="h",
        template="plotly_dark", title="Top Hiring Companies",
        color="Job Postings",
        color_continuous_scale=["#1a1f2e","#4a90d9"],
    )
    fig.update_layout(height=420, showlegend=False,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_locations(loc_df):
    fig = px.bar(
        loc_df.sort_values("Job Count", ascending=True),
        x="Job Count", y="Location", orientation="h",
        template="plotly_dark",
        title="Job Density by City / Region",
        color="Job Count",
        color_continuous_scale=["#1a1f2e","#FF8C00"],
    )
    fig.update_layout(height=420, showlegend=False,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_posting_trend(df):
    trend_df = df.dropna(subset=["days_ago"]).copy()
    trend_df["days_ago"] = trend_df["days_ago"].astype(int)
    trend_df = trend_df[trend_df["days_ago"] <= 30]
    if trend_df.empty:
        return None
    daily = (trend_df.groupby("days_ago").size()
             .reset_index(name="Jobs Posted")
             .sort_values("days_ago"))
    fig = px.area(
        daily, x="days_ago", y="Jobs Posted",
        template="plotly_dark",
        title="Job Posting Volume  |  Last 30 Days",
        labels={"days_ago": "Days Ago"},
        color_discrete_sequence=["#4a90d9"],
    )
    fig.update_layout(height=300,
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


# ============================================================
# PART 4: DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Global Employment Market Analyzer",
    page_icon="🌍", layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 12px;
    }
    .job-card {
        background: #1a1f2e;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 4px solid #4a90d9;
    }
    .region-header {
        color: #4a90d9;
        font-weight: 700;
        font-size: 0.85em;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

st.title("Global Employment Market Analyzer")
st.caption("Live job data via Adzuna API  |  27 countries across 4 regions  |  Real-time skill intelligence")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Search Parameters")

    target_job = st.selectbox("Job Role / Sector", [
        "Data Analyst", "Data Scientist", "Data Engineer",
        "Machine Learning Engineer", "Business Analyst",
        "Software Engineer", "Python Developer",
        "AI Specialist", "BI Developer", "Cloud Engineer",
        "Full Stack Developer", "DevOps Engineer",
        "Product Manager", "Project Manager",
        "Cybersecurity Analyst", "Network Engineer",
        "UX Designer", "Digital Marketing",
        "Finance Analyst", "HR Manager",
    ])

    # Region selector first
    st.markdown("**Region**")
    selected_region = st.selectbox(
        "Region",
        list(COUNTRIES_BY_REGION.keys()),
        label_visibility="collapsed"
    )

    # Then country within that region
    region_countries = COUNTRIES_BY_REGION[selected_region]
    st.markdown("**Country**")
    selected_country_name = st.selectbox(
        "Country",
        list(region_countries.keys()),
        label_visibility="collapsed"
    )

    country_code = region_countries[selected_country_name]
    currency     = CURRENCY_MAP.get(country_code, "USD")
    flag         = FLAG_MAP.get(country_code, "")

    st.markdown(
        '<div style="background:#1a1f2e;border-radius:6px;'
        'padding:8px 12px;margin:4px 0;">'
        '<span style="color:#AAAAAA;font-size:0.85em">Selected: </span>'
        '<b style="color:#EEEEEE">' + flag + '  ' + selected_country_name + '</b>'
        '<br><span style="color:#AAAAAA;font-size:0.85em">Currency: </span>'
        '<b style="color:#4a90d9">' + currency + '</b>'
        '</div>',
        unsafe_allow_html=True
    )

    target_city = st.text_input(
        "City (optional)",
        placeholder="e.g. Berlin, Mumbai, New York"
    )

    st.markdown("---")

    # Multi-country comparison
    st.subheader("Compare Countries")
    st.caption("Select up to 4 countries to compare job counts")
    compare_countries = st.multiselect(
        "Compare with:",
        options=[c for c in ALL_COUNTRIES.keys()
                 if c != selected_country_name],
        max_selections=3,
        default=[],
    )

    st.markdown("---")
    st.subheader("Your Skills")
    my_skills = st.multiselect(
        "Skills you have (for gap analysis):",
        options=ALL_SKILLS,
        default=["python", "sql", "excel"],
    )

    st.markdown("---")
    pages_to_fetch = st.slider("Pages to fetch (20 jobs/page)", 1, 5, 3)
    run_btn = st.button("Analyze Market", use_container_width=True,
                        type="primary")


# ============================================================
# MAIN ANALYSIS
# ============================================================

if run_btn:
    location_str = target_city.strip() if target_city.strip() else ""

    st.markdown("---")
    st.subheader(
        flag + "  " + target_job + "  |  " + selected_country_name
        + "  |  " + selected_region
    )

    progress = st.progress(0, text="Fetching job listings...")

    with st.spinner("Contacting Adzuna API..."):
        raw_jobs = fetch_jobs(target_job, country_code,
                              location=location_str,
                              pages=pages_to_fetch)
    progress.progress(40, text="Processing job data...")

    if not raw_jobs:
        st.error(
            "No jobs returned for " + selected_country_name
            + ". Adzuna may have limited data for this country/role combo. "
            "Try United Kingdom, United States, Germany, or Australia "
            "for best results."
        )
        st.stop()

    df       = parse_jobs(raw_jobs, currency)
    skill_df = extract_skills(df)
    loc_df   = extract_locations(df)
    sal_info = salary_insights(df, currency)

    progress.progress(70, text="Fetching salary and company data...")
    hist_df = fetch_salary_histogram(target_job, country_code)
    comp_df = fetch_top_companies(target_job, country_code)
    progress.progress(100, text="Building dashboard...")
    progress.empty()

    # ── KPI ROW ───────────────────────────────────────────────
    st.markdown("### Market Snapshot  |  " + selected_country_name)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Jobs Found",  len(df))
    k2.metric("With Salary Data",  len(df.dropna(subset=["sal_avg"])))
    if sal_info:
        k3.metric("Median Salary",
                  currency + " " + "{:,.0f}".format(sal_info["median"]))
        k4.metric("Top Salary",
                  currency + " " + "{:,.0f}".format(sal_info["max"]))
    else:
        k3.metric("Median Salary", "No data")
        k4.metric("Top Salary",    "No data")
    senior_count = len(df[df["seniority"] == "Senior"])
    k5.metric("Senior Roles",
              str(senior_count) + " ("
              + str(round(senior_count / len(df) * 100)) + "%)")

    # ── COUNTRY COMPARISON ────────────────────────────────────
    if compare_countries:
        st.markdown("---")
        st.markdown("### Country Comparison  |  Job Market Size")
        st.caption("Comparing job availability for: " + target_job)

        compare_data = [{
            "Country": flag + " " + selected_country_name,
            "Jobs":    len(df),
            "Currency": currency,
        }]

        with st.spinner("Fetching comparison data..."):
            for comp_name in compare_countries:
                comp_code = ALL_COUNTRIES.get(comp_name, "")
                comp_flag = FLAG_MAP.get(comp_code, "")
                if comp_code:
                    comp_jobs = fetch_jobs(target_job, comp_code, pages=1)
                    compare_data.append({
                        "Country":  comp_flag + " " + comp_name,
                        "Jobs":     len(comp_jobs),
                        "Currency": CURRENCY_MAP.get(comp_code, ""),
                    })

        comp_df_chart = pd.DataFrame(compare_data).sort_values(
            "Jobs", ascending=True)
        fig_comp = px.bar(
            comp_df_chart, x="Jobs", y="Country",
            orientation="h", template="plotly_dark",
            title="Job Market Size Comparison  |  " + target_job,
            color="Jobs",
            color_continuous_scale=["#1a1f2e","#4a90d9"],
            text="Jobs",
        )
        fig_comp.update_traces(textposition="outside")
        fig_comp.update_layout(height=300, showlegend=False,
                               margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_comp, use_container_width=True)

        st.caption(
            "Note: Comparison shows first-page results only (20 jobs). "
            "Countries with fewer than 5 results may have limited Adzuna coverage."
        )

    # ── SKILLS ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Skills Intelligence")

    if not skill_df.empty:
        tab1, tab2 = st.tabs(["Market Skill Demand", "Your Skill Gap"])

        with tab1:
            st.plotly_chart(chart_skills(skill_df),
                            use_container_width=True)
            st.markdown("#### Top 5 Must-Have Skills in "
                        + selected_country_name)
            cols = st.columns(5)
            for col, (_, row) in zip(cols, skill_df.head(5).iterrows()):
                col.metric(
                    label=row["Skill"].title(),
                    value=str(row["% of Jobs"]) + "% of jobs",
                    delta=row["Category"], delta_color="off"
                )

        with tab2:
            if my_skills:
                st.plotly_chart(chart_skill_gap(skill_df, my_skills),
                                use_container_width=True)
                gap_skills = skill_df[
                    ~skill_df["Skill"].isin(
                        [s.lower() for s in my_skills])
                ].head(5)
                if not gap_skills.empty:
                    st.markdown("#### Priority Skills to Learn for "
                                + selected_country_name)
                    gcols = st.columns(len(gap_skills))
                    for col, (_, row) in zip(gcols,
                                             gap_skills.iterrows()):
                        col.metric(
                            label=row["Skill"].title(),
                            value=str(row["% of Jobs"]) + "% demand",
                            delta="Missing from your profile",
                            delta_color="inverse"
                        )
            else:
                st.info("Select your skills in the sidebar.")
    else:
        st.info("No skill data extracted. Try fetching more pages.")

    # ── SALARY ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Salary Intelligence  |  " + currency)

    sl, sr = st.columns(2)
    with sl:
        if not hist_df.empty:
            st.plotly_chart(chart_salary_histogram(hist_df, currency),
                            use_container_width=True)
        elif sal_info:
            st.markdown(
                '<div style="background:#1a1f2e;border-radius:8px;'
                'padding:20px">'
                '<b style="color:#EEEEEE">Salary Summary  |  '
                + currency + '</b><br><br>'
                '<span style="color:#AAAAAA">Median: </span>'
                '<b style="color:#00C851">'
                + "{:,.0f}".format(sal_info["median"]) + '</b><br>'
                '<span style="color:#AAAAAA">Average: </span>'
                '<b style="color:#FFD700">'
                + "{:,.0f}".format(sal_info["mean"]) + '</b><br>'
                '<span style="color:#AAAAAA">Range: </span>'
                '<b style="color:#EEEEEE">'
                + "{:,.0f}".format(sal_info["min"])
                + " - "
                + "{:,.0f}".format(sal_info["max"]) + '</b>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Salary data not available for this search.")

    with sr:
        fig_sal = chart_salary_by_seniority(df, currency)
        if fig_sal:
            st.plotly_chart(fig_sal, use_container_width=True)
        else:
            st.info("Not enough salary data by seniority.")

    # ── SENIORITY + TREND ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### Market Demand Patterns")

    dl, dr = st.columns(2)
    with dl:
        st.plotly_chart(chart_seniority(df), use_container_width=True)
    with dr:
        trend_fig = chart_posting_trend(df)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Not enough date data for posting trend.")

    # ── COMPANIES + LOCATIONS ─────────────────────────────────
    st.markdown("---")
    st.markdown("### Where to Apply  |  " + selected_country_name)

    cl, cr = st.columns(2)
    with cl:
        display_comp = comp_df if not comp_df.empty else (
            df["company"].value_counts().reset_index()
            .rename(columns={"company":"Company",
                             "count":"Job Postings"}).head(15)
        )
        if not display_comp.empty:
            st.plotly_chart(chart_top_companies(display_comp),
                            use_container_width=True)
    with cr:
        if not loc_df.empty:
            st.plotly_chart(chart_locations(loc_df),
                            use_container_width=True)

    # ── JOB LISTINGS ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Live Job Listings  |  " + flag
                + " " + selected_country_name)

    cf = st.columns([2, 2, 2, 1])
    f_seniority = cf[0].multiselect(
        "Seniority:", df["seniority"].unique().tolist(),
        default=df["seniority"].unique().tolist())
    f_location  = cf[1].text_input("Filter location:", "")
    f_salary    = cf[2].checkbox("Only jobs with salary data", False)
    f_days      = cf[3].number_input("Posted within (days):", 1, 60, 30)

    filtered = df[df["seniority"].isin(f_seniority)].copy()
    if f_location:
        filtered = filtered[filtered["location"]
                            .str.contains(f_location, case=False, na=False)]
    if f_salary:
        filtered = filtered.dropna(subset=["sal_avg"])
    if "days_ago" in filtered.columns:
        filtered = filtered[
            filtered["days_ago"].isna()
            | (filtered["days_ago"] <= f_days)]

    st.caption("Showing " + str(len(filtered))
               + " of " + str(len(df)) + " jobs")

    for _, job in filtered.head(20).iterrows():
        salary_str = (
            currency + " " + "{:,.0f}".format(job["sal_min"])
            + " - " + "{:,.0f}".format(job["sal_max"])
            if pd.notna(job.get("sal_min"))
            and pd.notna(job.get("sal_max"))
            else "Salary not disclosed"
        )
        days_str = (str(int(job["days_ago"])) + "d ago"
                    if pd.notna(job.get("days_ago")) else "Date unknown")

        st.markdown(
            '<div class="job-card">'
            '<b style="color:#EEEEEE;font-size:1.05em">'
            + str(job["title"]) + '</b>'
            '&nbsp;&nbsp;<span style="color:#888888;font-size:0.85em">'
            + days_str + '</span><br>'
            '<span style="color:#4a90d9">' + str(job["company"])
            + '</span>&nbsp;|&nbsp;'
            '<span style="color:#AAAAAA">' + str(job["location"])
            + '</span>&nbsp;|&nbsp;'
            '<span style="color:#00C851">' + salary_str
            + '</span>&nbsp;|&nbsp;'
            '<span style="color:#FFD700">' + str(job["seniority"])
            + '</span>'
            '</div>',
            unsafe_allow_html=True
        )

    # ── EXPORT ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Export Data")
    ex1, ex2 = st.columns(2)
    with ex1:
        csv_jobs = (df.drop(columns=["description"], errors="ignore")
                    .to_csv(index=False).encode("utf-8"))
        st.download_button(
            "Download Job Listings CSV", data=csv_jobs,
            file_name=selected_country_name.replace(" ","_")
                      + "_jobs.csv",
            mime="text/csv"
        )
    with ex2:
        if not skill_df.empty:
            csv_skills = skill_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Skills Analysis CSV", data=csv_skills,
                file_name=selected_country_name.replace(" ","_")
                          + "_skills.csv",
                mime="text/csv"
            )

    # ── MARKET CONTEXT TIP BOX ────────────────────────────────
    st.markdown("---")
    st.markdown("### Market Intelligence Tips  |  "
                + flag + " " + selected_country_name)
    st.markdown(
        '<div style="background:#1a1f2e;border-radius:10px;padding:20px">'
        '<b style="color:#4a90d9;font-size:1.05em">'
        'How to stand out in ' + selected_country_name + '</b><br><br>'
        '<span style="color:#CCCCCC">'
        '1. <b style="color:#EEEEEE">Fix your skill gaps first</b>  |  '
        'The red bars in your Skill Gap chart are the exact skills '
        'you are missing for this market. Each one you add raises '
        'your match rate significantly.<br><br>'
        '2. <b style="color:#EEEEEE">Target the top hiring companies</b>  |  '
        'Companies with 5 or more active postings are scaling rapidly. '
        'Apply directly on their careers page in addition to Adzuna.<br><br>'
        '3. <b style="color:#EEEEEE">Apply within 7 days of posting</b>  |  '
        'Most recruiters shortlist in the first week. '
        'Use the "Posted within 7 days" filter for the best response rate.<br><br>'
        '4. <b style="color:#EEEEEE">Anchor your salary negotiation</b>  |  '
        'Use the median salary figure as your minimum baseline. '
        'Senior roles typically command 25 to 40 percent above median.<br><br>'
        '5. <b style="color:#EEEEEE">Use the Country Comparison tool</b>  |  '
        'If your primary market has few listings, '
        'the comparison chart shows you which nearby countries '
        'have more demand for the same role right now.'
        '</span></div>',
        unsafe_allow_html=True
    )

else:
    # Landing screen
    st.markdown("---")

    # Show all supported countries as a visual grid
    st.markdown("### Supported Countries  |  27 nations across 4 regions")
    for region, countries in COUNTRIES_BY_REGION.items():
        st.markdown("**" + region + "**")
        cols = st.columns(6)
        for i, (name, code) in enumerate(countries.items()):
            flag = FLAG_MAP.get(code, "")
            cols[i % 6].markdown(
                '<div style="background:#1a1f2e;border-radius:6px;'
                'padding:6px 10px;margin:3px 0;text-align:center;'
                'font-size:0.85em;">'
                + flag + ' ' + name + '<br>'
                '<span style="color:#4a90d9;font-size:0.8em">'
                + CURRENCY_MAP.get(code,"") + '</span>'
                '</div>',
                unsafe_allow_html=True
            )
        st.markdown("")

    st.markdown("---")
    st.markdown(
        '<div style="background:#1a1f2e;border-radius:12px;'
        'padding:24px;text-align:center;">'
        '<b style="color:#EEEEEE;font-size:1.2em">'
        'Select a role and country in the sidebar, '
        'then click Analyze Market</b><br><br>'
        '<span style="color:#4a90d9">'
        'Live job listings  |  Salary intelligence  |  '
        'Skill gap analysis<br>'
        'Top hiring companies  |  Location density  |  '
        'Country comparison  |  Export to CSV'
        '</span></div>',
        unsafe_allow_html=True
    )