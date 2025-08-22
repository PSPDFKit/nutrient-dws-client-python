import os
import sys


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, "LLM_DOC.md")

    user_project_root = os.getcwd()
    output_directory = os.path.join(user_project_root, ".github")
    output_file = os.path.join(output_directory, "copilot-instructions.md")

    relative_doc_path = os.path.relpath(doc_path, user_project_root)

    try:
        rule = f"""
# Nutrient DWS Python Client Usage
- Use the `nutrient-dws` package for operations with document processing operations including conversion, merging, compression, watermarking, signage, and text extraction.
- Package Documentation and Examples can be found at: {relative_doc_path}
"""
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(rule)

        print(
            f"📄 Updated GitHub Copilot Rules to point to Nutrient DWS documentation at {relative_doc_path}."
        )
    except Exception as err:
        print(
            f"Failed to update .github/copilot-instructions.md file: {err}",
            file=sys.stderr,
        )
        sys.exit(1)
