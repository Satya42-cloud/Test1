import streamlit as st
import pandas as pd
import yagmail
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Load internal dataset
@st.cache_data
def load_data():
    return pd.read_csv("https://raw.githubusercontent.com/Satya42-cloud/Test1/refs/heads/main/Shortlisted%20Vendor.csv")

df = load_data()

# Authentication
def login():
    st.title("Procurement Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "password":
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_vendors" not in st.session_state:
    st.session_state.selected_vendors = {}
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# Generate PDF contract
def generate_pdf(vendor_name, route_id):
    file_name = f"contract_{vendor_name}_{route_id}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    text = f"""
    Contract Award Notice

    Dear {vendor_name},

    Congratulations! You have been selected as the preferred vendor for Route {route_id}.
    Please find the contract terms enclosed.

    Regards,
    Procurement Team
    """
    for i, line in enumerate(text.strip().split("\n")):
        c.drawString(100, 800 - i*20, line.strip())
    c.save()
    return file_name

# Send email with attachment
def send_email(recipient_email, vendor_name, route_id, pdf_file):
    try:
        yag = yagmail.SMTP("your_email@gmail.com", "your_app_password")  # Use app password if Gmail
        subject = f"Contract Award for Route {route_id}"
        body = f"Dear {vendor_name},\n\nCongratulations! You have been selected for Route {route_id}.\nPlease find the contract attached.\n\nRegards,\nProcurement Team"
        yag.send(to=recipient_email, subject=subject, contents=body, attachments=pdf_file)
    except Exception as e:
        st.error(f"Error sending email to {recipient_email}: {e}")

# Main app
if not st.session_state.logged_in:
    login()
else:
    st.title("Procurement Manager Dashboard")

    if st.button("📊 View Report"):
        st.session_state.show_report = True

    if st.session_state.show_report:
        route_options = sorted(df["Route ID"].unique().tolist())
        selected_routes = st.multiselect("Select Route(s):", route_options)

        if selected_routes:
            filtered_df = df[df["Route ID"].isin(selected_routes)]

            for route_id in selected_routes:
                st.subheader(f"Route {route_id}")
                route_df = filtered_df[filtered_df["Route ID"] == route_id]

                for idx, row in route_df.iterrows():
                    cols = st.columns([3, 3, 2, 2, 2])
                    cols[0].markdown(f"**{row['Vendor Name']}**")
                    cols[1].markdown(f"Quoted Cost: ₹{row['Total Quoted Cost']}")
                    cols[2].markdown(f"Rank: {row['Rank']}")

                    selected = st.session_state.selected_vendors.get(route_id)
                    if selected == row["Vendor ID"]:
                        cols[3].button("Selected ✅", key=f"sel_{route_id}_{idx}", disabled=True)
                    elif selected is not None:
                        cols[3].button("Rejected ❌", key=f"rej_{route_id}_{idx}", disabled=True)
                    else:
                        if cols[3].button("Select", key=f"btn_{route_id}_{idx}"):
                            st.session_state.selected_vendors[route_id] = row["Vendor ID"]
                            st.experimental_rerun()

            if all(route in st.session_state.selected_vendors for route in selected_routes):
                st.success("✅ All routes have selected vendors.")

                with st.expander("📄 Preview Contracts"):
                    for route_id in selected_routes:
                        vendor_id = st.session_state.selected_vendors[route_id]
                        vendor_row = df[(df["Route ID"] == route_id) & (df["Vendor ID"] == vendor_id)].iloc[0]
                        st.markdown(f"""
                        **To:** {vendor_row['Vendor Name']}
                        **Email:** {vendor_row['Vendor Email']}
                        **Subject:** Contract Award for Route {route_id}

                        Dear {vendor_row['Vendor Name']},
                        Congratulations! You have been selected as the preferred vendor for **Route {route_id}**.
                        Please review and acknowledge the attached contract terms.

                        Regards,
                        Procurement Team
                        """)

                if st.button("📨 Send Contracts"):
                    for route_id in selected_routes:
                        vendor_id = st.session_state.selected_vendors[route_id]
                        vendor_row = df[(df["Route ID"] == route_id) & (df["Vendor ID"] == vendor_id)].iloc[0]
                        pdf_path = generate_pdf(vendor_row['Vendor Name'], route_id)
                        send_email(vendor_row["Vendor Email"], vendor_row["Vendor Name"], route_id, pdf_path)
                        os.remove(pdf_path)  # Clean up after sending

                    st.success("📬 All contracts sent successfully!")
