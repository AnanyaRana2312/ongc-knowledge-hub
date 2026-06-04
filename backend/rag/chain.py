"""
backend/rag/chain.py
--------------------
RAG generation chain. Retrieves documents and uses the LLM to generate an answer.
"""

import logging
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from backend.models.ollama_client import get_llm
from backend.rag.retriever import retrieve_documents

logger = logging.getLogger(__name__)

# Strict RAG system prompt to prevent hallucination
RAG_PROMPT_TEMPLATE = """You are a highly knowledgeable and professional assistant for the ONGC Knowledge Hub.
Your task is to answer the user's question based strictly on the provided context below.

Context:
{context}

Guidelines:
1. If the answer is not contained within the Context, politely state: "I don't have enough information in the knowledge base to answer this."
2. Do NOT use outside knowledge or hallucinate information.
3. Be concise, accurate, and format your response clearly (using bullet points if applicable).

Question: {question}

Answer:"""


def format_context(documents: List[Document]) -> str:
    """Combine retrieved documents into a single context string."""
    parts = []
    for i, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "N/A")
        content = doc.page_content.strip()
        parts.append(f"--- Document {i} (Source: {source}, Page: {page}) ---\n{content}\n")
    return "\n".join(parts)


def generate_answer(query: str, domain: Optional[str] = None) -> dict:
    """
    Execute the RAG pipeline: Retrieve context and generate an answer.

    Args:
        query: User's question.
        domain: Optional domain to search in. If None, dynamically routed.

    Returns:
        dict with "answer" and "source_documents".
    """
    logger.info(f"Generating answer for query: '{query}' in domain: '{domain}'")

    # 1. Retrieve relevant documents
    # The retriever dynamically routes if domain is None
    docs = retrieve_documents(query=query, domain=domain, k=5)

    if not docs:
        logger.info("No context retrieved. Falling back to default no-info response.")
        return {
            "answer": "I don't have enough information in the knowledge base to answer this.",
            "source_documents": []
        }

    # 2. Format context and prompt
    context_text = format_context(docs)
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE).format(
        context=context_text,
        question=query
    )

    # 3. Generate answer using LLM
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        answer = response.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate answer via LLM: {e}")
        answer = "I encountered an error while trying to generate the answer. Please try again later."

    return {
        "answer": answer,
        "source_documents": docs
    }
