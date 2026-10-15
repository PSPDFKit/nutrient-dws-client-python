import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from nutrient_dws import NutrientClient

load_dotenv()
api_key = os.getenv("NUTRIENT_API_KEY")
if not api_key:
    raise SystemExit("NUTRIENT_API_KEY is required in your environment or .env file.")
if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("OPENAI_API_KEY is required in your environment or .env file.")

client = NutrientClient(api_key=api_key)


async def redact_emails(path: str) -> str:
    result = await client.create_redactions_ai(
        path,
        criteria="Redact all email addresses.",
        redaction_state="apply",
    )
    output_path = Path("output") / "redacted.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result["buffer"])
    return f"Saved redacted PDF to {output_path} ({len(result['buffer'])} bytes)."


tool = StructuredTool.from_function(
    coroutine=redact_emails,
    name="redact_emails",
    description="Redact email addresses from a document using Nutrient DWS.",
)


async def main() -> None:
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=os.environ["OPENAI_API_KEY"],
    )
    agent = create_react_agent(model, [tool])
    state = await agent.ainvoke(
        {"messages": [("user", "Redact emails from ./assets/sample.pdf.")]}
    )
    print(state["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
