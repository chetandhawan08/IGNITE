try:
    from groq import Groq
except ImportError:
    Groq = None

from .config import GROQ_API_KEY, last_dataset_context

client = Groq(api_key=GROQ_API_KEY) if Groq is not None and GROQ_API_KEY else None


def ai_summarize(summary_dict):
    if client is None:
        if Groq is not None and not GROQ_API_KEY:
            return (
                "AI summarization is unavailable because GROQ_API_KEY is not set. "
                "Add it to backend/.env or your environment."
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
        if Groq is not None and not GROQ_API_KEY:
            return (
                "AI chat is unavailable because GROQ_API_KEY is not set. "
                "Add it to backend/.env or your environment."
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
