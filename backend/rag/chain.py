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

Chat History:
{chat_history}

Context:
{context}

Guidelines:
1. If the answer is not contained within the Context, politely state: "I don't have enough information in the knowledge base to answer this."
2. Do NOT use outside knowledge or hallucinate information.
3. Be concise, accurate, and format your response clearly (using bullet points if applicable).
4. Use the Chat History to understand follow-up questions.
5. If the user asks for a chart, graph, or data visualization, provide the raw data in a specific JSON format inside a ```json block. Use the format:
```json
{{
  "chart_type": "bar", // can be bar, line, pie, scatter, or area
  "data": [{{"name": "Category 1", "value": 10}}, {{"name": "Category 2", "value": 20}}]
}}
```

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


def generate_answer(query: str, domain: Optional[str] = None, chat_history: Optional[List[dict]] = None) -> dict:
    """
    Execute the RAG pipeline: Retrieve context and generate an answer.

    Args:
        query: User's question.
        domain: Optional domain to search in. If None, dynamically routed.
        chat_history: Optional list of previous messages in the session.

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
    
    # Format chat history
    history_text = "No previous history."
    if chat_history:
        history_parts = []
        for msg in chat_history[-5:]: # only last 5 messages to save context window
            role = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {msg['content']}")
        history_text = "\n".join(history_parts)
        
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE).format(
        context=context_text,
        chat_history=history_text,
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


async def stream_generate_answer(query: str, domain: Optional[str] = None, chat_history: Optional[List[dict]] = None):
    """
    Execute the RAG pipeline and yield chunks of the answer asynchronously.

    Yields JSON strings with newlines:
    {"type": "token", "content": "..."}
    ...
    {"type": "citations", "data": [...]}
    """
    import json
    import asyncio
    logger.info(f"Streaming answer for query: '{query}' in domain: '{domain}'")
    
    # Send an initial empty token to force FastAPI to flush headers and prevent browser timeout
    yield json.dumps({"type": "token", "content": ""}) + "\n"
    await asyncio.sleep(0.1)

    # 1. Retrieve relevant documents
    # Run synchronously blocking retriever in a thread to prevent freezing the FastAPI event loop
    docs = await asyncio.to_thread(retrieve_documents, query=query, domain=domain, k=5)
    
    # Yield another keep-alive after retrieval
    yield json.dumps({"type": "token", "content": ""}) + "\n"
    await asyncio.sleep(0.1)
    
    citations = []
    for doc in docs:
        citations.append({
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
            "domain": doc.metadata.get("domain", "default"),
            "chunk_index": doc.metadata.get("chunk_index"),
        })

    if not docs:
        logger.info("No context retrieved. Falling back to default no-info response.")
        yield json.dumps({"type": "token", "content": "I don't have enough information in the knowledge base to answer this."}) + "\n"
        yield json.dumps({"type": "citations", "data": []}) + "\n"
        return

    # 2. Format context and prompt
    context_text = format_context(docs)
    
    history_text = "No previous history."
    if chat_history:
        history_parts = []
        for msg in chat_history[-5:]: # only last 5 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {msg['content']}")
        history_text = "\n".join(history_parts)
        
    prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE).format(
        context=context_text,
        chat_history=history_text,
        question=query
    )

    # 3. Stream answer using LLM
    try:
        llm = get_llm()
        # astream is an async generator returning chunks
        async for chunk in llm.astream(prompt):
            yield json.dumps({"type": "token", "content": chunk.content}) + "\n"
    except Exception as e:
        logger.error(f"Failed to stream answer via LLM: {e}")
        yield json.dumps({"type": "token", "content": "\n\nI encountered an error while generating the answer."}) + "\n"
        
    # 4. Yield citations at the end
    yield json.dumps({"type": "citations", "data": citations}) + "\n"

