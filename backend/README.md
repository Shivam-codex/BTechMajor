# Smart City Complaint Management System — Backend

A production-grade, local, **Non-ML Deterministic Natural Language Processing** and **Information Retrieval** system for civic grievance redressal.

## Core Principles
- **ZERO Machine Learning:** No trained weights, no transformers, no black-box neural networks. 100% explainable, deterministic rule-based NLP.
- **Multilingual Support:** English, Marathi (Devanagari), and Code-mixed grievances.
- **Full Explainability:** Transparent extraction, tokenization, lemmatization, and rule scoring.

## Phase 1 Modules
- `backend/app/models/`: SQLAlchemy 2.0 schema for Complaints with SQLite default & PostgreSQL compatibility.
- `backend/app/services/extraction/`: Multi-format text extractors (`pdf_extractor.py`, `docx_extractor.py`, `txt_extractor.py`, `document_service.py`).
- `backend/app/services/nlp/`: Deterministic NLP normalization, tokenization, script/language detection, and municipal lemma mapping.
- `backend/app/core/`: Configuration via Pydantic v2 Settings, database engine, and structured privacy-preserving audit logging.

## Running Tests
```bash
python -m pytest backend/tests -v
```
