import streamlit as st
import pandas as pd
from common.helpers import get_snowflake_connection, execute_query

def main():
    st.title("Data Analysis")

    conn = get_snowflake_connection()
    
    query = """
    SELECT 'Category A' AS category, 10 AS count
    UNION ALL SELECT 'Category B', 15
    UNION ALL SELECT 'Category C', 7
    UNION ALL SELECT 'Category D', 12
    UNION ALL SELECT 'Category E', 9
    """
    results = execute_query(conn, query)

    if results:
        df = pd.DataFrame(results, columns=["Category", "Count"])
        st.bar_chart(df.set_index("Category"))
    else:
        st.write("No data to display.")

if __name__ == "__main__":
    main()