# streamlit_app.py

import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# Configure your Gemini API key (use your own key here)
genai.configure(api_key="AIzaSyBg_0TJ_miX2UHYFjxNp9nH7EYGi9LiOJA")  # Replace with your actual Gemini API key

# Initialize the Gemini Pro model
model = genai.GenerativeModel("gemma-3-27b-it")

# Define agents
class IndustryResearcherAgent:
    def __init__(self, model):
        self.model = model

    def run(self, company_name):
        prompt = f"""
        You are an expert industry analyst. Conduct a detailed analysis of the {company_name} industry,
        focusing on current market trends, competitors, key offerings, and strategic opportunities.
        Include insights on high-growth areas, technological advancements, and unique positioning in the market.
        """
        response = self.model.generate_content(prompt)
        return response.text

class AIUseCaseStrategistAgent:
    def __init__(self, model):
        self.model = model

    def run(self, company_name):
        prompt = f"""
        As an AI strategy consultant, research current and emerging trends in AI and ML for the {company_name} industry.
        Suggest innovative and practical use cases for AI that can provide competitive advantages. Focus on use cases
        that improve efficiency, scalability, and ROI. Include examples of successful AI implementations in similar domains.
        """
        response = self.model.generate_content(prompt)
        return response.text

class ResourceCollectorAgent:
    def __init__(self, model):
        self.model = model

    def run(self, company_name):
        prompt = f"""
        As an AI resource specialist, identify and compile a curated list of relevant datasets, tools, and libraries
        for implementing AI solutions within the {company_name} industry. Ensure that resources are practical and
        scalable for real-world applications.
        """
        response = self.model.generate_content(prompt)
        return response.text

# PDF generator
def generate_pdf(company_name, insights, use_cases, resources):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 10, f"AI Insights for {company_name}\n\n")

    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 10, "📊 Industry Research")
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, insights + "\n")

    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 10, "🤖 AI Use Case Suggestions")
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, use_cases + "\n")

    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 10, "📚 AI Resources")
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, resources + "\n")

    file_path = f"{company_name}_AI_Report.pdf"
    pdf.output(file_path)
    return file_path

# Streamlit UI
st.set_page_config(page_title="AI Research Assistant", layout="centered")
st.title("🔍 AI Industry Insight Generator")

company_name = st.text_input("Enter a Company or Industry Name")

if st.button("Generate Insights") and company_name:
    with st.spinner("Running AI agents..."):
        industry_agent = IndustryResearcherAgent(model)
        use_case_agent = AIUseCaseStrategistAgent(model)
        resource_agent = ResourceCollectorAgent(model)

        industry_insights = industry_agent.run(company_name)
        use_cases = use_case_agent.run(company_name)
        resources = resource_agent.run(company_name)

        st.subheader("📊 Industry Insights")
        st.write(industry_insights)

        st.subheader("🤖 AI Use Case Ideas")
        st.write(use_cases)

        st.subheader("📚 Resources")
        st.write(resources)

        pdf_path = generate_pdf(company_name, industry_insights, use_cases, resources)

        with open(pdf_path, "rb") as file:
            st.download_button("📥 Download Report as PDF", file, file_name=pdf_path)
