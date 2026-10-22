import os

from crewai import Agent, Crew, Task
from crewai.tools import tool
from dotenv import load_dotenv

from nutrient_dws import NutrientClient

load_dotenv()
api_key = os.getenv("NUTRIENT_API_KEY")
if not api_key:
    raise SystemExit("NUTRIENT_API_KEY is required in your environment or .env file.")
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY is required in your environment or .env file.")

client = NutrientClient(api_key=api_key)


@tool("extract_document_text")
async def extract_document_text(input_path: str) -> str:
    """Extract document text with Nutrient DWS before planning further processing."""
    result = await client.extract_text(input_path)
    return str(result)


document_planner = Agent(
    role="Document Workflow Planner",
    goal="Design a robust Nutrient DWS processing pipeline for incoming files.",
    backstory="You optimize OCR, extraction, and redaction workflows for accuracy.",
    tools=[extract_document_text],
    llm="gpt-6-luna",
)

document_reviewer = Agent(
    role="Document QA Reviewer",
    goal="Review proposed workflow plans for failure modes and compliance risks.",
    backstory="You specialize in validating document automation quality.",
    llm="gpt-6-luna",
)

plan_task = Task(
    description=(
        "Use your extraction tool on ./assets/sample.pdf, then design a pipeline "
        "that redacts emails and exports a cleaned PDF."
    ),
    expected_output="Extracted text and a numbered plan for the remaining processing.",
    agent=document_planner,
)

review_task = Task(
    description=(
        "Review the proposed pipeline. Flag risks and add fallback handling steps."
    ),
    expected_output="Risk review with concrete mitigations.",
    agent=document_reviewer,
)

crew = Crew(
    agents=[document_planner, document_reviewer],
    tasks=[plan_task, review_task],
    verbose=True,
)


if __name__ == "__main__":
    print(crew.kickoff())
