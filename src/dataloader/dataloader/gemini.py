"""Gemini integration for document analysis and enrichment."""

from dataloader.config import settings


async def analyze_document(content: str, prompt: str = "") -> str:
    """Analyze document content using Gemini 3.0 Flash Preview.

    Args:
        content: The document text to analyze.
        prompt: Optional analysis prompt. Defaults to summarization.

    Returns:
        Gemini's analysis response.
    """
    from google import genai

    client = genai.Client(api_key=settings.google_api_key)

    if not prompt:
        prompt = "Summarize the key information in this document. Extract entities, dates, and relationships."

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=f"{prompt}\n\n---\n\n{content}",
    )
    return response.text


async def extract_entities(content: str) -> dict:
    """Extract structured entities from document content using Gemini."""
    from google import genai

    client = genai.Client(api_key=settings.google_api_key)

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=(
            "Extract all entities (people, organizations, locations, dates, concepts) "
            "from this text. Return as JSON with keys: people, organizations, locations, "
            "dates, concepts. Each value is a list of strings.\n\n"
            f"---\n\n{content}"
        ),
    )

    import json
    try:
        # Try to parse JSON from response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return {"raw": response.text}
