"""
Direct Method Example

This example demonstrates how to use the Nutrient DWS Python Client
with direct method calls for document processing operations.
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from nutrient_dws import NutrientClient

# Load environment variables from .env file
load_dotenv()

# Check if API key is provided
if not os.getenv('NUTRIENT_API_KEY'):
    print('Error: NUTRIENT_API_KEY is not set in .env file')
    exit(1)

# Initialize the client with API key
client = NutrientClient({
    'apiKey': os.getenv('NUTRIENT_API_KEY')
})

# Define paths
assets_dir = Path(__file__).parent.parent / 'assets'
output_dir = Path(__file__).parent.parent / 'output'

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)


# Example 1: Convert a document
async def convert_document():
    print('Example 1: Converting DOCX to PDF')

    try:
        docx_path = assets_dir / 'sample.docx'
        result = await client.convert(docx_path, 'pdf')

        # Save the result to the output directory
        output_path = output_dir / 'converted-document.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['buffer'])

        print(f'Conversion successful. Output saved to: {output_path}')
        print(f'MIME type: {result["mimeType"]}')
        return output_path
    except Exception as error:
        print(f'Conversion failed: {error}')
        raise error


# Example 2: Extract text from a document
async def extract_text(file_path: Path):
    print('\nExample 2: Extracting text from PDF')

    try:
        result = await client.extract_text(file_path)

        # Save the extracted text to the output directory
        output_path = output_dir / 'extracted-text.json'
        with open(output_path, 'w') as f:
            json.dump(result['data'], f, indent=2, default=str)

        # Display a sample of the extracted text
        text_sample = result['data']['pages'][0]['plainText'][:100] + '...'
        print(f'Text extraction successful. Output saved to: {output_path}')
        print(f'Text sample: {text_sample}')
        return output_path
    except Exception as error:
        print(f'Text extraction failed: {error}')
        raise error


# Example 3: Add a watermark to a document
async def add_watermark(file_path: Path):
    print('\nExample 3: Adding watermark to PDF')

    try:
        result = await client.watermark_text(file_path, 'CONFIDENTIAL', {
            'opacity': 0.5,
            'font_color': '#FF0000',
            'rotation': 45,
            'width': {'value': 50, 'unit': '%'}
        })

        # Save the watermarked document to the output directory
        output_path = output_dir / 'watermarked-document.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['buffer'])

        print(f'Watermarking successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Watermarking failed: {error}')
        raise error


# Example 4: Merge multiple documents
async def merge_documents():
    print('\nExample 4: Merging documents')

    try:
        # Create a second PDF
        pdf_path = assets_dir / 'sample.pdf'

        # Get the converted PDF from Example 1
        converted_pdf_path = output_dir / 'converted-document.pdf'

        # Merge the documents
        result = await client.merge([converted_pdf_path, pdf_path])

        # Save the merged document to the output directory
        output_path = output_dir / 'merged-document.pdf'
        with open(output_path, 'wb') as f:
            f.write(result['buffer'])

        print(f'Merging successful. Output saved to: {output_path}')
        return output_path
    except Exception as error:
        print(f'Merging failed: {error}')
        raise error


# Example 5: Process sample.pdf directly
async def process_sample_pdf():
    print('\nExample 5: Processing sample.pdf directly')

    try:
        pdf_path = assets_dir / 'sample.pdf'

        # Extract text from sample.pdf
        extract_result = await client.extract_text(pdf_path)
        extract_output_path = output_dir / 'sample-pdf-extracted-text.json'
        with open(extract_output_path, 'w') as f:
            json.dump(extract_result['data'], f, indent=2, default=str)

        watermark_image_path = assets_dir / 'sample.png'

        # Add watermark to sample.pdf
        watermark_result = await client.watermark_image(pdf_path, watermark_image_path, {
            'opacity': 0.4,
        })

        watermark_output_path = output_dir / 'sample-pdf-watermarked.pdf'
        with open(watermark_output_path, 'wb') as f:
            f.write(watermark_result['buffer'])

        print('Sample PDF processing successful.')
        print(f'Extracted text saved to: {extract_output_path}')
        print(f'Watermarked PDF saved to: {watermark_output_path}')

        return watermark_output_path
    except Exception as error:
        print(f'Sample PDF processing failed: {error}')
        raise error


# Run all examples
async def run_examples():
    try:
        print('Starting direct method examples...\n')

        # Run the examples in sequence
        converted_pdf_path = await convert_document()
        await extract_text(converted_pdf_path)
        await add_watermark(converted_pdf_path)
        await merge_documents()
        await process_sample_pdf()

        print('\nAll examples completed successfully!')
    except Exception as error:
        print(f'\nExamples failed: {error}')


# Execute the examples
if __name__ == '__main__':
    asyncio.run(run_examples())
