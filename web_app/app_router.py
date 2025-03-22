import streamlit as st

main_page = st.Page("app_views/app.py")
view_page = st.Page("app_views/view_page.py")

router = st.navigation([main_page, view_page], position="hidden")

router.run()