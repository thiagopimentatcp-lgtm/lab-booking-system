import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import urllib.parse

st.set_page_config(page_title="Lab Equipment Booking", page_icon="🔬")

st.title("🔬 LaSense Booking System")
st.write("Manage research equipment for the SABE group.")

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Team Emails
TEAM_EMAILS = "t.coimbrapimenta@latrobe.edu.au, H.Bellette@latrobe.edu.au, V.Pithaih@latrobe.edu.au, 21447366@students.latrobe.edu.au, A.Renata@latrobe.edu.au, R.Rath@latrobe.edu.au, 21443977@students.latrobe.edu.au, 22110321@students.latrobe.edu.au, 21975616@students.latrobe.edu.au, H.Mourao@latrobe.edu.au"

# Sidebar Navigation
action = st.sidebar.radio("What would you like to do?", ["Book Equipment", "Cancel a Booking"])

if action == "Book Equipment":
    with st.sidebar:
        st.header("New Booking")
        with st.form("booking_form", clear_on_submit=True):
            user_name = st.text_input("User Name")
            equipment = st.selectbox("Potentiostat", ["PalmSens (new one)", "DropSens (old one)"])
            booking_date = st.date_input("Date", min_value=datetime.today())
            
            col1, col2 = st.columns(2)
            start_t = col1.time_input("Start Time", value=time(9, 0))
            end_t = col2.time_input("End Time", value=time(10, 0))
            
            submit_button = st.form_submit_button("Confirm Booking")

    if submit_button:
        if user_name:
            try:
                df = conn.read()
                df['Date'] = df['Date'].astype(str)
                
                # Conflict Check
                conflicts = df[(df["Equipment"] == equipment) & (df["Date"] == str(booking_date))]
                is_conflict = False
                for _, row in conflicts.iterrows():
                    if (str(start_t) < row["End Time"]) and (str(end_t) > row["Start Time"]):
                        is_conflict = True
                        existing_user = row["User"]
                        break
                
                if is_conflict:
                    st.error(f"❌ Conflict! Already booked by **{existing_user}**.")
                else:
                    new_entry = pd.DataFrame([{"Equipment": equipment, "Date": str(booking_date), "Start Time": str(start_t), "End Time": str(end_t), "User": user_name}])
                    updated_df = pd.concat([df, new_entry], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success(f"✅ Success! {equipment} booked.")
                    st.balloons()
                    
                    # Email Notification
                    subject = urllib.parse.quote(f"Lab Booking: {equipment}")
                    body = urllib.parse.quote(f"Hi team, I booked {equipment} for {booking_date} from {start_t} to {end_t}.")
                    st.markdown(f'<a href="mailto:{TEAM_EMAILS}?subject={subject}&body={body}" target="_blank"><button style="background-color: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">📧 Notify Team via Email</button></a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter your name.")

elif action == "Cancel a Booking":
    st.sidebar.header("Cancel Booking")
    try:
        df = conn.read()
        if not df.empty:
            # Create a list of descriptions for the dropdown
            df['Selection'] = df['User'] + " | " + df['Equipment'] + " | " + df['Date']
            to_delete = st.sidebar.selectbox("Select your booking to cancel:", df['Selection'].tolist())
            
            if st.sidebar.button("❌ Delete Booking"):
                # Remove the selected row
                df_new = df[df['Selection'] != to_delete].drop(columns=['Selection'])
                conn.update(data=df_new)
                st.success("Booking cancelled successfully!")
                st.rerun()
        else:
            st.sidebar.info("No bookings found to cancel.")
    except Exception as e:
        st.error(f"Error: {e}")

# Display Schedule
st.subheader("📅 Current Schedule")
try:
    df_view = conn.read()
    if not df_view.empty:
        st.dataframe(df_view.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("The schedule is currently empty.")
except:
    st.info("Connect your Google Sheet to start.")
