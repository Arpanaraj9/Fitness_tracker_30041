import streamlit as st
import Backend as backend
import datetime

# --- HELPER FUNCTIONS FOR UI ---
def get_user_id():
    """Gets the user ID from session state."""
    return st.session_state.get('user_id')

def get_user_name():
    """Gets the user name from session state."""
    return st.session_state.get('user_name')

# --- MAIN PAGE LAYOUT ---
st.set_page_config(page_title="Personal Fitness Tracker")
st.title("💪 Fitness Tracker")

# Initialize session state for the user ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# --- USER LOGIN/REGISTRATION ---
if not get_user_id():
    st.header("Login or Register")
    email = st.text_input("Enter your email:")
    if st.button("Log In"):
        user = backend.read_user_by_email(email)
        if user:
            st.session_state.user_id = user[0]
            st.session_state.user_name = user[1]
            st.success(f"Welcome back, {user[1]}!")
            st.experimental_rerun()
        else:
            st.error("User not found. Please register below.")
    with st.expander("New User? Register here."):
        with st.form("new_user_form"):
            name = st.text_input("Name")
            email_reg = st.text_input("Email")
            weight = st.number_input("Weight (kg)", min_value=1.0)
            submitted = st.form_submit_button("Register")
            if submitted:
                new_id = backend.create_user(name, email_reg, weight)
                if new_id:
                    st.success(f"Successfully registered! Your user ID is {new_id}.")
                    st.session_state.user_id = new_id
                    st.session_state.user_name = name
                    st.experimental_rerun()
                else:
                    st.error("Registration failed. Email might already exist.")

