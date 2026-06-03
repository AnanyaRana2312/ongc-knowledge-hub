"""
backend/rag/router.py
----------------------
Semantic query router using a local LLM to dynamically determine 
which collection/domain a user's question belongs to.
"""

import logging
from typing import List

from backend.models.ollama_client import get_llm

logger = logging.getLogger(__name__)

# Prompt instructing the LLM to classify the query.
ROUTING_PROMPT_TEMPLATE = """You are a smart classifier for a knowledge base routing system.
Your job is to classify the user's question into one of the available category domains.

Available domains:
{domains_list}

Rules:
1. Choose the domain that is most relevant to the question.
2. Respond with ONLY the exact name of the chosen domain from the list.
3. If the question does not match any of the domains, output "default".
4. Do NOT output any explanation, markdown, conversational text, or punctuation. Just output the word.

Examples:
Question: "procedures for drill string tension" -> drilling
Question: "standard fire escape map and assembly point" -> safety
Question: "how to apply for casual leave in HR portal" -> hr

Question: "{query}"
Answer:"""


def classify_query_domain(query: str, active_domains: List[str]) -> str:
    """
    Classify a user query into one of the active domains using the local LLM.

    Args:
        query: User natural language search query.
        active_domains: List of currently active collection/domain names in ChromaDB.

    Returns:
        The matched domain name, or 'default' if it cannot be classified.
    """
    if not active_domains:
        logger.info("No active domains available for classification. Returning 'default'.")
        return "default"

    # If there is only one domain active, skip LLM call and route there directly
    if len(active_domains) == 1:
        logger.info(f"Only one active domain exists ('{active_domains[0]}'). Auto-routing.")
        return active_domains[0]

    # Normalize domains for matching
    domains_map = {d.lower(): d for d in active_domains}
    domains_list_str = "\n".join([f"- {d}" for d in active_domains])

    prompt = ROUTING_PROMPT_TEMPLATE.format(
        domains_list=domains_list_str,
        query=query
    )

    try:
        logger.info(f"Running LLM classification for query: '{query}' across domains: {active_domains}")
        llm = get_llm()
        response = llm.invoke(prompt)
        predicted = response.content.strip().lower()

        # Simple cleaning of quotes, brackets or extra spacing
        predicted = predicted.replace("'", "").replace('"', "").replace("[", "").replace("]", "").strip()

        # Match prediction against active domains
        for key, original in domains_map.items():
            if key in predicted or predicted in key:
                logger.info(f"Routed query '{query}' to domain: '{original}' (LLM response: '{predicted}')")
                return original

        logger.info(f"LLM response '{predicted}' did not match active domains. Falling back to default.")
        return "default"

    except Exception as e:
        logger.error(f"LLM query classification failed: {e}. Falling back to default.")
        return "default"
