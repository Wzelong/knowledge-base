from agents import Agent, ModelSettings, Runner
from openai.types.shared import Reasoning
from pydantic import BaseModel

MERGE_INSTRUCTIONS = """\
You maintain canonical descriptions for concepts in a knowledge base.

You receive a concept's existing description and a new description extracted from another source. Write the single best description: keep every fact from the existing description, fold in only what the new description genuinely adds, and stay within 1-3 sentences. If the new description adds nothing, return the existing description unchanged.

Respond with the description text only.
"""

merge_agent = Agent(
    name="Description merger",
    instructions=MERGE_INSTRUCTIONS,
    model="gpt-5.4-mini",
    model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
)


async def merge_descriptions(name: str, existing: str, new: str) -> str:
    prompt = (
        f"Concept: {name}\n\n"
        f"Existing description:\n{existing}\n\n"
        f"New description:\n{new}"
    )
    result = await Runner.run(merge_agent, prompt)
    return result.final_output.strip()


JUDGE_INSTRUCTIONS = """\
You decide whether two entries in a knowledge base refer to the same concept.

Judge by what the descriptions define, not by surface naming: if both descriptions define the same idea or mechanism, the entries are the same concept even when their names differ in wording or specificity. They are different concepts when one describes a part, variant, or specialization of what the other describes — even if closely related and usually discussed together (e.g. a component inside a larger mechanism, or a specialized form of a general technique).

Answer same_concept=true only when merging the two entries would lose no distinction a learner might care about.
"""


class SameConceptVerdict(BaseModel):
    same_concept: bool
    reason: str


judge_agent = Agent(
    name="Concept judge",
    instructions=JUDGE_INSTRUCTIONS,
    model="gpt-5.4-mini",
    model_settings=ModelSettings(reasoning=Reasoning(effort="low")),
    output_type=SameConceptVerdict,
)


async def is_same_concept(
    existing_name: str, existing_description: str, new_name: str, new_description: str
) -> SameConceptVerdict:
    prompt = (
        f"Entry A: {existing_name}\n{existing_description}\n\n"
        f"Entry B: {new_name}\n{new_description}"
    )
    result = await Runner.run(judge_agent, prompt)
    return result.final_output
