import streamlit as st
import pandas as pd
from common.helpers import execute_query_pandas, get_snowflake_connection
from components.chart import build_chart
from services.audit_service import add_audit_record, create_audit_table
from utils.config import *

conn = get_snowflake_connection()

def main_page():
    st.title("LFX Event Registrations Report :rocket:")
    st.write("Event registration data from Cvent or RegFox.")
    st.divider()

    event_name_filter = handle_search_input()
    st.divider()

    display_matching_events(event_name_filter)
    st.divider()

    display_chart(event_name_filter)
    st.divider()

    display_table_data(event_name_filter)
    st.divider()

    handle_audit_logging()

def handle_search_input():
    event_name_filter_raw = st.text_input(
        label='Enter event name to search.',
        placeholder='Search for an event name',
        help='Enter event name',
        key='event_name_search',
        max_chars=80,
        on_change=execute_search,
    )
    event_name_filter = event_name_filter_raw.replace("'", '').replace('"', '')
    if event_name_filter_raw != event_name_filter:
        st.write(':exclamation: :red[Invalid characters in search field. Do not include quotes.]')
        event_name_filter = ''
    return event_name_filter

def display_matching_events(event_name_filter):
    st.write('#### Matching Events')
    if event_name_filter and len(event_name_filter) > 2:
        distinct_events_query = f"""
            SELECT DISTINCT {EVENT_NAME_COLUMN}
            FROM {TABLE_NAME}
            WHERE event_name ilike '%{event_name_filter}%'
            ORDER BY event_name;
        """
        event_name_df: pd.DataFrame = execute_query_pandas(conn, distinct_events_query)
        num_filtered_events = len(event_name_df)
        if num_filtered_events > 0:
            if num_filtered_events == 1:
                st.write(f'{num_filtered_events} match')
            else:
                st.write(f'{num_filtered_events} matches - update the event name above to refine your search')
            for value in event_name_df[EVENT_NAME_COLUMN]:
                st.write(f'- {value}')
        else:
            st.write('No matching events. Search for an event name above.')
    else:
        st.write('Search for an event name above.')

def display_chart(event_name_filter):
    st.write('#### Chart')
    if event_name_filter and len(event_name_filter) > 2:
        line_chart_query = f"""
            SELECT {REGISTRATION_DATE_COLUMN}, COUNT(*) AS registration_count, {EVENT_NAME_COLUMN}
            FROM {TABLE_NAME}
            WHERE event_name ilike '%{event_name_filter}%'
            GROUP BY {REGISTRATION_DATE_COLUMN}, {EVENT_NAME_COLUMN}
            ORDER BY {REGISTRATION_DATE_COLUMN};
        """
        chart_df: pd.DataFrame = execute_query_pandas(conn, line_chart_query)
        chart_df.drop(columns=EVENT_NAME_COLUMN, inplace=True)

        if not chart_df.empty:
            chart_selection: Optional[str] = st.selectbox(
                'Select chart style:', options=CHART_TYPES, index=0)
            chart_title = f'Event Registrations'
            c = build_chart(chart_df, chart_selection, chart_title)
            st.altair_chart(c, use_container_width=True)
        else:
            st.write("No data available for the selected event.")
    else:
        st.write('Search for an event name above.')

def display_table_data(event_name_filter):
    st.write('#### Table Data')
    if event_name_filter and len(event_name_filter) > 2:
        filters = get_table_filters()
        df = get_filtered_data(event_name_filter, filters)
        display_download_button(df, event_name_filter)
        st.dataframe(df, use_container_width=True)
    else:
        st.write('Search for an event name above.')

