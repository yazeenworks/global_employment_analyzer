# Global Employment Market Analyzer

A live job market intelligence dashboard covering 27 countries
across 4 regions, powered by the Adzuna API. Built to help
job seekers make data-driven decisions about where and how to apply.

## Features
- Live job listings from 27 countries across Europe, Americas,
  Asia Pacific and Middle East & Africa
- Real-time skill demand analysis from job descriptions
- Skill gap analysis — compares market demand vs your skills
- Salary intelligence with histogram and seniority breakdown
- Top hiring companies per country and role
- Country comparison tool — compare job market size across 4 nations
- Job density map by city and region
- Posting trend chart — last 30 days of hiring activity
- Filter by seniority, location, salary and posting date
- Export job listings and skills data as CSV

## Tech Stack
Python, Streamlit, Adzuna API, Plotly,
Pandas, BeautifulSoup, Requests

## Supported Countries
Europe: UK, Germany, France, Netherlands, Austria,
        Belgium, Switzerland, Poland, Spain, Italy, Russia

Americas: USA, Canada, Brazil, Mexico, Argentina

Asia Pacific: India, Australia, New Zealand, Singapore,
              Japan, China, South Korea, Indonesia

Middle East & Africa: South Africa, Nigeria, Kenya

## Run Locally
pip install -r requirements.txt
streamlit run employment_analyzer.py
