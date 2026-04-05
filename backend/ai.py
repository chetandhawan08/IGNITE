try:
    from groq import Groq
except ImportError:
    Groq = None

import os

from .config import GROQ_API_KEY, last_dataset_context


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if Groq is None or not api_key:
        return None
    return Groq(api_key=api_key)


def ai_summarize(summary_dict):
    client = get_groq_client()
    if client is None:
        if Groq is not None and not (os.getenv("GROQ_API_KEY") or GROQ_API_KEY):
            return (
                "AI summarization is unavailable because GROQ_API_KEY is not set. "
                "Set it in your environment, or in Render's Environment settings for the deployed app."
            )
        return (
            "AI summarization is unavailable because the Groq SDK is not installed. "
            "Install it with: pip install groq"
        )

    prompt = f"""
You are an expert data scientist analyzing time-series data.

Analyze this dataset summary:
{summary_dict}

Provide:
- Key trends
- Anomalies interpretation
- Scientific insights
- Short conclusion
"""
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )
    return completion.choices[0].message.content


def ai_chat(user_message, conversation_history):
    client = get_groq_client()
    dataset_context = ""
    if last_dataset_context["data"] is not None:
        dataset_context = f"""
The user has loaded a dataset. Here is its summary for context:
Source: {last_dataset_context['source']}
Summary: {last_dataset_context['data']}

Use this as context when answering questions about the data.
"""

    system_prompt = f"""You are an expert AI assistant specializing in time-series analysis,
anomaly detection, and exoplanet science. You help users understand their datasets,
interpret anomalies, and explain astrophysics concepts clearly.
{dataset_context}"""

    if client is None:
        if Groq is not None and not (os.getenv("GROQ_API_KEY") or GROQ_API_KEY):
            return (
                "AI chat is unavailable because GROQ_API_KEY is not set. "
                "Set it in your environment, or in Render's Environment settings for the deployed app."
            )
        return (
            "AI chat is unavailable because the Groq SDK is not installed. "
            "Install it with: pip install groq"
        )

    messages = [{"role": "system", "content": system_prompt}] + conversation_history + [
        {"role": "user", "content": user_message}
    ]

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )
    return completion.choices[0].message.content
