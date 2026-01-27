from pydantic import BaseModel
from openai import AsyncOpenAI

from app.core.config import settings


class PaperMetadata(BaseModel):
    """Structured output for paper metadata extraction."""
    title: str
    abstract: str
    confidence: float


SYSTEM_PROMPT = """You are an expert academic paper parser. Your task is to extract the title and abstract from academic paper text.

Instructions:
1. The title is typically at the very beginning of the paper, often in a larger font or on its own line
2. The abstract usually appears after the title and author information, often labeled "Abstract"
3. If the abstract is not explicitly labeled, look for a summary paragraph at the beginning of the paper
4. Extract the COMPLETE abstract, not just the first sentence
5. If you cannot find a clear abstract, summarize the paper's main contribution in 2-3 sentences
6. Provide a confidence score (0.0 to 1.0) indicating how confident you are in the extraction

Output the title and abstract exactly as they appear in the paper (preserving formatting where appropriate).
Do not add any commentary or explanation - just extract the information."""


async def extract_paper_metadata(text: str) -> PaperMetadata:
    """Extract title and abstract from paper text using OpenAI.

    Args:
        text: The text content of the paper (typically first ~8000 chars)

    Returns:
        PaperMetadata with title, abstract, and confidence score

    Raises:
        Exception: If OpenAI API call fails
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract the title and abstract from this paper:\n\n{text}"},
        ],
        response_format=PaperMetadata,
    )

    return response.choices[0].message.parsed
