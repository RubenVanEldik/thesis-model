from datetime import datetime, timedelta
import streamlit as st


class Status:
    def __init__(self):
        self.status = st.empty()
        self.text = None
        self.last_updated_at = datetime.now()

    def update(self, text, *, type="info", timestamp=None):
        # Update the status if there is no timestamp, or the text is different, or its the first timestamp of the month
        if timestamp is None:
            getattr(self.status, type)(text)
            self.text = text
            self.last_updated_at = datetime.now()
        elif self.text != text or (datetime.now() - self.last_updated_at) > timedelta(seconds=0.5):
            getattr(self.status, type)(f"{text} ({timestamp.strftime('%B %Y')})")
            self.text = text
            self.last_updated_at = datetime.now()
