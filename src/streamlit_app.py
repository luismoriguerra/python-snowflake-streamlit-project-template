import streamlit as st
import io
import altair as alt
import pandas as pd
from common.helpers import get_snowflake_connection, execute_query_pandas
from typing import Optional

conn = get_snowflake_connection()

# A few constants to simplify things below
table_name = 'ANALYTICS.PLATINUM.EVENT_REGISTRATION_EXPORT'
event_table_name = 'ANALYTICS.PLATINUM.EVENT_REGISTRATIONS'
audit_table_name = 'ANALYTICS.PLATINUM.APPLICATION_AUDIT_LOG'
# audit_table_name = 'RAW.APPLICATION_AUDIT_LOG'
audit_type_load_app = 'load_app'
audit_type_execute_search = 'execute_search'
audit_type_download_report = 'download_report'
registration_id_col = 'REGISTRATION_ID'
project_id_col = 'PROJECT_ID'
company_id_col = 'COMPANY_ID'
event_name_column = 'EVENT_NAME'
user_title_column = 'TITLE'
registration_count_column = 'REGISTRATION_COUNT'
opt_in_lf_news_col = 'OPT_IN_LF_NEWS_ANNOUNCEMENTS'
opt_in_tnc_promos_col = 'OPT_IN_TNC_PROMOTIONS'
is_speaker_col = 'IS_SPEAKER'
is_lf_member_col = 'IS_CURRENT_LF_MEMBER'
is_project_member_col = 'IS_CURRENT_PROJECT_MEMBER'
registration_date_column = 'REGISTRATION_DATE'

default_event_selection = '  --- Select Event ---  '
chart_types = ['Line Chart', 'Bar Chart', 'Mark Circles']
opt_show_all_text = 'Show All'
opt_in_only_txt = 'Show Opt-In Records Only'
opt_out_only_txt = 'Show Did Not Opt-In Records Only'
is_speaker_text = 'Speakers'
is_not_speaker_text = 'Attendees Only'
is_lf_member_text = 'LF Member'
is_not_lf_member_text = 'Not a LF Member'
is_project_member_text = 'Project Member'
is_not_project_member_text = 'Not a Project Member'
num_filtered_events: int = 0


def create_audit_table():
    execute_query(conn, 
        f"""
    CREATE TABLE IF NOT EXISTS {audit_table_name} (
      id STRING DEFAULT UUID_STRING() PRIMARY KEY,
      application STRING NOT NULL,
      audit_type STRING NOT NULL,
      user_name STRING NOT NULL,
      user_email STRING NULL,
      context_data TEXT NULL,
      event_ts TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
    )
    """
    ).collect()
    print("Audit table created")


def add_audit_record(audit_type: str, event_name: Optional[str] = None):
    st.write(f'User dict: {st.experimental_user.to_dict()}')
    user_name = st.experimental_user["user_name"]
    user_email = st.experimental_user["email"]

    if not user_email:
        user_email = 'Not Defined'

    if event_name:
        event_name = event_name.replace("'", '').replace('"', '')
    elif audit_type == audit_type_load_app:
        event_name = 'user loaded or refreshed the application'

    execute_query(conn, 
        f"""
        INSERT INTO {audit_table_name} (application, audit_type, user_name, user_email, context_data)
        VALUES('streamlit_event_registrations',
               '{audit_type}', '{user_name}', '{user_email}', '{event_name}')
    """
    ).collect()
    print("Audit record added")


def execute_search():
    # Add a note about downloading the report - grab the text_input value from the session state using the test_input key identifier
    add_audit_record(audit_type_execute_search,
                     st.session_state.event_name_search)


def download_clicked(event_name_filter: str):
    # Add a note about downloading the report
    add_audit_record(audit_type_download_report, event_name_filter)


