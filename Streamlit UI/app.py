import streamlit as st
import pandas as pd
import yagmail
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---- Load the dataset from GitHub URL ----
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Satya42-cloud/Test1/refs/heads/main/Shortlisted%20Vendor.csv"
    return pd.read_csv(url)

df = load_data()

# ---- Authentication ----
def login():
    st.title("Procurement Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "password":
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

# ---- Session state initialization ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_vendors" not in st.session_state:
    st.session_state.selected_vendors = {}
if "show_report" not in st.session_state:
    st.session_state.show_report = False
if "draft_selections" not in st.session_state:
    st.session_state.draft_selections = {}

# ---- Generate PDF contract ----
def generate_pdf(vendor_name, routes):
    file_name = f"contract_{vendor_name}.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    text = f"""
    Contract Award Notice

    Dear {vendor_name},

    Congratulations! You have been selected as the preferred vendor for the following routes:
    {', '.join(routes)}

    Please find the contract terms enclosed.

    Regards,
    Procurement Team
    """
    for i, line in enumerate(text.strip().split("\n")):
        c.drawString(100, 800 - i*20, line.strip())
    c.save()
    return file_name

# ---- Send email with attachment ----
def send_email(recipient_email, vendor_name, routes, pdf_file):
    try:
        yag = yagmail.SMTP("harikaankathi7@gmail.com", "vpkczaiwjrmgdmvv")  # Use your Gmail credentials
        subject = f"Contract Award for Routes {', '.join(routes)}"
        body = f"Dear {vendor_name},\n\nCongratulations! You have been selected for the following routes: {', '.join(routes)}.\nPlease find the contract attached.\n\nRegards,\nProcurement Team"
        yag.send(to=recipient_email, subject=subject, contents=body, attachments=pdf_file)
    except Exception as e:
        st.error(f"Error sending email to {recipient_email}: {e}")

# ---- Main app flow ----
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

                    # Draft Mode: Check if this vendor is in draft
                    if route_id in st.session_state.draft_selections and st.session_state.draft_selections[route_id] == row["Vendor ID"]:
                        cols[3].button("Selected ✅", key=f"draft_{route_id}_{idx}", disabled=False)
                    else:
                        if cols[3].button("Select", key=f"btn_{route_id}_{idx}"):
                            st.session_state.draft_selections[route_id] = row["Vendor ID"]

            # Check if all routes have vendor selections
            if all(route in st.session_state.draft_selections for route in selected_routes):
                st.success("✅ All routes have selected vendors.")
                st.session_state.selected_vendors = st.session_state.draft_selections.copy()

                with st.expander("📄 Preview Contracts"):
                    vendors_to_send = {}
                    for route_id in selected_routes:
                        vendor_id = st.session_state.selected_vendors[route_id]
                        vendor_row = df[(df["Route ID"] == route_id) & (df["Vendor ID"] == vendor_id)].iloc[0]
                        
                        # Group routes by vendor
                        if vendor_id not in vendors_to_send:
                            vendors_to_send[vendor_id] = {"vendor_name": vendor_row["Vendor Name"], "email": vendor_row["Vendor Email"], "routes": []}
                        vendors_to_send[vendor_id]["routes"].append(route_id)

                    # Show the grouped contracts for each vendor
                    for vendor_id, vendor_info in vendors_to_send.items():
                        vendor_name = vendor_info["vendor_name"]
                        email = vendor_info["email"]
                        routes = vendor_info["routes"]

                        st.markdown(f"""
                        **To:** {vendor_name}  
                        **Email:** {email}  
                        **Subject:** Contract Award for Routes {', '.join(routes)}  

                        Dear {vendor_name},  
                        Congratulations! You have been selected as the preferred vendor for the following routes: {', '.join(routes)}.  
                        Please review and acknowledge the attached contract terms.

                        Regards,  
                        Procurement Team
                        """)

                if st.button("📨 Send Contracts"):
                    for vendor_id, vendor_info in vendors_to_send.items():
                        vendor_name = vendor_info["vendor_name"]
                        email = vendor_info["email"]
                        routes = vendor_info["routes"]

                        # Generate the PDF contract
                        pdf_path = generate_pdf(vendor_name, routes)

                        # Send the email with the PDF attachment
                        send_email(email, vendor_name, routes, pdf_path)
                        os.remove(pdf_path)  # Clean up after sending

                    st.success("📬 All contracts sent successfully!")
