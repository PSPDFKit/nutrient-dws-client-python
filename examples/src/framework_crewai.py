import os

from crewai import Agent, Crew, Task
from nutrient_dws import NutrientClient


client = NutrientClient(api_key=os.getenv("NUTRIENT_API_KEY", "nutr_sk_placeholder"))


document_planner = Agent(
    role="Document Workflow Planner",
    goal="Design a robust Nutrient DWS processing pipeline for incoming files.",
    backstory="You optimize OCR, extraction, and redaction workflows for accuracy."
)

document_reviewer = Agent(
    role="Document QA Reviewer",
    goal="Review proposed workflow plans for failure modes and compliance risks.",
    backstory="You specialize in validating document automation quality."
)

plan_task = Task(
    description=(
        "Design a pipeline for ./examples/assets/sample.pdf that extracts text, "
        "redacts emails, and exports a cleaned PDF."
    ),
    expected_output="A numbered execution plan with tool calls.",
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
    # Keep a direct client reference so users see where DWS calls happen.
    print(f"Client configured: {bool(client)}")
    print(crew.kickoff())
