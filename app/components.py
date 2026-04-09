"""UI components for the Streamlit application."""

import streamlit as st

from app.session import add_message, reset_conversation
from config.topics import TOPICS, get_topic_display_string
from utils.text_processing import post_process_markdown, split_content_with_mermaid

# Content preview length for source display
_SOURCE_PREVIEW_LENGTH = 300


def render_header() -> None:
    """Render application header."""
    header_style = (
        "text-align: center; padding: 1rem; "
        "background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); "
        "border-radius: 10px; margin-bottom: 2rem;"
    )
    st.markdown(
        f"""
    <div style='{header_style}'>
        <h1 style='color: white; margin: 0;'>💼 DATA ENGINEERING INTERVIEW PREP</h1>
        <p style='color: #f0f0f0; margin: 0.5rem 0 0 0;'>Powered by Amazon Nova Lite & LangChain</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render sidebar with info and controls."""
    with st.sidebar:
        st.markdown("### 📚 About")
        st.markdown(
            """
        Prepare for Data Engineering interviews with:
        - Practice questions at all levels
        - Leapfrog competency framework
        - Context-aware responses
        """,
        )

        st.markdown("---")

        st.markdown("### 🎯 Topics")
        for topic in TOPICS:
            st.markdown(f"{topic.display_name}")

        st.markdown("---")

        st.markdown("### 💡 Example Questions")
        st.markdown(
            """
        - "Give me Python interview questions"
        - "Explain SQL joins with examples"
        - "What are ETL best practices?"
        - "More scenario-based questions"
        """,
        )

        st.markdown("---")

        if st.button("🔄 Reset Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

        st.markdown("---")
        st.caption(f"💬 Messages: {len(st.session_state.messages)}")


def render_welcome() -> None:
    """Display welcome message."""
    topic_display = get_topic_display_string()

    welcome = f"""👋 **Welcome! I'm here to help you prepare for Data Engineering interviews.**

I can help with:
- ✅ Practice interview questions (Entry/Mid/Advanced levels)
- ✅ Technical concepts with examples
- ✅ Leapfrog competency-based preparation

**Topics:** {topic_display}

**Just ask me anything!** For example:
- "Give me Python interview questions"
- "Explain window functions in SQL"
- "What should I know about database indexing?"
"""
    add_message("assistant", welcome)


def render_content_with_mermaid(content: str) -> None:
    """
    Render content that may contain mermaid diagrams.

    Splits content into markdown and mermaid parts,
    rendering each appropriately with proper formatting.
    """
    parts = split_content_with_mermaid(content)

    for part in parts:
        if part["type"] == "markdown":
            formatted_content = post_process_markdown(part["content"])
            st.markdown(formatted_content)
        elif part["type"] == "mermaid":
            try:
                import streamlit_mermaid as stmd  # noqa: PLC0415

                stmd.st_mermaid(part["content"])
            except ImportError:
                # Fallback to code block if streamlit_mermaid not installed
                st.code(part["content"], language="mermaid")


def render_sources_used(sources: list) -> None:
    """
    Display retrieved vector database chunks as expandable sources.

    Shows users exactly which documents were used to generate the answer.
    """
    if not sources:
        return

    with st.expander(
        f"📖 **Sources Used** ({len(sources)} chunks from vector database)",
        expanded=False,
    ):
        for i, source in enumerate(sources, 1):
            with st.container():
                col1, col2 = st.columns([1, 4])

                with col1:
                    st.metric(
                        label=f"Source {i}",
                        value=f"{source.score:.0%}",
                        help="Relevance score from vector similarity search",
                    )

                with col2:
                    st.write(f"**{source.topic}** - {source.subtopic}")
                    st.caption(f"📄 {source.metadata.get('source', 'Unknown file')}")

                    if hasattr(source, "content") and source.content:
                        preview = (
                            source.content[:_SOURCE_PREVIEW_LENGTH] + "..."
                            if len(source.content) > _SOURCE_PREVIEW_LENGTH
                            else source.content
                        )
                        st.code(preview, language=None)

                if i < len(sources):
                    st.divider()


def render_project_resources(project_types: list[str]) -> None:
    """
    Display download buttons for project assignment doc and dataset.

    Takes an explicit list of project types (e.g. ["ETL"]) determined by
    the preprocessing LLM, rather than inferring from source metadata.
    """
    if not project_types:
        return

    from config.settings import get_config

    config = get_config()
    resources = config.data.project_resources
    projects_dir = config.project_root / config.data.projects_directory

    for project_type in project_types:
        if project_type in resources:
            _render_resource_buttons(resources[project_type], projects_dir, project_type)


_resource_button_counter = 0


def _render_resource_buttons(info: dict, projects_dir, project_type: str) -> None:
    """Render download + Drive link buttons for a single project."""
    global _resource_button_counter
    _resource_button_counter += 1

    file_path = projects_dir / info["assignment_file"]

    st.markdown(f"**📥 {info['title']} — Resources**")
    col1, col2 = st.columns(2)
    with col1:
        if file_path.exists():
            st.download_button(
                "📄 Assignment Document",
                data=file_path.read_text(encoding="utf-8"),
                file_name=info["assignment_file"],
                mime="text/markdown",
                key=f"download_{project_type}_{_resource_button_counter}",
            )
    with col2:
        st.link_button(
            "📊 Dataset (Google Drive)",
            info["dataset_drive_url"],
        )


def render_chat_messages() -> None:
    """Render all chat messages with mermaid support."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_content_with_mermaid(message["content"])
            if message.get("sources"):
                render_sources_used(message["sources"])
            if message.get("project_resource_types"):
                render_project_resources(message["project_resource_types"])
