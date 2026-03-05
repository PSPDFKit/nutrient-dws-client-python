import asyncio
import os

from agents import Agent, Runner, function_tool
from nutrient_dws import NutrientClient


client = NutrientClient(api_key=os.getenv("NUTRIENT_API_KEY", "nutr_sk_placeholder"))


@function_tool
async def extract_text(input_path: str) -> str:
    """Extract text from a document using Nutrient DWS."""
    result = await client.extract_text(input_path)
    return str(result)


assistant = Agent(
    name="nutrient-openai-agents-demo",
    instructions="Help users extract text and summarize document workflows.",
    tools=[extract_text],
)


async def main() -> None:
    run = await Runner.run(
        assistant,
        "Extract text from ./assets/sample.pdf and summarize it in three bullets.",
    )
    print(run.final_output)


if __name__ == "__main__":
    asyncio.run(main())
