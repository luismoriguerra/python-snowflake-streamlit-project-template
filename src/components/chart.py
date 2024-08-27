import altair as alt
import pandas as pd
from typing import Optional
from utils.config import REGISTRATION_DATE_COLUMN, REGISTRATION_COUNT_COLUMN

def build_chart(
    chart_df: pd.DataFrame, 
    chart_type: Optional[str], 
    chart_title: str, 
    sub_title: str = '', 
    x_axis: str = 'Registration Date', 
    y_axis: str = '# Registrations'
) -> alt.Chart:
    base = alt.Chart(chart_df, title=alt.Title(chart_title, subtitle=sub_title))

    if chart_type == 'Bar Chart':
        c = base.mark_bar()
    elif chart_type == 'Mark Circles':
        c = base.mark_circle()
    else:
        c = base.mark_line()

    c = c.encode(
        x=alt.X(REGISTRATION_DATE_COLUMN, title=x_axis),
        y=alt.Y(REGISTRATION_COUNT_COLUMN, title=y_axis)
    ).configure_title(fontSize=16).interactive()

    return c