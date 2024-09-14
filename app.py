import streamlit as st
import pandas as pd
import pymysql
import pickle
import os

# Database connection details
db_host = 'localhost'
db_user = 'root'
db_password = ''
db_name = 'sra'

connection = pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_name)

# Create the database if it doesn't exist
with connection.cursor() as cursor:
    db_sql = f"CREATE DATABASE IF NOT EXISTS {db_name};"
    cursor.execute(db_sql)

# Connect to the specific database
connection.select_db(db_name)

with connection.cursor() as cursor:
    table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """
    cursor.execute(table_sql)

# Load the model using the absolute path
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_model():
    model_path = os.path.join(os.path.dirname(__file__), "Model", "model.pkl")
    return pickle.load(open(model_path, "rb"))

# Set page configuration
st.set_page_config(
    page_title="Health Insurance Cost Prediction System",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="auto",
)

# Initialize session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

model = load_model()

# Define the login page
def login_page():
    st.markdown(
        """
        <div>
            <center><h1>Welcome to Health Insurance Cost Prediction System</h1></center>
            <center><h2>Login Page</h2></center>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Define hardcoded credentials for demonstration purposes
    valid_username = "user123"
    valid_password = "pass123"

    # Input fields for username and password
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    # Check credentials against the database
    if st.button("Login"):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE username=%s AND password=%s"
                cursor.execute(sql, (username, password))
                result = cursor.fetchone()

            if result:
                # Store login status in session_state
                st.session_state.logged_in = True
                st.session_state.page = "input_data"
            else:
                st.error("Invalid credentials. Please try again.")
        except Exception as e:
            st.error(f"Login failed. Error: {e}")

    # Registration button
    if st.button("Register if New User"):
        st.session_state.page = "register"


def registration_page():
    st.markdown(
        """
        <div>
            <center><h1>Welcome to Health Insurance Cost Prediction System</h1></center>
            <center><h2>Registration Page</h2></center>
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_username = st.text_input("New Username:")
    new_password = st.text_input("New Password:", type="password")

    if st.button("Register"):
        if not new_username or not new_password:
            st.error("Username and password cannot be empty. Please enter valid credentials.")
        else:
            try:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                    cursor.execute(sql, (new_username, new_password))
                connection.commit()

                st.success("Registration successful. You can now log in.")

                # Provide a clickable link to the login page in the same window
                st.write("To log in, click <a href='/login' target='_self'>here</a>.", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Registration failed. Error: {e}")


# Define the input data page
def input_data_page():
    st.markdown(
        """
        <div>
            <center><h1>Input Data Page</h1></center>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("### Information of the beneficiary")

    input_data = []
    # Age
    input_data.append(st.slider("Enter his/her age", 0, 100))

    # Sex
    sex = st.radio("Gender of beneficiary", ("Male", "Female"))
    input_data.append(1 if sex == "Male" else 0)

    # Height and Weight to calculate BMI
    height = st.slider("Enter his/her height (in cm)", 100, 250)
    weight = st.slider("Enter his/her weight (in kg)", 30, 200)

    # Calculate BMI
    bmi = weight / ((height / 100) ** 2)
    input_data.append(round(bmi, 2))

    # Display BMI bar
    st.text(f"Calculated BMI: {bmi}")
    st.progress(bmi / 40.0)  # Assuming a healthy BMI range is between 18.5 and 30

    # Children
    input_data.append(st.selectbox("How many children does he/she have?", [0, 1, 2, 3, 4, 5]))

    # Smoke
    smoke = st.radio("Does he/she smoke?", ("Yes", "No"))
    input_data.append(1 if smoke == "Yes" else
    0)

    # Region
    region = st.selectbox("Select the region", ("Northeast", "Northwest", "Southeast", "Southwest"))
    if region == "Northeast":
        input_data.append(0)
    elif region == "Northwest":
        input_data.append(1)
    elif region == "Southeast":
        input_data.append(2)
    elif region == "Southwest":
        input_data.append(3)

    # Prediction
    if st.button("Predict"):
        try:
            prediction = model.predict([input_data])
            st.session_state.prediction_result = prediction[0]
            st.session_state.page = "result"
        except Exception as e:
            st.error(f"Prediction failed. Error: {e}")

admin_username = "admin"
admin_password = "admin123"

# Define the result page
def result_page():
    st.markdown(
        """
        <div>
            <center><h1>Result Page</h1></center>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Display the prediction result
    if "prediction_result" in st.session_state:
        prediction_result = round(float(st.session_state.prediction_result), 2)
        st.success(f"The estimated medical cost is ${prediction_result}")

        # Display insurance policy links
        st.write("### Insurance Policy Links")
        st.markdown("[PolicyBazaar](https://www.policybazaar.com/health-insurance/health-insurance-india/)")
        st.markdown("[Acko](https://www.acko.com/health-insurance/)")
        # Add more links if needed

        # Prompt user for admin password to access the admin panel
        admin_password_input = st.text_input("Enter Admin Password:", type="password")
        if admin_password_input == admin_password:
            # Add a button to go to the admin panel
            if st.button("Go to Admin Panel"):
                st.session_state.page = "admin_panel"
        elif admin_password_input != "":
            st.warning("Incorrect admin password. Access denied.")
    else:
        st.error("No prediction result found. Please go back to the Input Data page and make a prediction.")

# Define the admin panel page
def admin_panel():
    st.markdown(
        """
        <div>
            <center><h1>Admin Panel</h1></center>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Display user data from the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        result = cursor.fetchall()

    if result:
        df = pd.DataFrame(result, columns=["ID", "Username", "Password"])
        st.dataframe(df)
    else:
        st.info("No user data available.")

# Main function to switch between pages based on user input
def main():
    # Check login status
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            registration_page()
        else:
            login_page()
    elif st.session_state.page == "input_data":
        input_data_page()
    elif st.session_state.page == "result":
        result_page()
    elif st.session_state.page == "admin_panel":
        admin_panel()

    # Clean up session state when the user logs out or app starts
    if st.session_state.page == "login" and st.session_state.logged_in:
        st.session_state.logged_in = False
        st.session_state.page = "login"

if __name__ == "__main__":
    main()

connection.close()
