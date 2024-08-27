import os
import streamlit as st
import pandas as pd

def get_snowflake_connection():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except ImportError:
        # Local development
        import snowflake.connector
        
        return snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            private_key_file=st.secrets["snowflake"]["key_path"],
            role=st.secrets["snowflake"]["role"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
        )

def execute_query(conn, query):
    try:
        if hasattr(conn, 'sql'):  # Snowpark session
            return conn.sql(query).collect()
        else:  # Regular connector
            cur = conn.cursor()
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None

def execute_query_pandas(conn, query):
    try:
        if hasattr(conn, 'sql'):  # Snowpark session
            # Snowpark session
            return conn.sql(query).collect().to_pandas()
        else:
            # Regular connector
            cur = conn.cursor()
            cur.execute(query)
            columns = [col[0] for col in cur.description]
            data = cur.fetchall()
            return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None