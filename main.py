"""Main Streamlit application entry point."""

import streamlit as st

from app.components import (
    render_chat_messages,
    render_header,
    render_sidebar,
    render_welcome,
)
from app.handlers import handle_message_streaming
from app.session import add_message, init_session_state
from utils.logging import setup_logging

# Setup logging
setup_logging()

# Page configuration
st.set_page_config(
    page_title="DE Interview Prep Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main application entry point."""
    init_session_state()

    render_header()
    render_sidebar()

    if not st.session_state.messages:
        render_welcome()

    render_chat_messages()

    if prompt := st.chat_input("Ask me anything about data engineering interviews..."):
        add_message("user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        handle_message_streaming(prompt)

        st.rerun()


if __name__ == "__main__":
    main()
