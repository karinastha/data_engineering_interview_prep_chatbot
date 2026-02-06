"""
Text Processing Utilities

Helper functions for processing text content, particularly for
fixing markdown formatting issues in Streamlit rendering.
"""

import re
from typing import Optional


def post_process_markdown(text: str) -> str:
    """
    Fix markdown formatting for proper Streamlit rendering.
    
    Streamlit's st.markdown() requires double newlines (\\n\\n) for paragraph 
    breaks, but LLMs often output single newlines. This function ensures
    proper formatting.
    
    Args:
        text: Raw markdown text from LLM
        
    Returns:
        Fixed markdown with proper paragraph breaks
    """
    if not text:
        return text
    
    # Ensure blank line before headers (h1-h6)
    text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
    
    # Ensure blank line after headers
    text = re.sub(r'(#{1,6}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', text)
    
    # Ensure blank line before code blocks
    text = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', text)
    
    # Ensure blank line after code blocks
    text = re.sub(r'(```)\n([^\n`])', r'\1\n\n\2', text)
    
    # Ensure blank line before lists (bullet or numbered)
    # Only if previous line isn't already a list item or blank
    text = re.sub(r'([^\n\-\*\d\s])\n([\-\*]\s|\d+\.\s)', r'\1\n\n\2', text)
    
    # Ensure blank line after lists when transitioning to non-list content
    # Match list item followed by non-list, non-blank line
    text = re.sub(r'([\-\*]\s[^\n]+)\n([^\-\*\d\n\s])', r'\1\n\n\2', text)
    text = re.sub(r'(\d+\.\s[^\n]+)\n([^\-\*\d\n\s])', r'\1\n\n\2', text)
    
    # Ensure spacing around emoji headers/markers (common in our responses)
    # Match common emojis used in responses: 📚💡🚀🟢🟡🔴 and any emoji
    # Expanded Unicode ranges to cover all emoji categories
    emoji_pattern = r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FAFF]'
    
    # FIRST: Handle inline emojis (same line) - insert newline before emoji
    # This handles cases like "Question? 📚 Definition:" all on one line
    # Match: non-newline, optional whitespace, emoji -> insert newline before emoji
    text = re.sub(rf'([^\n]) +({emoji_pattern})', r'\1\n\n\2', text)
    
    # Then handle single newline before emoji -> double newline
    text = re.sub(rf'([^\n])\n({emoji_pattern})', r'\1\n\n\2', text)
    
    # Ensure blank line AFTER emoji-prefixed lines (before the next emoji or text)
    text = re.sub(rf'({emoji_pattern}[^\n]+)\n({emoji_pattern})', r'\1\n\n\2', text)
    
    # Ensure blank line before **Q:** or **Question** patterns (interview questions)
    text = re.sub(r'([^\n])\n(\*?\*?Q[:\.])', r'\1\n\n\2', text)
    
    # Ensure blank line before numbered question patterns (1. Q: or 1. **Q:)
    text = re.sub(r'([^\n])\n(\d+\.\s*\*?\*?Q[:\.])', r'\1\n\n\2', text)
    
    # Ensure blank line before bold section headers like **Definition:** or **Example:**
    text = re.sub(r'([^\n])\n(\*\*[A-Z][a-z]+[:\*])', r'\1\n\n\2', text)
    
    # Clean up any triple+ newlines (normalize to double)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def fix_mermaid_syntax(mermaid_code: str) -> str:
    """
    Fix common LLM-generated mermaid syntax errors.
    
    Common issues:
    - Space before brackets: `A [Label]` should be `A[Label]`
    - Space before parentheses: `A (Label)` should be `A(Label)`
    - Missing quotes in labels with special chars
    - Invalid arrow syntax
    - Cylinder shape spacing: `[( Database )]` should be `[(Database)]`
    
    Args:
        mermaid_code: Raw mermaid code from LLM
        
    Returns:
        Fixed mermaid code
    """
    # Fix space before square brackets: `A [Label]` -> `A[Label]`
    mermaid_code = re.sub(r'(\w)\s+\[', r'\1[', mermaid_code)
    
    # Fix space before parentheses: `A (Label)` -> `A(Label)`
    mermaid_code = re.sub(r'(\w)\s+\(', r'\1(', mermaid_code)
    
    # Fix space before curly braces: `A {Label}` -> `A{Label}`
    mermaid_code = re.sub(r'(\w)\s+\{', r'\1{', mermaid_code)
    
    # Fix space after opening brackets: `[ Label]` -> `[Label]`
    mermaid_code = re.sub(r'\[\s+', '[', mermaid_code)
    mermaid_code = re.sub(r'\(\s+', '(', mermaid_code)
    mermaid_code = re.sub(r'\{\s+', '{', mermaid_code)
    
    # Fix space before closing brackets: `[Label ]` -> `[Label]`
    mermaid_code = re.sub(r'\s+\]', ']', mermaid_code)
    mermaid_code = re.sub(r'\s+\)', ')', mermaid_code)
    mermaid_code = re.sub(r'\s+\}', '}', mermaid_code)
    
    # CRITICAL: Replace parentheses INSIDE square brackets with dashes
    # `[Label(stuff)]` breaks mermaid - parens are shape syntax
    # Convert to `[Label - stuff]` or `[Label: stuff]`
    def fix_parens_in_brackets(match):
        content = match.group(1)
        # Replace ( with " - " and ) with nothing
        content = re.sub(r'\s*\(', ' - ', content)
        content = re.sub(r'\)\s*', '', content)
        return f'[{content}]'
    
    mermaid_code = re.sub(r'\[([^\]]*\([^\]]*\)[^\]]*)\]', fix_parens_in_brackets, mermaid_code)
    
    # Fix double spaces
    mermaid_code = re.sub(r'  +', ' ', mermaid_code)
    
    # Fix arrow with spaces: `-- >` -> `-->`
    mermaid_code = re.sub(r'--\s+>', '-->', mermaid_code)
    mermaid_code = re.sub(r'-\.\s+->', '-.->', mermaid_code)
    mermaid_code = re.sub(r'-\.\s+>', '-.>', mermaid_code)
    
    # Ensure proper line endings
    mermaid_code = mermaid_code.strip()
    
    return mermaid_code


