import streamlit as st
import pandas as pd
from common.helpers import get_snowflake_connection, execute_query

def main():
    st.title("Data Overview")

    conn = get_snowflake_connection()
    
    query = "SELECT 1 AS id, 'Apple' AS fruit, 0.5 AS price UNION ALL SELECT 2, 'Banana', 0.3 UNION ALL SELECT 3, 'Cherry', 0.7"
    results = execute_query(conn, query)

    if results:
        df = pd.DataFrame(results, columns=["ID", "Fruit", "Price"])
        st.dataframe(df)
    else:
        st.write("No data to display.")

if __name__ == "__main__":
    main()