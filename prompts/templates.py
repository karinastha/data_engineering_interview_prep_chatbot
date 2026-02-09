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
- Answer based on the <context> when relevant, using [Source N] citations for each reference
- Number each unique context document as [Source 1], [Source 2], etc.
- If context doesn't cover the topic, use your general knowledge but mention it
- Be concise and interview-focused
- Include practical examples when helpful
- End with a "📖 Sources Used:" section listing all referenced sources

Your response:"""