def extract_mermaid_blocks(content: str) -> list[tuple[str, int, int]]:
    """
    Extract mermaid diagram blocks from markdown content.
    
    Args:
        content: Markdown text potentially containing mermaid blocks
        
    Returns:
        List of tuples: (mermaid_code, start_index, end_index)
    """
    pattern = r'```mermaid\n(.*?)```'
    matches = []
    
    for match in re.finditer(pattern, content, re.DOTALL):
        mermaid_code = match.group(1).strip()
        matches.append((mermaid_code, match.start(), match.end()))
    
    return matches


def split_content_with_mermaid(content: str) -> list[dict]:
    """
    Split content into markdown and mermaid sections for mixed rendering.
    
    Args:
        content: Markdown text with potential mermaid blocks
        
    Returns:
        List of dicts with 'type' ('markdown' or 'mermaid') and 'content'
    """
    mermaid_blocks = extract_mermaid_blocks(content)
    
    if not mermaid_blocks:
        return [{"type": "markdown", "content": content}]
    
    parts = []
    last_end = 0
    
    for mermaid_code, start, end in mermaid_blocks:
        # Add markdown before this mermaid block
        if start > last_end:
            markdown_part = content[last_end:start].strip()
            if markdown_part:
                parts.append({"type": "markdown", "content": markdown_part})
        
        # Add mermaid block with syntax fixes applied
        fixed_mermaid = fix_mermaid_syntax(mermaid_code)
        parts.append({"type": "mermaid", "content": fixed_mermaid})
        last_end = end
    
    # Add remaining markdown after last mermaid block
    if last_end < len(content):
        remaining = content[last_end:].strip()
        if remaining:
            parts.append({"type": "markdown", "content": remaining})
    
    return parts
