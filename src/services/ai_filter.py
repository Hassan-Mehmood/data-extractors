"""
AI-powered record filtering using LangChain + OpenAI.

Records are processed in batches of BATCH_SIZE to stay within token limits.
The LLM returns structured output (a list of matching item_ids), which are
then used to filter the original records.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.core.config import Settings

BATCH_SIZE = 50

_SYSTEM_PROMPT = """\
You are a data filtering assistant. The user will describe what records they want.
You will be given a batch of structured records from an ANX intelligence chart.
Each record has an item_id and several attributes.

Your task: Return ONLY the item_ids of records that match the user's description.
Be inclusive — if a record is a reasonable match, include it.
Do not explain your reasoning. Only return the list of matching item_ids.
"""


class _FilterResult(BaseModel):
    matching_ids: list[str]


def _records_to_text(records: list[dict]) -> str:
    lines: list[str] = []
    for rec in records:
        parts = [f"{k}={v!r}" for k, v in rec.items() if v not in (None, "")]
        lines.append("  ".join(parts))
    return "\n".join(lines)


def filter_records(
    records: list[dict],
    prompt: str,
    settings: Settings,
) -> list[dict]:
    """
    Filter *records* by *prompt* using the configured OpenAI model.

    Records are split into batches of BATCH_SIZE. Each batch is sent to the
    LLM with a structured-output schema that returns only matching item_ids.
    The results across all batches are merged and deduplicated before filtering.

    Parameters
    ----------
    records:
        All parsed records from the ANX file.
    prompt:
        The user's natural-language query describing which records to keep.
    settings:
        App settings (must include OPENAI_API_KEY and OPENAI_MODEL).

    Returns
    -------
    Filtered list of records whose item_id was selected by the LLM.
    """
    if not records:
        return []

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,  # type: ignore[arg-type]
        temperature=0,
    ).with_structured_output(_FilterResult)

    matched_ids: set[str] = set()

    # Process in batches
    for batch_start in range(0, len(records), BATCH_SIZE):
        batch = records[batch_start : batch_start + BATCH_SIZE]
        batch_text = _records_to_text(batch)

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"User request: {prompt}\n\nRecords (one per line):\n{batch_text}"
                )
            ),
        ]

        result: _FilterResult = llm.invoke(messages)  # type: ignore[assignment]
        matched_ids.update(result.matching_ids)

    # Maintain original order
    return [r for r in records if r.get("item_id") in matched_ids]
