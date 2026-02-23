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
- When MULTIPLE sources are provided, incorporate information from ALL of them to give a comprehensive answer
- If context says "No relevant information found" AND user is asking for interview questions, DO NOT generate questions - instead ask them to pick a topic (Python, SQL, Database, or ETL)
- For conceptual/explanatory questions, you may supplement with general knowledge if context is limited
- Be concise and interview-focused with practical examples
- Do NOT cite or reference source numbers in your answer - just use the information naturally
- IMPORTANT: If the context contains project information (ETL_INSIGHTS.md or ELT_DBT.md), provide detailed project specifications, NOT general concepts

Your response:"""  # noqa: E501
