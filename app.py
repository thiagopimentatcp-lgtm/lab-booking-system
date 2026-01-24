import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import urllib.parse

st.set_page_config(page_title="Lab Equipment Booking", page_icon="🔬")

st.title("🔬 LaSense Booking System")
st.write("Please check the schedule below before booking to avoid conflicts.")

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# List of Team Emails
TEAM_EMAILS = "t.coimbrapimenta@latrobe.edu.au, H.Bellette@latrobe.edu.au, V.Pithaih@latrobe.edu.au, 21447366@students.latrobe.edu.au, A.Renata@latrobe.edu.au, R.Rath@latrobe.edu.au, 21443977@students.latrobe.edu.au, 22110321@students.latrobe.edu.au, 21975616@students.latrobe.edu.au, H.Mourao@latrobe.edu.au"

# --- Booking Form ---
with st.sidebar:
    st.header("New Booking")
    with st.form("booking_form", clear_on_submit=True):
        user_name = st.text_input("User Name")
        equipment = st.selectbox("Potentiostat", 
                                 ["PalmSens", "DropSens"])
        booking_date = st.date_input("Date", min_value=datetime.today())
        
        col1, col2 = st.columns(2)
        start_t = col1.time_input("Start Time", value=time(9, 0))
        end_t = col2.time_input("End Time", value=time(10, 0))
        
        submit_button = st.form_submit_button("Book Equipment")

if submit_button:
    if user_name:
        try:
            df = conn.read()
            df['Date'] = df['Date'].astype(str)
            
            # Conflict Logic: Check if equipment is busy on same day/time
            conflicts = df[
                (df["Equipment"] == equipment) & 
                (df["Date"] == str(booking_date))
            ]
            
            is_conflict = False
            for _, row in conflicts.iterrows():
                if (str(start_t) < row["End Time"]) and (str(end_t) > row["Start Time"]):
                    is_conflict = True
                    existing_user = row["User"]
                    break
            
            if is_conflict:
                st.error(f"❌ Conflict! This slot is already booked by **{existing_user}**. Please choose another time.")
            else:
                # Save New Booking
                new_booking = pd.DataFrame([{
                    "Equipment": equipment,
                    "Date": str(booking_date),
                    "Start Time": str(start_t),
                    "End Time": str(end_t),
                    "User": user_name
                }])
                
                updated_df = pd.concat([df, new_booking], ignore_index=True)
                conn.update(data=updated_df)
                
                st.success(f"✅ Success! {equipment} has been booked for {user_name}.")
                st.balloons()

                # --- Notification Link Generation ---
                subject = urllib.parse.quote(f"Lab Booking: {equipment} by {user_name}")
                body = urllib.parse.quote(
                    f"Hi team,\n\nI have just booked the {equipment} for {booking_date} "
                    f"from {start_t} to {end_t}.\n\nBest regards,\n{user_name}"
                )
                mailto_link = f"mailto:{TEAM_EMAILS}?subject={subject}&body={body}"
                
                st.markdown(f"""
                    <a href="{mailto_link}" target="_blank">
                        <button style="
                            background-color: #007bff; 
                            color: white; 
                            padding: 10px 20px; 
                            border: none; 
                            border-radius: 5px; 
                            cursor: pointer;">
                            📧 Click here to notify the team via Email
                        </button>
                    </a>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error: {e}. Please check your Google Sheets connection.")
    else:
        st.warning("Please enter your name.")

# --- Display Schedule ---
st.subheader("📅 Current Schedule")
try:
    df_view = conn.read()
    if not df_view.empty:
        df_view = df_view.sort_values(by="Date", ascending=False)
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("The schedule is currently empty.")
except:
    st.info("Ready to start! Make the first booking.")