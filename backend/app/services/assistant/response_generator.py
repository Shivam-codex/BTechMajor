"""
Conversational Municipal Assistant Response Generator.
Generates short, plain-language answers that any citizen can understand,
using Google GenAI SDK (gemini-2.5-flash) grounded strictly in retrieved municipal knowledge base chunks.
Falls back to local Ollama (gemma3:4b) and then to concise local templates if no API is configured or a call fails.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from backend.app.core.config import settings
from backend.app.services.retrieval.ranking import RetrievalResult

logger = logging.getLogger("smart_city_backend")


def format_conversational_fallback(
    query: str,
    retrieved_chunks: List[Any],
    intent_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Synthesizes a warm, articulate, Flipkart/Amazon-style customer support response
    purely from local deterministic knowledge and detected intent.
    Used when GEMINI_API_KEY is not set or when external API calls fail.
    """
    intent = intent_info.get("intent", "PROCEDURAL_QUERY") if intent_info else "PROCEDURAL_QUERY"
    category = intent_info.get("category") if intent_info else None
    dept = intent_info.get("department") if intent_info else None
    tracking_id = intent_info.get("tracking_id") if intent_info else None
    is_emergency = intent_info.get("is_emergency", False) if intent_info else False

    # 1. Greeting Intent
    if intent == "GREETING":
        return (
            "Hi! 👋 I'm the city civic assistant.\n\n"
            "I can help you:\n"
            "- Report a problem (power cut, water leak, pothole, garbage, street light)\n"
            "- Track a complaint\n"
            "- Check how long a fix takes\n\n"
            "What do you need help with?"
        )

    # 2. Tracking Intent
    if intent == "TRACK_STATUS":
        if tracking_id:
            return (
                f"To track **{tracking_id}**, tap the **Track Complaint** button below.\n\n"
                "Status flow: Submitted ➔ Assigned ➔ In Progress ➔ Resolved."
            )
        return (
            "Open **My Complaints** below to see all your complaints and their live status."
        )

    # 3. Out of Domain Intent (e.g., poetry, unrelated chit-chat)
    if intent == "OUT_OF_DOMAIN" or not retrieved_chunks:
        return (
            "I could not find sufficient information about this question in the "
            "Sample Municipal Knowledge Base. Please call the municipal helpline at "
            "1800-233-0001 (toll-free, 24/7)."
        )

    # 4. Grievance Filing & Procedural Inquiry
    top_chunk = retrieved_chunks[0]
    top_title = getattr(top_chunk, "title", None) or (top_chunk.get("title") if isinstance(top_chunk, dict) else "Municipal Guidelines")
    top_dept = getattr(top_chunk, "department", None) or (top_chunk.get("department") if isinstance(top_chunk, dict) else (dept or "Municipal Corporation"))
    top_text = getattr(top_chunk, "text", None) or (top_chunk.get("text") if isinstance(top_chunk, dict) else "")

    if intent == "LODGE_GRIEVANCE" and category:
        intro_phrase = f"Here's how to file your **{category}** complaint:"
    else:
        intro_phrase = f"Here's the city rule for **{category or 'civic services'}**:"

    body_parts = [
        intro_phrase,
        "",
        str(top_text).strip(),
    ]

    # Add a short filing hint
    if intent == "LODGE_GRIEVANCE":
        body_parts.append(
            "\nTap **Submit Grievance** below to file it. You only need the problem and the "
            "exact location (a landmark or street works). You'll get a tracking ID."
        )

    # Add a one-line emergency advisory if applicable
    if is_emergency or category == "Electricity":
        body_parts.append(
            "\n⚠️ If it's a live wire, sparking, or a fallen pole: stay away and call **1912** now."
        )

    body_parts.append(f"\n_Source: Sample Municipal Knowledge Base — {top_title} ({top_dept})._")

    return "\n".join(body_parts)


