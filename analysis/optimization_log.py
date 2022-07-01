import streamlit as st

import utils
import validate


def optimization_log(run_name, resolution):
    """
    Show the optimization log
    """
    assert validate.is_string(run_name)
    assert validate.is_resolution(resolution)

    st.title("📜 Optimization log")

    # Read the log
    log = utils.read_text(f"./output/{run_name}/{resolution}/log.txt")

    # Display the log as a code block
    st.code(log)
