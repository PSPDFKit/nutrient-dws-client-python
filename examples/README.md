# Nutrient DWS Python Client Examples

This example project demonstrates how to use the Nutrient DWS Python Client for document processing operations.

## Project Structure

- `assets/` - Contains sample files for processing (PDF, DOCX, PNG)
- `src/` - Contains Python source files
  - `direct_method.py` - Examples using direct method calls
  - `workflow.py` - Examples using the workflow builder pattern
- `output/` - Directory where processed files will be saved
- `.env.example` - Example environment variables file

## Prerequisites

- Python 3.10 or higher
- pip

## Setup

### Option 1: Virtual Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/pspdfkit-labs/nutrient-dws-client-python.git
   cd nutrient-dws-client-python
   ```

2. Build the package from source:
   ```bash
   python -m build
   ```

3. Navigate to the examples directory:
   ```bash
   cd examples
   ```

4. Set up and activate the virtual environment:
   ```bash
   # Set up the virtual environment and install dependencies
   python setup_venv.py

   # Activate the virtual environment
   # On macOS/Linux:
   source example_venv/bin/activate

   # On Windows:
   example_venv\Scripts\activate
   ```

5. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file and add your Nutrient DWS Processor API key. You can sign up for a free API key by visiting [Nutrient](https://www.nutrient.io/api/):
   ```
   NUTRIENT_API_KEY=your_api_key_here
   ```

### Option 2: Development Mode Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/pspdfkit-labs/nutrient-dws-client-python.git
   cd nutrient-dws-client-python
   ```

2. Install the main package in development mode:
   ```bash
   pip install -e .
   ```

3. Navigate to the examples directory:
   ```bash
   cd examples
   ```

4. Install dependencies for the example project:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file and add your Nutrient DWS Processor API key. You can sign up for a free API key by visiting [Nutrient](https://www.nutrient.io/api/):
   ```
   NUTRIENT_API_KEY=your_api_key_here
   ```

## Running the Examples

### Direct Method Examples

To run the direct method examples:

```bash
python src/direct_method.py
```

This will:
1. Convert a DOCX file to PDF
2. Extract text from the PDF
3. Add a watermark to the PDF
4. Merge multiple documents

### Workflow Examples

To run the workflow examples:

```bash
python src/workflow.py
```

This will:
1. Perform a basic document conversion workflow
2. Create a document merging with watermark workflow
3. Extract text with JSON output
4. Execute a complex multi-step workflow

## Output

All processed files will be saved to the `output/` directory. You can examine these files to see the results of the document processing operations.

## Documentation

For more information about the Nutrient DWS Python Client, refer to:

- [README.md](../README.md) - Main documentation
- [METHODS.md](../docs/METHODS.md) - Direct methods documentation
- [WORKFLOW.md](../docs/WORKFLOW.md) - Workflow system documentation
