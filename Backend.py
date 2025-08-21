import psycopg2
import datetime

# --- DATABASE CONNECTION & HELPER FUNCTIONS ---
def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="Personal Fitness Tracker",
            user="postgres",
            password="1234",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def close_db_connection(conn, cursor):
    """Closes the database connection and cursor."""
    if cursor:
        cursor.close()
    if conn:
        conn.close()

# --- USER PROFILE & FRIENDS (CRUD) ---

def create_user(name, email, weight):
    """C: Creates a new user profile."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Users (name, email, weight_kg) VALUES (%s, %s, %s) RETURNING user_id;",
            (name, email, weight)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.Error as e:
        print(f"Error creating user: {e}")
        if conn: conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

def read_user_by_email(email):
    """R: Reads a user profile by email."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email, weight_kg FROM Users WHERE email = %s;", (email,))
        return cur.fetchone()
    except psycopg2.Error as e:
        print(f"Error reading user: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

def update_user_profile(user_id, name, email, weight):
    """U: Updates an existing user profile."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute(
            "UPDATE Users SET name = %s, email = %s, weight_kg = %s WHERE user_id = %s;",
            (name, email, weight, user_id)
        )
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        print(f"Error updating user profile: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def add_friend(user_id, friend_email):
    """C: Adds a new friend connection."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM Users WHERE email = %s;", (friend_email,))
        friend_id = cur.fetchone()
        if not friend_id: return False # Friend email not found

        friend_id = friend_id[0]
        # Insert friendship in a consistent order (smaller ID first) to avoid duplicates
        id1, id2 = sorted([user_id, friend_id])
        cur.execute(
            "INSERT INTO Friends (user_id_1, user_id_2) VALUES (%s, %s);",
            (id1, id2)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error adding friend: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def read_friends(user_id):
    """R: Reads all friends of a user."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        cur.execute(
            "SELECT U.user_id, U.name, U.email FROM Friends F JOIN Users U ON F.user_id_1 = U.user_id OR F.user_id_2 = U.user_id WHERE (F.user_id_1 = %s OR F.user_id_2 = %s) AND U.user_id != %s;",
            (user_id, user_id, user_id)
        )
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error reading friends: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def remove_friend(user_id, friend_id):
    """D: Deletes a friend connection."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        # Ensure symmetric deletion
        id1, id2 = sorted([user_id, friend_id])
        cur.execute(
            "DELETE FROM Friends WHERE user_id_1 = %s AND user_id_2 = %s;",
            (id1, id2)
        )
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        print(f"Error removing friend: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# --- WORKOUTS & EXERCISES (CRUD) ---

def create_workout_with_exercises(user_id, workout_date, duration_minutes, exercises):
    """C: Creates a new workout and its associated exercises in a single transaction."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Workouts (user_id, workout_date, duration_minutes) VALUES (%s, %s, %s) RETURNING workout_id;",
            (user_id, workout_date, duration_minutes)
        )
        workout_id = cur.fetchone()[0]

        for exercise in exercises:
            cur.execute(
                "INSERT INTO Exercises (workout_id, exercise_name, sets, reps, weight_kg) VALUES (%s, %s, %s, %s, %s);",
                (workout_id, exercise['name'], exercise['sets'], exercise['reps'], exercise['weight'])
            )

        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error logging workout: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def read_workouts(user_id):
    """R: Reads a user's workout history."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        cur.execute(
            "SELECT workout_id, workout_date, duration_minutes FROM Workouts WHERE user_id = %s ORDER BY workout_date DESC;",
            (user_id,)
        )
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error reading workouts: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def read_exercises_for_workout(workout_id):
    """R: Reads exercises for a specific workout."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        cur.execute(
            "SELECT exercise_name, sets, reps, weight_kg FROM Exercises WHERE workout_id = %s;",
            (workout_id,)
        )
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error reading exercises: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def delete_workout(workout_id):
    """D: Deletes a workout and all its exercises (due to ON DELETE CASCADE)."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute("DELETE FROM Workouts WHERE workout_id = %s;", (workout_id,))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        print(f"Error deleting workout: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# --- GOALS (CRUD) ---

def create_goal(user_id, description, target, start_date, end_date):
    """C: Creates a new fitness goal."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Goals (user_id, goal_description, target_value, start_date, end_date) VALUES (%s, %s, %s, %s, %s);",
            (user_id, description, target, start_date, end_date)
        )
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error creating goal: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def read_goals(user_id):
    """R: Reads all goals for a user."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        cur.execute(
            "SELECT goal_id, goal_description, target_value, is_completed FROM Goals WHERE user_id = %s ORDER BY is_completed, end_date;",
            (user_id,)
        )
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error reading goals: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def update_goal(goal_id, is_completed):
    """U: Updates a goal's completion status."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute(
            "UPDATE Goals SET is_completed = %s WHERE goal_id = %s;",
            (is_completed, goal_id)
        )
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        print(f"Error updating goal: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def delete_goal(goal_id):
    """D: Deletes a goal."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        cur.execute("DELETE FROM Goals WHERE goal_id = %s;", (goal_id,))
        conn.commit()
        return cur.rowcount > 0
    except psycopg2.Error as e:
        print(f"Error deleting goal: {e}")
        if conn: conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# --- LEADERBOARD (READ) ---

def read_leaderboard(user_id):
    """R: Reads the leaderboard for a user and their friends based on weekly workout minutes."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        
        # Get all users (user + friends) to include in the leaderboard
        cur.execute(
            """
            SELECT U.user_id FROM Users U
            WHERE U.user_id = %s
            UNION
            SELECT U.user_id FROM Friends F
            JOIN Users U ON F.user_id_1 = U.user_id OR F.user_id_2 = U.user_id
            WHERE (F.user_id_1 = %s OR F.user_id_2 = %s) AND U.user_id != %s;
            """,
            (user_id, user_id, user_id, user_id)
        )
        leaderboard_ids = [row[0] for row in cur.fetchall()]

        # Get total workout minutes for this week for all relevant users
        cur.execute(
            """
            SELECT U.name, SUM(W.duration_minutes) as total_minutes
            FROM Users U
            LEFT JOIN Workouts W ON U.user_id = W.user_id
            WHERE U.user_id IN %s
              AND W.workout_date >= date_trunc('week', NOW())
            GROUP BY U.name
            ORDER BY total_minutes DESC;
            """,
            (tuple(leaderboard_ids),)
        )
        return cur.fetchall()
    except psycopg2.Error as e:
        print(f"Error reading leaderboard: {e}")
        return []
    finally:
        close_db_connection(conn, cur)