def build_chart(
    chart_df: pd.DataFrame, chart_type: Optional[str], chart_title: str, sub_title: str = '', x_axis: str = 'Registration Date', y_axis: str = '# Registrations'
) -> alt.Chart:
    # TODO refactor to re-use common attributes.
    # Example charts: https://altair-viz.github.io/gallery/
    if chart_type == 'Bar Chart':
        c = (
            alt.Chart(chart_df, title=alt.Title(
                chart_title, subtitle=sub_title))
            .mark_bar()
            .encode(x=alt.X(registration_date_column, title=x_axis), y=alt.Y(registration_count_column, title=y_axis))
            .configure_title(fontSize=16)
            .interactive()
        )
    elif chart_type == 'Mark Circles':
        c = (
            alt.Chart(chart_df, title=alt.Title(
                chart_title, subtitle=sub_title))
            .mark_circle()
            .encode(x=alt.X(registration_date_column, title=x_axis), y=alt.Y(registration_count_column, title=y_axis))
            .configure_title(fontSize=16)
            .interactive()
        )
    else:
        # Default is the line chart
        c = (
            alt.Chart(chart_df, title=alt.Title(
                chart_title, subtitle=sub_title))
            .mark_line()
            .encode(x=alt.X(registration_date_column, title=x_axis), y=alt.Y(registration_count_column, title=y_axis))
            .configure_title(fontSize=16)
            .interactive()
        )

    return c


# Configure the page to use the wide mode
st.set_page_config(layout="wide")

# Header
st.title("LFX Event Registrations Report :rocket:")
st.write("Event registration data from Cvent or RegFox.")
st.divider()

# Get the current credentials
# session = get_active_session()

with st.container():
    # Filter by text
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
        st.write(
            ':exclamation: :red[Invalid characters in search field. Do not include quotes.]')
        event_name_filter = ''
    st.divider()

with st.container():
    st.write('#### Matching Events')
    if event_name_filter and len(event_name_filter) > 2:
        # Distinct events based on filter
        distinct_events_query = f"""
            SELECT DISTINCT {event_name_column}
            FROM {table_name}
            WHERE event_name ilike '%{event_name_filter}%'
            ORDER BY event_name;
        """
        event_name_df: pd.DataFrame = execute_query_pandas(conn, 
            distinct_events_query)
        # Print each value in the column
        num_filtered_events = len(event_name_df)
        if num_filtered_events > 0:
            # event_name_list = [event_name for event_name in event_name_df[event_name_column]]
            # options = st.multiselect("", event_name_list, event_name_list)
            if num_filtered_events == 1:
                st.write(f'{num_filtered_events} match')
            else:
                st.write(
                    f'{num_filtered_events} matches - update the event name above to refine your search')
            for value in event_name_df[event_name_column]:
                st.write(f'- {value}')
        else:
            st.write('No matching events. Search for an event name above.')
    else:
        st.write('Search for an event name above.')

    st.divider()

with st.container():
    st.write('#### Chart')
    if event_name_filter and len(event_name_filter) > 2:
        # The chart query
        line_chart_query = f"""
            SELECT {registration_date_column}, COUNT(*) AS registration_count, {event_name_column}
            FROM {table_name}
            WHERE event_name ilike '%{event_name_filter}%'
            GROUP BY {registration_date_column}, {event_name_column}
            ORDER BY {registration_date_column};
        """

        event_details_query = f"""
            SELECT PROJECT_NAME, EVENT_NAME, TO_CHAR(DATE(EVENT_START_DATE), 'MMMM DD, YYYY') AS EVENT_START_DATE, TO_CHAR(DATE(EVENT_END_DATE), 'MMMM DD, YYYY') AS EVENT_END_DATE
            FROM {event_table_name}
            WHERE event_name ilike '%{event_name_filter}%'
        """
        # Query and create a data frame containing the results
        chart_df: pd.DataFrame = execute_query_pandas(conn, line_chart_query)

        # Filtering safely in Python
        chart_df.drop(columns=event_name_column, inplace=True)

        # Plotting the data
        if not chart_df.empty:
            chart_selection: Optional[str] = st.selectbox(
                'Select chart style:', options=chart_types, index=0)
            chart_title = f'Event Registrations - (Includes {
                num_filtered_events} Events)'
            sub_title = ''
            if num_filtered_events == 1:
                # Grab the start/end date for this single event
                event_df: pd.DataFrame = execute_query_pandas(conn, 
                    event_details_query)
                if not event_df.empty:
                    # st.write(event_df)
                    chart_title = f'Event Registrations - {
                        event_name_df[event_name_column][0]}'
                    sub_title = f'Event Dates: {
                        event_df["EVENT_START_DATE"][0]} - {event_df["EVENT_END_DATE"][0]}'
            c: alt.Chart = build_chart(
                chart_df, chart_selection, chart_title, sub_title)
            st.altair_chart(c, use_container_width=True)
        else:
            st.write("No data available for the selected event.")
    else:
        st.write('Search for an event name above.')

    st.divider()

