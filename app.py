from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="Streamlit Modular Template",
    layout="wide",
)

_assets = Path(__file__).parent / "assets"
st.logo(str(_assets / "logo.png"), icon_image=str(_assets / "logo_sm.svg"))

menu = {
    "Help": [
        st.Page("pages/description.py", title="APP Description", icon=":material/description:",),
    ],
    "Jobs": [
        st.Page("pages/jobs_and_pipelines/jobs_run_daily.py", title="Jobs Runs (Daily)", icon=":material/grid_view:"),
    ],
    "Settings": [
        st.Page("pages/settings/settings_page.py", title="Settings", icon=":material/settings:"),
    ],
}

st.markdown(
    """<style>
    hr { margin-top: 0.25rem !important; margin-bottom: 0.25rem !important; }
    [data-testid="stMarkdownContainer"] p { margin: 0 !important; }
    </style>""",
    unsafe_allow_html=True,
)

pg = st.navigation(menu)
pg.run()