def format_deterministic_response(
    query: str,
    retrieved_chunks: List[Any],
    intent_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fallback response packager returning structured metadata and rich answer.
    """
    full_answer = format_conversational_fallback(query, retrieved_chunks, intent_info)

    sources_summary = []
    seen_docs = set()
    for chunk in retrieved_chunks:
        c_dict = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk
        doc_id = c_dict.get("document_id")
        if doc_id and doc_id not in seen_docs:
            sources_summary.append({
                "document_id": doc_id,
                "title": c_dict.get("title", ""),
                "category": c_dict.get("category", ""),
                "department": c_dict.get("department", ""),
                "score": round(float(c_dict.get("score", 0.0)), 4),
                "source": c_dict.get("source", ""),
            })
            seen_docs.add(doc_id)

    top_score = 0.0
    if retrieved_chunks:
        top_chunk = retrieved_chunks[0]
        top_score = getattr(top_chunk, "score", 0.0) if hasattr(top_chunk, "score") else top_chunk.get("score", 0.0)

    has_answer = bool(retrieved_chunks) or (intent_info and intent_info.get("intent") in ["GREETING", "TRACK_STATUS"])

    return {
        "answer": full_answer,
        "sources": sources_summary,
        "retrieved_chunks": [c.to_dict() if hasattr(c, "to_dict") else c for c in retrieved_chunks],
        "confidence": top_score,
        "has_answer": has_answer,
    }


def generate_ollama_response(
    user_prompt: str,
    system_instruction: str,
    model_name: Optional[str] = None,
) -> Optional[str]:
    """
    Synthesizes a fluent, local-first conversational response using locally hosted Ollama (e.g. gemma3:4b).
    Returns None if Ollama is unreachable, model is not pulled, or generation fails.
    """
    try:
        import httpx

        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        api_url = f"{base_url}/api/generate"
        target_model = model_name or settings.OLLAMA_VISION_MODEL or "gemma3:4b"

        payload = {
            "model": target_model,
            "system": system_instruction,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 200,
            },
        }

        with httpx.Client(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            resp = client.post(api_url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                ans_text = str(data.get("response", "")).strip()
                if ans_text:
                    if "Sample Municipal Knowledge Base" not in ans_text:
                        ans_text = f"{ans_text}\n\n_Source: Sample Municipal Knowledge Base._"
                    return ans_text
    except Exception as exc:
        logger.debug("Local Ollama assistant generation skipped/failed: %s", exc)
    return None


def generate_llm_response(
    question: str,
    retrieved_chunks: list,
    intent_info: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Synthesizes a fluent, articulate, ChatGPT/Gemini-style response.
    Tier 1: Google GenAI (Gemini) if GEMINI_API_KEY is configured.
    Tier 2: Local Ollama Gemma 3 (gemma3:4b) for zero-cost, private local generation.
    Tier 3: Rich deterministic conversational template generator.
    """
    clean_question = (question or "").strip()

    # Out of domain check
    if intent_info and intent_info.get("intent") == "OUT_OF_DOMAIN":
        return format_conversational_fallback(clean_question, [], intent_info)

    # 1. Format retrieved knowledge context for LLM prompt
    context_blocks = []
    for i, c in enumerate(retrieved_chunks, 1):
        c_dict = c.to_dict() if hasattr(c, "to_dict") else c
        title = c_dict.get("title", "Municipal Procedure")
        category = c_dict.get("category", "General")
        department = c_dict.get("department", "Municipal Corporation")
        text = str(c_dict.get("text", "")).strip()

        context_blocks.append(
            f"[Source {i}: {title} | Department: {department} | Category: {category}]\n"
            f"{text}"
        )

    context_str = "\n\n---\n\n".join(context_blocks) if context_blocks else "General Smart City Municipal Procedures"

    # 2. Format conversation history
    history_str = ""
    if conversation_history:
        recent = conversation_history[-4:]
        lines = [f"{m.get('role', 'user').title()}: {m.get('content', '')}" for m in recent]
        history_str = "Recent Conversation History:\n" + "\n".join(lines) + "\n\n"

    system_instruction = (
        "You are the city municipal help assistant for an urban local body.\n"
        "Your answers must be SHORT and SIMPLE so that any citizen can understand them at a glance.\n\n"
        "Strict rules:\n"
        "1. Keep the whole answer to 2 to 5 short lines. Never write long essays.\n"
        "2. Use plain everyday words. No jargon, no marketing, no self-praise.\n"
        "3. Never mention AI, Gemini, RAG, models, or that you are an assistant.\n"
        "4. Do not use big headers, long greetings, or many emojis. At most one small emoji.\n"
        "5. Answer only from the provided municipal knowledge. If it is missing, say you don't have "
        "that information and give the helpline 1800-233-0001.\n"
        "6. If the citizen wants to file a complaint, say the 2 to 3 things needed "
        "(the problem and the exact location/landmark) and tell them to tap the submit button.\n"
        "7. Mention timelines or hotlines only when they are relevant to the question.\n"
        "8. For real danger (live wire, sparking, gas leak, open manhole), add one short line: "
        "stay away and call 1912.\n"
        "9. Reply in the citizen's language (English, Hindi, or Marathi).\n"
        "10. Do not add a source or attribution line; the app shows that separately."
    )

    user_prompt = (
        f"{history_str}"
        f"Citizen Inquiry: {clean_question}\n\n"
        f"--- MUNICIPAL KNOWLEDGE BASE CONTEXT ---\n"
        f"{context_str}\n"
        f"-----------------------------------------\n\n"
        f"Reply in a short, simple way (2 to 5 short lines) that any citizen can understand."
    )

    # 3. Tier 1: Try Google Gemini GenAI if API key is present
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )

            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )

            if response and response.text:
                ans_text = response.text.strip()
                if "Sample Municipal Knowledge Base" not in ans_text:
                    ans_text = f"{ans_text}\n\n_Source: Sample Municipal Knowledge Base._"
                return ans_text
        except Exception as exc:
            logger.warning(
                "Gemini GenAI API call failed (%s). Attempting local generation.",
                str(exc),
            )

    # 4. Tier 2: Try local Ollama (Gemma 3) if running
    ollama_ans = generate_ollama_response(user_prompt, system_instruction)
    if ollama_ans:
        return ollama_ans

    # 5. Tier 3: Local Deterministic Template Fallback
    return format_conversational_fallback(clean_question, retrieved_chunks, intent_info)
