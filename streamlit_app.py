import streamlit as st
from common.helpers import get_snowflake_connection, execute_query

def main():
    st.title("My Snowflake Streamlit App")
    st.write("Welcome to the main page. Use the sidebar to navigate to other pages.")

    # Example of using the helper function
    conn = get_snowflake_connection()
    
    # Dummy query
    query = "SELECT 1 AS one, 'Hello' AS greeting"
    
    results = execute_query(conn, query)
    if results:
        st.write("Sample query result:")
        st.write(results[0])
    else:
        st.error("Failed to execute query")

if __name__ == "__main__":
    main()