# --- APPLICATION SECTIONS (Logged-in view) ---
else:
    st.sidebar.header(f"Welcome, {get_user_name()}!")
    selected_page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Log Workout", "Friends & Leaderboard", "Goals"]
    )
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    # --- DASHBOARD & PROFILE (READ/UPDATE) ---
    if selected_page == "Dashboard":
        st.header("Your Dashboard")

        # Display user profile
        user_data = backend.read_user_by_email(st.session_state.user_name)
        if user_data:
            st.subheader("Your Profile")
            st.write(f"**Name:** {user_data[1]}")
            st.write(f"**Email:** {user_data[2]}")
            st.write(f"**Weight:** {user_data[3]} kg")

            # Update Profile form
            with st.form("update_profile_form"):
                st.subheader("Update Profile")
                new_name = st.text_input("New Name", value=user_data[1])
                new_email = st.text_input("New Email", value=user_data[2])
                new_weight = st.number_input("New Weight (kg)", value=user_data[3], min_value=1.0)
                if st.form_submit_button("Update"):
                    if backend.update_user_profile(get_user_id(), new_name, new_email, new_weight):
                        st.session_state.user_name = new_name
                        st.success("Profile updated successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to update profile.")
        else:
            st.error("Could not load user data.")

        st.subheader("Your Workout History")
        workouts = backend.read_workouts(get_user_id())
        if workouts:
            for workout in workouts:
                workout_id, date, duration = workout
                with st.expander(f"Workout on {date} - {duration} minutes"):
                    st.write(f"**Duration:** {duration} minutes")
                    exercises = backend.read_exercises_for_workout(workout_id)
                    st.markdown("---")
                    st.subheader("Exercises")
                    if exercises:
                        for exercise in exercises:
                            name, sets, reps, weight = exercise
                            st.write(f"- **{name}**: {sets} sets, {reps} reps, {weight} kg")
                        if st.button("Delete Workout", key=f"del_wk_{workout_id}"):
                            if backend.delete_workout(workout_id):
                                st.success("Workout deleted.")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete workout.")
                    else:
                        st.info("No exercises logged for this workout.")
        else:
            st.info("You haven't logged any workouts yet.")

    # --- LOG WORKOUT (CREATE) ---
    elif selected_page == "Log Workout":
        st.header("Log a New Workout")
        with st.form("new_workout_form"):
            workout_date = st.date_input("Date", datetime.date.today())
            duration = st.number_input("Duration (minutes)", min_value=1)
            
            st.subheader("Exercises")
            num_exercises = st.number_input("Number of exercises", min_value=1, value=1)
            exercises_list = []
            for i in range(num_exercises):
                st.markdown(f"**Exercise {i+1}**")
                name = st.text_input("Exercise Name", key=f"name_{i}")
                sets = st.number_input("Sets", min_value=1, key=f"sets_{i}")
                reps = st.number_input("Reps", min_value=1, key=f"reps_{i}")
                weight = st.number_input("Weight (kg)", min_value=0.0, key=f"weight_{i}")
                exercises_list.append({'name': name, 'sets': sets, 'reps': reps, 'weight': weight})
            
            submitted = st.form_submit_button("Log Workout")
            if submitted:
                if backend.create_workout_with_exercises(get_user_id(), workout_date, duration, exercises_list):
                    st.success("Workout logged successfully!")
                else:
                    st.error("Failed to log workout.")
    
    # --- FRIENDS & LEADERBOARD (CREATE/READ/DELETE) ---
    elif selected_page == "Friends & Leaderboard":
        st.header("Your Friends")
        
        with st.form("add_friend_form"):
            st.subheader("Add a Friend")
            friend_email = st.text_input("Friend's Email")
            if st.form_submit_button("Add Friend"):
                if backend.add_friend(get_user_id(), friend_email):
                    st.success(f"Friend request sent to {friend_email}!")
                else:
                    st.error(f"Could not find a user with email {friend_email} or you are already friends.")

        st.subheader("Your Friends List")
        friends = backend.read_friends(get_user_id())
        if friends:
            for friend in friends:
                friend_id, name, email = friend
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"- {name} ({email})")
                with col2:
                    if st.button("Remove", key=f"rem_fr_{friend_id}"):
                        if backend.remove_friend(get_user_id(), friend_id):
                            st.success(f"{name} has been removed from your friends list.")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to remove friend.")
        else:
            st.info("You don't have any friends yet.")

        st.markdown("---")
        st.header("Weekly Leaderboard")
        leaderboard_data = backend.read_leaderboard(get_user_id())
        if leaderboard_data:
            st.dataframe(leaderboard_data, use_container_width=True)
        else:
            st.info("No leaderboard data available for this week. Log a workout to get started!")

    # --- GOALS (CRUD) ---
    elif selected_page == "Goals":
        st.header("Your Goals")
        
        # CREATE Goal
        with st.form("new_goal_form"):
            st.subheader("Set a New Goal")
            description = st.text_area("Goal Description")
            target = st.number_input("Target Value (e.g., 5 workouts/week)", min_value=1)
            start_date = st.date_input("Start Date", datetime.date.today())
            end_date = st.date_input("End Date")
            if st.form_submit_button("Set Goal"):
                if backend.create_goal(get_user_id(), description, target, start_date, end_date):
                    st.success("Goal set successfully!")
                else:
                    st.error("Failed to set goal.")
        
        st.markdown("---")
        
        # READ/UPDATE/DELETE Goals
        st.subheader("Your Current Goals")
        goals = backend.read_goals(get_user_id())
        if goals:
            for goal in goals:
                goal_id, desc, target, is_completed = goal
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                with col1:
                    status = "✅ Completed" if is_completed else "⏳ In Progress"
                    st.write(f"**{status}**: {desc}")
                with col2:
                    is_completed_new = st.checkbox("Mark as Done", value=is_completed, key=f"chk_{goal_id}")
                    if is_completed_new != is_completed:
                        if backend.update_goal(goal_id, is_completed_new):
                            st.success("Goal status updated.")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to update goal status.")
                with col3:
                    if st.button("Delete", key=f"del_goal_{goal_id}"):
                        if backend.delete_goal(goal_id):
                            st.success("Goal deleted.")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to delete goal.")
        else:
            st.info("You haven't set any goals yet.")