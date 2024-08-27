import streamlit as st
from common.helpers import get_snowflake_connection, execute_query, is_snowflake_cloud
from utils.config import AUDIT_TABLE_NAME
from typing import Optional

conn = get_snowflake_connection()

def create_audit_table():
    
    if not is_snowflake_cloud():
        return
    
    execute_query(conn, 
        f"""
    CREATE TABLE IF NOT EXISTS {AUDIT_TABLE_NAME} (
      id STRING DEFAULT UUID_STRING() PRIMARY KEY,
      application STRING NOT NULL,
      audit_type STRING NOT NULL,
      user_name STRING NOT NULL,
      user_email STRING NULL,
      context_data TEXT NULL,
      event_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
    """
    )
    print("Audit table created")

def add_audit_record(audit_type: str, event_name: Optional[str] = None):
    
    if not is_snowflake_cloud():
        return
    
    
    user_name = st.experimental_user["user_name"]
    user_email = st.experimental_user["email"] or 'Not Defined'

    if event_name:
        event_name = event_name.replace("'", '').replace('"', '')
    elif audit_type == 'load_app':
        event_name = 'user loaded or refreshed the application'

    execute_query(conn, 
        f"""
        INSERT INTO {AUDIT_TABLE_NAME} (application, audit_type, user_name, user_email, context_data)
        VALUES('streamlit_event_registrations',
               '{audit_type}', '{user_name}', '{user_email}', '{event_name}')
    """
    )
    print("Audit record added")