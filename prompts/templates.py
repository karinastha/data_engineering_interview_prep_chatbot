"""Q&A prompt templates."""

QA_PROMPT_TEMPLATE = """<context>
{context}
</context>

<conversation_history>
{history}
</conversation_history>

<user_question>
{question}
</user_question>

Instructions:
- Answer based on the <context> provided above
- Use inline [Source N] citations throughout your answer (e.g., "According to [Source 1], CDC allows... [Source 2] mentions that...")
- Each [Source N] in the context gets its own number: [Source 1], [Source 2], [Source 3], etc.
- When MULTIPLE sources are provided, try to incorporate information from ALL of them to give a comprehensive answer
- If you use information from a source, cite it with [Source N]
- If context doesn't fully cover the topic, supplement with general knowledge (but prioritize context)
- Be concise and interview-focused with practical examples
- DO NOT create a "📖 Sources Used:" section at the end - the UI displays all sources automatically
- IMPORTANT: If the context contains project information (ETL_INSIGHTS.md or ELT_DBT.md), provide detailed project specifications, NOT general concepts

Your response:"""
