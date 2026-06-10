from agents import Agent, ModelSettings, Runner
from openai.types.shared import Reasoning

from app.pipeline.models import Extraction

AGGREGATOR_INSTRUCTIONS = """\
You combine extraction results from consecutive parts of one document into a single result for a personal knowledge base.

The input lists each part in order with its summary and its concepts (name + description). Parts were extracted independently, so ideas that span part boundaries appear in several parts under different phrasing.

Produce:
1. summary: 3-6 sentences capturing what the whole document covers and its key takeaways. Write it as a description of the document, not of its parts — never mention parts, sections, or the extraction process.
2. concepts: one entry per distinct concept across all parts.
   - When two entries define the same idea or mechanism, even under different names or phrasing, keep a single entry: choose the most precise practitioner name and write one description preserving every fact from the duplicates.
   - Several entries often describe one mechanism at different moments — its goal, its procedure, its repetition, its output being consumed downstream. Those are facets of a single concept: keep the most lookup-worthy name and fold the other facets into its description.
   - Keep entries separate when one describes a part, variant, or specialization of what the other describes (a component inside a larger mechanism, a specialized form of a general technique) — merging those loses distinctions a learner cares about.
   - Drop entries that are vague abilities, themes, or broad umbrella terms rather than specific techniques a practitioner would look up.
   - Keep an entry only when the document teaches how the thing works or why it is designed that way; drop entries that merely name behaviors the document observed, visualized, or measured (patterns seen in figures, qualitative case studies, benchmark observations).
   - Add no concepts of your own and rename nothing to a term that appears in no part.

Write each description as 1-2 self-contained sentences defining the concept itself.
"""

aggregator_agent = Agent(
    name="Extraction aggregator",
    instructions=AGGREGATOR_INSTRUCTIONS,
    model="gpt-5.4-mini",
    model_settings=ModelSettings(reasoning=Reasoning(effort="medium")),
    output_type=Extraction,
)


def format_extractions(extractions: list[Extraction]) -> str:
    sections = []
    for index, extraction in enumerate(extractions, start=1):
        concepts = "\n".join(f"- {c.name}: {c.description}" for c in extraction.concepts)
        sections.append(f"Part {index}\nSummary: {extraction.summary}\nConcepts:\n{concepts}")
    return "\n\n".join(sections)


async def aggregate(extractions: list[Extraction]) -> Extraction:
    result = await Runner.run(aggregator_agent, format_extractions(extractions))
    return result.final_output