with st.container():
    st.write('#### Table Data')

    if event_name_filter and len(event_name_filter) > 2:

        # Show the table and download filters
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            speaker_filter = st.radio(
                "Speaker Filter", [opt_show_all_text, is_speaker_text, is_not_speaker_text])
        with col2:
            lf_member_filter = st.radio("LF Member Filter", [
                                        opt_show_all_text, is_lf_member_text, is_not_lf_member_text])
        with col3:
            project_member_filter = st.radio("Event Project Member Filter", [
                                             opt_show_all_text, is_project_member_text, is_not_project_member_text])
        with col4:
            opt_in_lf_news = st.radio("Opt-In Filter for LF News Announcements", [
                                      opt_show_all_text, opt_in_only_txt, opt_out_only_txt])
        with col5:
            opt_in_tnc_promos = st.radio(
                "Opt-In Filter for T&C Promotions", [opt_show_all_text, opt_in_only_txt, opt_out_only_txt])

        # Query the table
        # t = session.table(table_name)
        # The table query
        table_query = f"""
            SELECT *
            FROM {table_name}
            WHERE event_name ilike '%{event_name_filter}%'
            ORDER BY {registration_date_column};
        """

        df: pd.DataFrame = execute_query_pandas(conn, table_query)

        # Remove a few of the ID columns - not needed in the final report
        df.drop(columns=[registration_id_col, project_id_col,
                company_id_col], inplace=True)

        # Filter out rows where the TITLE column contains the word 'test' (case insensitive)
        df_filtered = df[~df[user_title_column].str.contains(
            'test', case=False, na=False)]

        if speaker_filter != opt_show_all_text:
            b = speaker_filter == is_speaker_text
            df_filtered = df_filtered[df[is_speaker_col] == b]
        if lf_member_filter != opt_show_all_text:
            b = lf_member_filter == is_lf_member_text
            df_filtered = df_filtered[df[is_lf_member_col] == b]
        if project_member_filter != opt_show_all_text:
            b = project_member_filter == is_project_member_text
            df_filtered = df_filtered[df[is_project_member_col] == b]
        if opt_in_lf_news != opt_show_all_text:
            b = opt_in_lf_news == opt_in_only_txt
            df_filtered = df_filtered[df[opt_in_lf_news_col] == b]
        if opt_in_tnc_promos != opt_show_all_text:
            b = opt_in_tnc_promos == opt_in_only_txt
            df_filtered = df_filtered[df[opt_in_tnc_promos_col] == b]

        # Convert DataFrame to CSV and then encode to string
        output = io.StringIO()
        # You can set index=True if you want to keep the DataFrame index
        df_filtered.to_csv(output, index=True)
        csv = output.getvalue()

        # Add the download button to trigger the data download.
        st.download_button(
            label=":arrow_down: :exclamation: Download data as CSV :exclamation: :arrow_down:",
            data=csv,
            # file_name=f"{event_name_selection}_data.csv",
            file_name="event_registration_data.csv",
            mime='text/csv',
            on_click=download_clicked,
            args=(event_name_filter,),
        )
        st.markdown(
            (
                ":exclamation: _This information contains confidential data protected under The Linux Foundation’s Privacy Policy. "
                "By downloading this information, you commit that (1) you will use it solely for legitimate purposes authorized by "
                "our Privacy Policy; and (2) you will handle it with the highest level of confidentiality and care. "
                "Unauthorized use, distribution, or disclosure of this data is strictly prohibited._"
            )
        )

        # Display data in a table
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.write('Search for an event name above.')

    st.divider()

with st.container():
    # Ensure the audit table is created
    create_audit_table()
    # Make a note about the user using/loading the application
    add_audit_record(audit_type_load_app)
