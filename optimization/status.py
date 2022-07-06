import streamlit as st


class Status:
    def __init__(self):
        self.status = st.empty()

    def update(self, text, *, type="info"):
        getattr(self.status, type)(text)
