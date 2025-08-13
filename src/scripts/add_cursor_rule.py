import os
import sys


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, "..", "LLM_DOC.md")
    with open(doc_path, encoding="utf-8") as file:
        documentation = file.read()
    type_path = os.path.join(script_dir, "..", "dist", "__init__.pyi")

    user_project_root = os.getcwd()
    output_directory = os.path.join(user_project_root, ".cursor/rules")
    output_file = os.path.join(output_directory, "nutrient-dws-doc.mdc")

    relative_type_path = os.path.relpath(type_path, user_project_root)

    try:
        rule = f"""
---
description: This rule explains how to use the Nutrient DWS Python Client (`@nutrient-sdk/dws-client-python`) for operations with document processing operations including conversion, merging, compression, watermarking, signage, and text extraction.
globs:
alwaysApply: false
---
> The Python Type Definitions can be found at: ${relative_type_path}

{documentation}
"""
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(rule)

        print(f"📄 Updated Cursor Rules to point to Nutrient DWS documentation at {output_file}.")
    except Exception as err:
        print(f"Failed to update Cursor Rule: {err}", file=sys.stderr)
        sys.exit(1)
