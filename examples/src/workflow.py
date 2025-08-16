"""
Workflow Example

This example demonstrates how to use the Nutrient DWS Python Client
with the workflow builder pattern for document processing operations.
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from nutrient_dws import NutrientClient
from nutrient_dws.builder.constant import BuildActions

# Load environment variables from .env file
load_dotenv()

# Check if API key is provided
if not os.getenv('NUTRIENT_API_KEY'):
    print('Error: NUTRIENT_API_KEY is not set in .env file')
    exit(1)

# Initialize the client with API key
client = NutrientClient(api_key=os.getenv('NUTRIENT_API_KEY'))

# Define paths
assets_dir = Path(__file__).parent.parent / 'assets'
output_dir = Path(__file__).parent.parent / 'output'

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)


# Example 1: Basic document conversion workflow
async def basic_conversion_workflow():
    print('Example 1: Basic document conversion workflow')

    try:
        docx_path = assets_dir / 'sample.docx'

        result = await client.workflow() \
            .add_file_part(docx_path) \
            .output_pdf() \
            .execute()

        # Save the result to the output directory
        output_path = output_dir / 'workflow-converted-document.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['output']['buffer'])

        print(f'Conversion workflow successful. Output saved to: {output_path}')
        print(f'MIME type: {result["output"]["mimeType"]}')
        return output_path
    except Exception as error:
        print(f'Conversion workflow failed: {error}')
        raise error


# Example 2: Document merging with watermark
async def merge_with_watermark_workflow():
    print('\nExample 2: Document merging with watermark workflow')

    try:
        pdf_path = output_dir / 'workflow-converted-document.pdf'
        png_path = assets_dir / 'sample.png'

        result = await client.workflow() \
            .add_file_part(pdf_path) \
            .add_file_part(png_path) \
            .apply_action(BuildActions.watermark_text('CONFIDENTIAL', {
                'opacity': 0.5,
                'fontSize': 48,
                'fontColor': '#FF0000'
            })) \
            .output_pdf() \
            .execute()

        # Save the result to the output directory
        output_path = output_dir / 'workflow-merged-watermarked.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['output']['buffer'])

        print(f'Merge with watermark workflow successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Merge with watermark workflow failed: {error}')
        raise error


# Example 3: Extract text with JSON output
async def extract_text_workflow(file_path: Path):
    print('\nExample 3: Extract text workflow with JSON output')

    try:
        result = await client.workflow() \
            .add_file_part(file_path) \
            .output_json({
                'plainText': True,
                'structuredText': True,
                'keyValuePairs': True,
                'tables': True
            }) \
            .execute()

        # Save the result to the output directory
        output_path = output_dir / 'workflow-extracted-text.json'
        with open(output_path, 'w') as f:
            json.dump(result['output']['data'], f, indent=2, default=str)

        print(f'Text extraction workflow successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Text extraction workflow failed: {error}')
        raise error


# Example 4: Complex multi-step workflow
async def complex_workflow():
    print('\nExample 4: Complex multi-step workflow')

    try:
        pdf_path = output_dir / 'workflow-converted-document.pdf'
        png_path = assets_dir / 'sample.png'

        result = await client.workflow() \
            .add_file_part(pdf_path) \
            .add_file_part(png_path) \
            .apply_actions([
                BuildActions.watermark_text('DRAFT', {
                    'opacity': 0.3,
                    'fontSize': 36,
                    'fontColor': '#0000FF'
                }),
                BuildActions.rotate(90)
            ]) \
            .output_pdfua({
                'metadata': {
                    'title': 'Complex Workflow Example',
                    'author': 'Nutrient DWS Python Client'
                }
            }) \
            .execute(on_progress= lambda current, total: print(f'Processing step {current} of {total}'))

        # Save the result to the output directory
        output_path = output_dir / 'workflow-complex-result.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['output']['buffer'])

        print(f'Complex workflow successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Complex workflow failed: {error}')
        raise error


# Example 5: Using sample.pdf directly
async def sample_pdf_workflow():
    print('\nExample 5: Using sample.pdf directly')

    try:
        pdf_path = assets_dir / 'sample.pdf'

        result = await client.workflow() \
            .add_file_part(pdf_path) \
            .apply_action(BuildActions.watermark_text('SAMPLE PDF', {
                'opacity': 0.4,
                'fontSize': 42,
                'fontColor': '#008000'
            })) \
            .output_pdf() \
            .execute()

        # Save the result to the output directory
        output_path = output_dir / 'workflow-sample-pdf-processed.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['output']['buffer'])

        print(f'Sample PDF workflow successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Sample PDF workflow failed: {error}')
        raise error


# Run all examples
async def run_examples():
    try:
        print('Starting workflow examples...\n')

        # Run the examples in sequence
        converted_pdf_path = await basic_conversion_workflow()
        await merge_with_watermark_workflow()
        await extract_text_workflow(converted_pdf_path)
        await complex_workflow()
        await sample_pdf_workflow()

        print('\nAll workflow examples completed successfully!')
    except Exception as error:
        print(f'\nWorkflow examples failed: {error}')


# Execute the examples
if __name__ == '__main__':
    asyncio.run(run_examples())
