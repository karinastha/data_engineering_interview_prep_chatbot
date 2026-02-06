"""Test mermaid parsing and rendering."""

from utils.text_processing import split_content_with_mermaid, fix_mermaid_syntax

# Sample LLM output with typical issues
sample = '''Here's an ETL architecture:

```mermaid
graph TD
    A [Data Sources] --> B [Extract]
    B --> C [Transform]
    C --> D [Load]
    D --> E [Data Warehouse]
    
    subgraph Sources
        A1 [API]
        A2 [Database]
        A3 [Files]
    end
    
    A1 --> A
    A2 --> A
    A3 --> A
```

This shows the flow.
'''

print("=" * 60)
print("TESTING MERMAID EXTRACTION + SYNTAX FIX")
print("=" * 60)

parts = split_content_with_mermaid(sample)
for p in parts:
    print(f"\n--- {p['type'].upper()} ---")
    print(p['content'])

print("\n" + "=" * 60)
print("TESTING SPECIFIC SYNTAX FIXES")
print("=" * 60)

test_cases = [
    "A [Label] --> B [Label]",  # Space before bracket
    "A (Round) --> B (Round)",  # Space before paren
    "A {Diamond} --> B {Diamond}",  # Space before brace
    "A-- >B",  # Space in arrow
    "A -.-> B [Dashed]",  # Mixed issues
    "A[( Database )]",  # Spaces in cylinder shape
    "A[ Label with spaces ]",  # Spaces inside brackets
    "subgraph Sources[ Source Layer ]",  # Subgraph with spaces
]

for tc in test_cases:
    fixed = fix_mermaid_syntax(tc)
    status = "✓" if tc != fixed else "="
    print(f"{status} '{tc}' -> '{fixed}'")
