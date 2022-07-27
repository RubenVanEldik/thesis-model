import streamlit as st


class Status:
    def __init__(self):
        self.status = st.empty()

    def update(self, text, *, status_type="info"):
        getattr(self.status, status_type)(text)
