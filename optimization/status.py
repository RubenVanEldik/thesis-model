import streamlit as st


class Status:
    def __init__(self):
        self.status = st.empty()

    def update(self, text, *, type="info"):
        if st._is_running_with_streamlit:
            getattr(self.status, type)(text)
        else:
            print(text)
