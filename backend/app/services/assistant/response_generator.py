"""
Conversational Municipal Assistant Response Generator.
Generates complete, fluent, platform-grade (Flipkart/Amazon style) responses
using Google GenAI SDK (gemini-2.5-flash) grounded strictly in retrieved municipal knowledge base chunks.
Includes rich conversational local fallback if GEMINI_API_KEY is not configured or if an API call fails.
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
            "Hello! 👋 Welcome to the **Smart City Civic Support & Grievance Portal**.\n\n"
            "I am your automated Municipal Assistant, ready to assist you 24/7. Here is what I can do for you:\n\n"
            "1. **⚡ File a Grievance:** Report issues with electricity, water leaks, potholes, garbage, or street lights.\n"
            "2. **🔍 Track Complaints:** Check live status and resolution updates for your filed complaints.\n"
            "3. **⏱️ Check Timelines (SLAs):** Get official resolution deadlines and escalation contacts.\n"
            "4. **📞 Emergency Help:** Instant contacts for power lines, burst pipelines, and disaster response.\n\n"
            "*How can I assist you with municipal services today? You can select a quick action below or type your question.*"
        )

    # 2. Tracking Intent
    if intent == "TRACK_STATUS":
        if tracking_id:
            return (
                f"I can certainly help you track **{tracking_id}**! 🔍\n\n"
                f"According to the official **Sample Municipal Knowledge Base** (*Complaint Status and Tracking Guide*):\n\n"
                f"- **Direct Tracking:** Click the button below to view the live status, assigned municipal engineer, and audit trail for `{tracking_id}`.\n"
                f"- **Status Stages:** Complaints progress through `Submitted` ➔ `Classified` ➔ `Assigned` ➔ `In Progress` ➔ `Resolved`.\n"
                f"- **Need Escalation?** If your grievance exceeds the official SLA turnaround time, you can trigger an escalation through your dashboard."
            )
        else:
            return (
                "I'd be happy to help you track your filed complaints! 📋\n\n"
                "According to the official **Sample Municipal Knowledge Base** (*Complaint Status and Tracking Guide*):\n\n"
                "1. **View All Your Complaints:** Click **[Open My Complaints Tracker]** below to view all grievances filed under your account.\n"
                "2. **Find by Tracking ID:** If you have an ID like `CMP-2026-XXXXX`, simply enter it here or on the tracking page to inspect live updates, assigned field staff, and SLA timers."
            )

    # 3. Out of Domain Intent (e.g., poetry, unrelated chit-chat)
    if intent == "OUT_OF_DOMAIN" or not retrieved_chunks:
        return (
            "I could not find sufficient information about this question in the "
            "Sample Municipal Knowledge Base. Please contact the General Grievance Cell "
            "or call the Central Municipal Helpline at 1800-233-0001 (Toll-Free, 24/7)."
        )

    # 4. Grievance Filing & Procedural Inquiry
    top_chunk = retrieved_chunks[0]
    top_title = getattr(top_chunk, "title", None) or (top_chunk.get("title") if isinstance(top_chunk, dict) else "Municipal Guidelines")
    top_dept = getattr(top_chunk, "department", None) or (top_chunk.get("department") if isinstance(top_chunk, dict) else (dept or "Municipal Corporation"))
    top_text = getattr(top_chunk, "text", None) or (top_chunk.get("text") if isinstance(top_chunk, dict) else "")

    intro_phrase = f"I can certainly help you with your inquiry regarding **{category or 'Civic Services'}**! 🏛️\n\n"
    if intent == "LODGE_GRIEVANCE" and category:
        intro_phrase = f"I'd be glad to help you lodge a complaint regarding **{category}** right away! 📝\n\n"

    body_parts = [
        intro_phrase,
        f"According to the official **Sample Municipal Knowledge Base** (*{top_title}*, {top_dept}):\n",
        f"{top_text}\n",
    ]

    # Add quick steps for filing
    if intent == "LODGE_GRIEVANCE":
        body_parts.append(
            "\n### 🚀 Quick Steps to Submit Your Grievance:\n"
            "1. **Click the Action Button Below:** Open the **[Submit Grievance Now]** button to launch the pre-configured form.\n"
            "2. **Provide Landmark & Details:** Specify the exact street, ward number, and description of the problem.\n"
            "3. **Attach Photos (Optional):** Upload images or documents to assist the field inspection squad.\n"
            "4. **Instant Tracking ID:** Upon submission, you will receive an official tracking ID (e.g. `CMP-2026-XXXXX`) to monitor progress."
        )

    # Add emergency advisory if applicable
    if is_emergency or category == "Electricity":
        body_parts.append(
            "\n⚠️ **Safety Advisory:** For hazardous situations (e.g. sparking transformers, fallen live wires, open manholes), "
            "please maintain a safe 15-meter distance and dial our **24/7 Rapid Squad at 1912** or **1800-233-0001** immediately."
        )

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


def generate_llm_response(
    question: str,
    retrieved_chunks: list,
    intent_info: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Synthesizes a fluent, articulate, ChatGPT/Gemini-style response using Google GenAI SDK.
    Grounds response strictly in retrieved municipal knowledge base chunks and conversational context.
    Falls back gracefully to format_conversational_fallback if GEMINI_API_KEY is not configured or call fails.
    """
    clean_question = (question or "").strip()

    # Out of domain check
    if intent_info and intent_info.get("intent") == "OUT_OF_DOMAIN":
        return format_conversational_fallback(clean_question, [], intent_info)

    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.info("GEMINI_API_KEY not set. Using conversational local response generator.")
        return format_conversational_fallback(clean_question, retrieved_chunks, intent_info)

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
        "You are the Official Smart City Municipal Assistant for our urban local body, "
        "designed like a modern customer care support bot (similar to Flipkart / Amazon customer support).\n"
        "Your tone must be warm, professional, proactive, and exceptionally helpful.\n\n"
        "Core Capabilities & Guidelines:\n"
        "1. Welcome citizen queries warmly. If they want to file or raise a complaint (e.g. electricity, water, roads, garbage), "
        "enthusiastically guide them on how to submit it right away.\n"
        "2. State that the guidance is derived from the official Sample Municipal Knowledge Base.\n"
        "3. Provide structured, numbered step-by-step instructions. Explain what details are needed (location, landmark, photos).\n"
        "4. Highlight resolution timelines (SLAs), escalation channels, and responsible municipal departments whenever present in the context.\n"
        "5. Provide safety advisories for hazardous issues (live wires, sparking transformers, gas leaks, open manholes) and mention emergency hotlines (1912 / 1800-233-0001).\n"
        "6. If the citizen's query is in Marathi, Hindi, or mixed Devanagari script, respond courteously in that language or provide a clear bilingual response.\n"
        "7. Format using clean Markdown (bold terms, bullet points, headers)."
    )

    user_prompt = (
        f"{history_str}"
        f"Citizen Inquiry: {clean_question}\n\n"
        f"--- MUNICIPAL KNOWLEDGE BASE CONTEXT ---\n"
        f"{context_str}\n"
        f"-----------------------------------------\n\n"
        f"Please provide an articulate, warm, comprehensive, and step-by-step response to assist the citizen."
    )

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
                ans_text = f"According to the official **Sample Municipal Knowledge Base**:\n\n{ans_text}"
            return ans_text
        else:
            return format_conversational_fallback(clean_question, retrieved_chunks, intent_info)

    except Exception as exc:
        logger.warning(
            "Gemini GenAI API call failed (%s). Falling back to conversational response generator.",
            str(exc),
        )
        return format_conversational_fallback(clean_question, retrieved_chunks, intent_info)