def get_table_filters():
    col1, col2, col3, col4, col5 = st.columns(5)
    return {
        'speaker': col1.radio("Speaker Filter", [OPT_SHOW_ALL_TEXT, IS_SPEAKER_TEXT, IS_NOT_SPEAKER_TEXT]),
        'lf_member': col2.radio("LF Member Filter", [OPT_SHOW_ALL_TEXT, IS_LF_MEMBER_TEXT, IS_NOT_LF_MEMBER_TEXT]),
        'project_member': col3.radio("Event Project Member Filter", [OPT_SHOW_ALL_TEXT, IS_PROJECT_MEMBER_TEXT, IS_NOT_PROJECT_MEMBER_TEXT]),
        'opt_in_lf_news': col4.radio("Opt-In Filter for LF News Announcements", [OPT_SHOW_ALL_TEXT, OPT_IN_ONLY_TXT, OPT_OUT_ONLY_TXT]),
        'opt_in_tnc_promos': col5.radio("Opt-In Filter for T&C Promotions", [OPT_SHOW_ALL_TEXT, OPT_IN_ONLY_TXT, OPT_OUT_ONLY_TXT])
    }

def get_filtered_data(event_name_filter, filters):
    table_query = f"""
        SELECT *
        FROM {TABLE_NAME}
        WHERE event_name ilike '%{event_name_filter}%'
        ORDER BY {REGISTRATION_DATE_COLUMN};
    """
    df: pd.DataFrame = execute_query_pandas(conn, table_query)
    df.drop(columns=[REGISTRATION_ID_COL, PROJECT_ID_COL, COMPANY_ID_COL], inplace=True)
    df_filtered = df[~df[USER_TITLE_COLUMN].str.contains('test', case=False, na=False)]

    if filters['speaker'] != OPT_SHOW_ALL_TEXT:
        df_filtered = df_filtered[df[IS_SPEAKER_COL] == (filters['speaker'] == IS_SPEAKER_TEXT)]
    if filters['lf_member'] != OPT_SHOW_ALL_TEXT:
        df_filtered = df_filtered[df[IS_LF_MEMBER_COL] == (filters['lf_member'] == IS_LF_MEMBER_TEXT)]
    if filters['project_member'] != OPT_SHOW_ALL_TEXT:
        df_filtered = df_filtered[df[IS_PROJECT_MEMBER_COL] == (filters['project_member'] == IS_PROJECT_MEMBER_TEXT)]
    if filters['opt_in_lf_news'] != OPT_SHOW_ALL_TEXT:
        df_filtered = df_filtered[df[OPT_IN_LF_NEWS_COL] == (filters['opt_in_lf_news'] == OPT_IN_ONLY_TXT)]
    if filters['opt_in_tnc_promos'] != OPT_SHOW_ALL_TEXT:
        df_filtered = df_filtered[df[OPT_IN_TNC_PROMOS_COL] == (filters['opt_in_tnc_promos'] == OPT_IN_ONLY_TXT)]

    return df_filtered

def display_download_button(df, event_name_filter):
    csv = df.to_csv(index=True)
    st.download_button(
        label=":arrow_down: :exclamation: Download data as CSV :exclamation: :arrow_down:",
        data=csv,
        file_name="event_registration_data.csv",
        mime='text/csv',
        on_click=download_clicked,
        args=(event_name_filter,),
    )
    st.markdown(
        ":exclamation: _This information contains confidential data protected under The Linux Foundation's Privacy Policy. "
        "By downloading this information, you commit that (1) you will use it solely for legitimate purposes authorized by "
        "our Privacy Policy; and (2) you will handle it with the highest level of confidentiality and care. "
        "Unauthorized use, distribution, or disclosure of this data is strictly prohibited._"
    )

def execute_search():
    add_audit_record(AUDIT_TYPE_EXECUTE_SEARCH, st.session_state.event_name_search)

def download_clicked(event_name_filter: str):
    add_audit_record(AUDIT_TYPE_DOWNLOAD_REPORT, event_name_filter)

def handle_audit_logging():
    create_audit_table()
    add_audit_record(AUDIT_TYPE_LOAD_APP)

if __name__ == "__main__":
    main_page()