"""
Markdown Rendering Experiments for Streamlit
============================================
Testing two approaches:
1. CSS fixes (inject custom CSS)
2. Post-processing (fix LLM output before rendering)
"""

import streamlit as st

# Sample LLM outputs that typically break in Streamlit
SAMPLE_OUTPUTS = {
    "missing_newlines": """Here's what you need to know:
**Key Points:**
- Point 1: This is important
- Point 2: Also important
**Code Example:**
```python
def example():
    return "hello"
```
**Summary:** Remember these concepts.""",

    "code_block_issue": """To implement this:
```sql
SELECT * FROM users
WHERE active = true;
```The results will show...""",

    "list_formatting": """Common approaches:
1. First approach
2. Second approach
3. Third approach
Each has trade-offs.""",

    "headers_squished": """# Main Topic
## Subtopic
Here's the content.
### Details
More details here."""
}


def test_css_approach():
    """Approach 1: CSS fixes"""
    st.subheader("🎨 Approach 1: CSS Fixes")
    
    css = """
    <style>
    /* Force proper spacing for markdown elements */
    .stMarkdown p {
        margin-bottom: 1em !important;
    }
    .stMarkdown ul, .stMarkdown ol {
        margin-top: 0.5em !important;
        margin-bottom: 1em !important;
    }
    .stMarkdown li {
        margin-bottom: 0.25em !important;
    }
    .stMarkdown pre {
        margin: 1em 0 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 1em !important;
        margin-bottom: 0.5em !important;
    }
    .stMarkdown code {
        padding: 0.2em 0.4em !important;
        background-color: rgba(175, 184, 193, 0.2) !important;
        border-radius: 3px !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    for name, output in SAMPLE_OUTPUTS.items():
        st.write(f"**Test: {name}**")
        st.markdown(output)
        st.divider()


def post_process_markdown(text: str) -> str:
    """Approach 2: Post-process LLM output to fix markdown formatting"""
    import re
    
    lines = text.split('\n')
    processed = []
    
    for i, line in enumerate(lines):
        processed.append(line)
        
        # Add blank line after headers if next line isn't blank
        if line.startswith('#') and i + 1 < len(lines) and lines[i + 1].strip():
            processed.append('')
        
        # Add blank line before headers if previous line isn't blank
        if line.startswith('#') and i > 0 and processed[-2].strip():
            processed.insert(-1, '')
        
        # Add blank line after code blocks if next line isn't blank
        if line.strip() == '```' and i + 1 < len(lines) and lines[i + 1].strip():
            # Check if this is a closing ``` (look backwards for opening)
            code_block_count = sum(1 for l in lines[:i+1] if l.strip().startswith('```'))
            if code_block_count % 2 == 0:  # Closing block
                processed.append('')
        
        # Add blank line before lists if previous line isn't blank and isn't a list
        if (line.strip().startswith('- ') or re.match(r'^\d+\.', line.strip())):
            if i > 0 and lines[i-1].strip() and not lines[i-1].strip().startswith('-') and not re.match(r'^\d+\.', lines[i-1].strip()):
                processed.insert(-1, '')
    
    return '\n'.join(processed)


def post_process_markdown_v2(text: str) -> str:
    """Simpler post-processing: ensure double newlines around block elements"""
    import re
    
    # Ensure blank line before headers
    text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
    
    # Ensure blank line after headers
    text = re.sub(r'(#{1,6}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', text)
    
    # Ensure blank line before code blocks
    text = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', text)
    
    # Ensure blank line after code blocks
    text = re.sub(r'(```)\n([^\n`])', r'\1\n\n\2', text)
    
    # Ensure blank line before lists (if not already in a list)
    text = re.sub(r'([^\n\-\d])\n([\-\*]\s|\d+\.\s)', r'\1\n\n\2', text)
    
    # Ensure blank line after lists (before non-list content)
    text = re.sub(r'([\-\*]\s[^\n]+|\d+\.\s[^\n]+)\n([^\-\*\d\n])', r'\1\n\n\2', text)
    
    # Clean up any triple+ newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def test_post_processing_approach():
    """Approach 2: Post-processing"""
    st.subheader("🔧 Approach 2: Post-Processing")
    
    for name, output in SAMPLE_OUTPUTS.items():
        st.write(f"**Test: {name}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("*Before (raw):*")
            st.markdown(output)
        
        with col2:
            st.write("*After (post-processed):*")
            processed = post_process_markdown_v2(output)
            st.markdown(processed)
        
        st.divider()


def test_combined():
    """Approach 3: Both CSS + Post-processing"""
    st.subheader("🚀 Approach 3: CSS + Post-Processing Combined")
    
    # Apply CSS
    css = """
    <style>
    .combined-test p { margin-bottom: 1em !important; }
    .combined-test pre { margin: 1em 0 !important; }
    .combined-test ul, .combined-test ol { margin: 0.5em 0 1em 0 !important; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    for name, output in SAMPLE_OUTPUTS.items():
        st.write(f"**Test: {name}**")
        processed = post_process_markdown_v2(output)
        st.markdown(f'<div class="combined-test">{processed}</div>', unsafe_allow_html=True)
        st.divider()


def main():
    st.title("🧪 Markdown Rendering Experiments")
    st.write("Testing fixes for broken markdown in Streamlit")
    
    tab1, tab2, tab3 = st.tabs(["CSS Only", "Post-Processing Only", "Combined"])
    
    with tab1:
        test_css_approach()
    
    with tab2:
        test_post_processing_approach()
    
    with tab3:
        test_combined()
    
    st.subheader("📊 Verdict")
    st.info("""
    **Observations to make:**
    1. Does CSS fix the spacing issues?
    2. Does post-processing fix the spacing issues?
    3. Which approach handles code blocks better?
    4. Which approach handles lists better?
    5. Is combined approach needed or is one sufficient?
    """)


if __name__ == "__main__":
    main()
