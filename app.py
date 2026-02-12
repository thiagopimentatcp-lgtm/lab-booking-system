import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import urllib.parse

st.set_page_config(page_title="Lab Booking - SABE", page_icon="🔬")

st.title("🔬 LaSense Booking System")

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Team Data
TEAM_EMAILS = "t.coimbrapimenta@latrobe.edu.au, S.MoraesSilva@latrobe.edu.au, H.Bellette@latrobe.edu.au, V.Pithaih@latrobe.edu.au, 21447366@students.latrobe.edu.au, A.Renata@latrobe.edu.au, R.Rath@latrobe.edu.au, 21443977@students.latrobe.edu.au, 22110321@students.latrobe.edu.au, 21975616@students.latrobe.edu.au, H.Mourao@latrobe.edu.au"
USER_NAMES = ["", "Andrea", "Bayan", "Hansi", "Henrique", "Henry", "Inder", "Manthi", "Ronil", "Saimon", "Thiago", "Vatsala"]

# Sidebar Navigation
action = st.sidebar.radio("Menu", ["Book Equipment", "Cancel a Booking"])

# Helper to read fresh data from the Google Sheet
def get_data():
    return conn.read(ttl=0) # ttl=0 prevents using old cached data

if action == "Book Equipment":
    with st.sidebar:
        st.header("New Booking")
        with st.form("booking_form", clear_on_submit=True):
            # NEW: Dropdown for User Names
            selected_user = st.selectbox("Who is Booking?", USER_NAMES)
            equipment = st.selectbox("Potentiostat", ["", "Dropsens (Old)", "PalmSens (New)"])
            booking_date = st.date_input("Date", min_value=datetime.today())
            
            col1, col2 = st.columns(2)
            start_t = col1.time_input("Start Time", value=time(9, 0))
            end_t = col2.time_input("End Time", value=time(10, 0))
            
            submit_button = st.form_submit_button("Confirm Booking")

    if submit_button:
        try:
            # 1. Fetch current data to ensure we append and don't overwrite
            df = get_data()
            if df is None: df = pd.DataFrame(columns=["Equipment", "Date", "Start Time", "End Time", "User"])
            
            # 2. Format columns for comparison
            if not df.empty:
                df['Date'] = df['Date'].astype(str)
                df['Start Time'] = df['Start Time'].astype(str)
                df['End Time'] = df['End Time'].astype(str)
            
            # 3. Conflict Check Logic
            is_conflict = False
            if not df.empty:
                conflicts = df[(df["Equipment"] == equipment) & (df["Date"] == str(booking_date))]
                for _, row in conflicts.iterrows():
                    # Check if times overlap: (StartA < EndB) and (EndA > StartB)
                    if (str(start_t) < row["End Time"]) and (str(end_t) > row["Start Time"]):
                        is_conflict = True
                        existing_user = row["User"]
                        break
            
            if is_conflict:
                st.error(f"❌ Conflict! This slot is already booked by **{existing_user}**.")
            else:
                # 4. Prepare new row and append to existing data
                new_entry = pd.DataFrame([{
                    "Equipment": equipment, 
                    "Date": str(booking_date), 
                    "Start Time": str(start_t), 
                    "End Time": str(end_t), 
                    "User": selected_user
                }])
                
                updated_df = pd.concat([df, new_entry], ignore_index=True)
                
                # 5. Push updated full dataframe back to Google Sheets
                conn.update(data=updated_df)
                st.success(f"✅ Success! {equipment} has been booked for {selected_user}.")
                st.balloons()
                
                # Notification Email Link
                subject = urllib.parse.quote(f"Lab Booking: {equipment}")
                body = urllib.parse.quote(f"Hi team, I have booked {equipment} for {booking_date} from {start_t} to {end_t}.")
                st.markdown(f'<a href="mailto:{TEAM_EMAILS}?subject={subject}&body={body}" target="_blank"><button style="background-color: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">📧 Notify Team via Email</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Database error: {e}")

elif action == "Cancel a Booking":
    st.sidebar.header("Cancel Booking")
    try:
        df = get_data()
        if df is not None and not df.empty:
            # Dropdown for the user to identify themselves
            cancelling_user = st.sidebar.selectbox("Confirm Your Name", USER_NAMES)
            
            # Filter the list to show ONLY bookings belonging to that user
            user_bookings = df[df['User'] == cancelling_user]
            
            if not user_bookings.empty:
                user_bookings['Selection'] = user_bookings['Equipment'] + " | " + user_bookings['Date'] + " | " + user_bookings['Start Time']
                to_delete = st.sidebar.selectbox("Select your booking to remove:", user_bookings['Selection'].tolist())
                
                if st.sidebar.button("❌ Remove My Booking"):
                    # Find the original row in the main dataframe and remove it
                    # We match based on User and the specific Selection strings
                    df['MatchKey'] = df['User'] + " | " + df['Equipment'] + " | " + df['Date'] + " | " + df['Start Time']
                    current_key = cancelling_user + " | " + to_delete
                    
                    df_new = df[df['MatchKey'] != current_key].drop(columns=['MatchKey'])
                    
                    conn.update(data=df_new)
                    st.success("Booking successfully removed.")
                    st.rerun()
            else:
                st.sidebar.warning(f"No bookings found under the name '{cancelling_user}'.")
        else:
            st.sidebar.info("The schedule is currently empty.")
    except Exception as e:
        st.error(f"Error reading data: {e}")

# --- FILTERED DISPLAY ---
st.subheader("📅 Upcoming Lab Schedule")
try:
    df_all = get_data()
    if df_all is not None and not df_all.empty:
        # Convert to datetime objects for filtering
        df_all['Date_obj'] = pd.to_datetime(df_all['Date'])
        today = datetime.combine(datetime.today(), time.min)
        
        # Filter: Only keep rows where Date is today or later
        df_upcoming = df_all[df_all['Date_obj'] >= today].copy()
        df_upcoming = df_upcoming.drop(columns=['Date_obj'])
        
        if not df_upcoming.empty:
            st.dataframe(df_upcoming.sort_values(by=["Date", "Start Time"]), use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming bookings. The lab is free!")
    else:
        st.info("No bookings recorded yet.")
except Exception as e:
    st.error(f"Could not load schedule: {e}")





