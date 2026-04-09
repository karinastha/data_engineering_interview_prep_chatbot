"""Message handlers for the Streamlit application."""

import streamlit as st

from app.components import render_content_with_mermaid, render_project_resources, render_sources_used
from app.session import add_message, get_chat_service, get_history
from utils.text_processing import post_process_markdown


def handle_message_streaming(user_input: str) -> None:
    """
    Process user input with streaming response.

    Flow:
    1. Get conversation history
    2. Call chat service streaming (preprocess → retrieve → stream generate)
    3. Display tokens as they arrive (markdown only during stream)
    4. Re-render with mermaid support and show sources after completion
    """
    chat_service = get_chat_service()
    history = get_history()

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for chunk in chat_service.answer_stream(
            message=user_input,
            history=history,
        ):
            full_response += chunk
            response_placeholder.markdown(post_process_markdown(full_response) + "▌")

        response_placeholder.empty()
        render_content_with_mermaid(full_response)

        rag_response = chat_service.get_last_response()
        if rag_response and rag_response.sources:
            render_sources_used(rag_response.sources)
        if rag_response and rag_response.project_resource_types:
            render_project_resources(rag_response.project_resource_types)

    rag_response = chat_service.get_last_response()
    sources = rag_response.sources if rag_response else None
    project_resource_types = rag_response.project_resource_types if rag_response else None
    add_message("assistant", full_response, sources, project_resource_types)


def handle_message(user_input: str) -> None:
    """
    Process user input through RAG pipeline (non-streaming fallback).

    Simple flow:
    1. Get conversation history
    2. Call chat service (preprocess → retrieve → generate)
    3. Display response with sources
    """
    chat_service = get_chat_service()
    history = get_history()

    with st.spinner("🤔 Thinking..."):
        response = chat_service.answer(
            message=user_input,
            history=history,
        )

    with st.chat_message("assistant"):
        render_content_with_mermaid(response.content)
        if response.sources:
            render_sources_used(response.sources)
        if response.project_resource_types:
            render_project_resources(response.project_resource_types)

    add_message("assistant", response.content, response.sources, response.project_resource_types)
