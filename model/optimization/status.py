import streamlit as st


class Status:
    def __init__(self):
        self.status = st.empty()
        self.text = None

    def update(self, text, *, type="info", timestamp=None):
        # Update the status if there is no timestamp, or the text is different, or its the first timestamp of the month
        if timestamp is None:
            getattr(self.status, type)(text)
            self.text = text
        elif self.text != text or (timestamp.is_month_start and timestamp.hour == 0):
            getattr(self.status, type)(f"{text} ({timestamp.strftime('%B %Y')})")
            self.text = text
