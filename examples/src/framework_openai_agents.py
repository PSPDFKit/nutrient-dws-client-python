import asyncio
import os

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from nutrient_dws import NutrientClient

load_dotenv()
api_key = os.getenv("NUTRIENT_API_KEY")
if not api_key:
    raise SystemExit("NUTRIENT_API_KEY is required in your environment or .env file.")
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY is required in your environment or .env file.")

client = NutrientClient(api_key=api_key)


@function_tool
async def extract_text(input_path: str) -> str:
    """Extract text from a document using Nutrient DWS."""
    result = await client.extract_text(input_path)
    return str(result)


assistant = Agent(
    name="nutrient-openai-agents-demo",
    model="gpt-4.1-mini",
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
