import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time
import pytz 
import urllib.parse

st.set_page_config(page_title="Lab Booking - SABE", page_icon="🔬")

st.title("🔬 LaSense Booking System")

# Logo
st.sidebar.image("lasense.PNG", use_container_width=True)

# Melbourne Timezone Initialization
melb_tz = pytz.timezone('Australia/Melbourne')
now_melb = datetime.now(melb_tz)
current_date_melb = now_melb.date()
current_time_melb = now_melb.time()

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Team Data
TEAM_EMAILS = "t.coimbrapimenta@latrobe.edu.au, 21608125@students.latrobe.edu.au, 21957653@students.latrobe.edu.au, 22880912@students.latrobe.edu.au, d.langley@latrobe.edu.au, S.MoraesSilva@latrobe.edu.au, H.Bellette@latrobe.edu.au, V.Pithaih@latrobe.edu.au, 21447366@students.latrobe.edu.au, R.Rath@latrobe.edu.au, 21443977@students.latrobe.edu.au, 22110321@students.latrobe.edu.au, 21975616@students.latrobe.edu.au"
USER_NAMES = ["", "Ashab", "Bayan", "Daniel", "Elizabeth", "Hansi", "Henry", "Inder", "Manthi", "Ronil", "Saimon", "Thiago", "Thien", "Vatsala"]

action = st.sidebar.radio("Menu", ["Book Equipment", "Cancel a Booking"])

def get_data():
    df = conn.read(ttl=0)
    if df is not None and not df.empty:
        # CRITICAL: Standardize all columns to strings to avoid type errors
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['Start Time'] = df['Start Time'].astype(str)
        df['End Time'] = df['End Time'].astype(str)
    return df

# --- BOOKING SECTION ---
if action == "Book Equipment":
    with st.sidebar:
        st.header("New Booking")
        with st.form("booking_form", clear_on_submit=True):
            selected_user = st.selectbox("Select Your Name", USER_NAMES)
            equipment = st.selectbox("Equipment", ["", "DropSens (Old)", "PalmSens (4 Channels)", "PalmSens (8 Channels)", "Portable Pstat (1 Channel)"])
            booking_date = st.date_input("Date", min_value=current_date_melb)
            
            col1, col2 = st.columns(2)
            start_t = col1.time_input("Start Time", value=time(9, 0))
            end_t = col2.time_input("End Time", value=time(10, 0))
            
            submit_button = st.form_submit_button("Confirm Booking")

    if submit_button:
        if not selected_user or not equipment:
            st.error("Please select both your name and the equipment.")
        elif booking_date == current_date_melb and start_t < current_time_melb:
            st.error(f"❌ Past Time Error: It is currently {current_time_melb.strftime('%H:%M')} in Melbourne.")
        elif start_t >= end_t:
            st.error("❌ Logic Error: End Time must be after Start Time.")
        else:
            try:
                df = get_data()
                if df is None: df = pd.DataFrame(columns=["Equipment", "Date", "Start Time", "End Time", "User"])
                
                # Check for overlaps
                conflicts = df[(df["Equipment"] == equipment) & (df["Date"] == str(booking_date))]
                is_conflict = False
                for _, row in conflicts.iterrows():
                    if (str(start_t) < str(row["End Time"])) and (str(end_t) > str(row["Start Time"])):
                        is_conflict = True
                        existing_user = row["User"]
                        break
                
                if is_conflict:
                    st.error(f"❌ Conflict! Slot taken by **{existing_user}**.")
                else:
                    new_entry = pd.DataFrame([{"Equipment": equipment, "Date": str(booking_date), "Start Time": str(start_t), "End Time": str(end_t), "User": selected_user}])
                    updated_df = pd.concat([df, new_entry], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success(f"✅ Success! {equipment} booked for {selected_user}.")
                    st.balloons()
                    
                    subject = urllib.parse.quote(f"Lab Booking: {equipment}")
                    body = urllib.parse.quote(f"Hi team, I booked {equipment} for {booking_date} from {start_t} to {end_t}.")
                    st.markdown(f'<a href="mailto:{TEAM_EMAILS}?subject={subject}&body={body}" target="_blank"><button style="background-color: #007bff; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer;">📧 Notify Team via Email</button></a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

# --- UPDATED CANCELLATION SECTION ---
elif action == "Cancel a Booking":
    st.sidebar.header("Cancel Booking")
    try:
        df = get_data()
        if df is not None and not df.empty:
            cancelling_user = st.sidebar.selectbox("Confirm Your Identity", USER_NAMES)
            
            if cancelling_user:
                today_str = current_date_melb.strftime('%Y-%m-%d')
                
                # Filter strictly for user and future/today bookings
                my_actual_bookings = df[
                    (df['User'] == cancelling_user) & 
                    (df['Date'] >= today_str)
                ].copy()
                
                if not my_actual_bookings.empty:
                    # Create the selection string
                    my_actual_bookings['Selection'] = my_actual_bookings['Equipment'] + " | " + my_actual_bookings['Date'] + " | " + my_actual_bookings['Start Time']
                    to_remove = st.sidebar.selectbox("Select CURRENT booking to remove:", my_actual_bookings['Selection'].tolist())
                    
                    if st.sidebar.button("❌ Remove My Booking"):
                        # Re-create MatchKey for the main dataframe to find the row to drop
                        df['MatchKey'] = df['User'] + " | " + df['Equipment'] + " | " + df['Date'] + " | " + df['Start Time']
                        current_key = cancelling_user + " | " + to_remove
                        
                        df_new = df[df['MatchKey'] != current_key].drop(columns=['MatchKey'])
                        conn.update(data=df_new)
                        st.success("Booking successfully removed.")
                        st.rerun()
                else:
                    st.sidebar.warning(f"No current or future bookings found for {cancelling_user}.")
        else:
            st.sidebar.info("The schedule is empty.")
    except Exception as e:
        st.error(f"Error during cancellation: {e}")

# --- DISPLAY SECTION ---
st.subheader("📅 Upcoming Lab Schedule")
try:
    df_all = get_data()
    if df_all is not None and not df_all.empty:
        today_str = current_date_melb.strftime('%Y-%m-%d')
        df_upcoming = df_all[df_all['Date'] >= today_str].copy()
        
        if not df_upcoming.empty:
            st.dataframe(df_upcoming.sort_values(by=["Date", "Start Time"]), use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming bookings. The lab is free!")
    else:
        st.info("No bookings recorded yet.")
except Exception as e:
    st.error(f"Could not load schedule: {e}")
