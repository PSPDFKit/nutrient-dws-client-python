# PyPI Trusted Publisher Setup Guide

## Current Error
The error message shows these claims from your GitHub Action:
- `sub`: `repo:PSPDFKit/nutrient-dws-client-python:ref:refs/heads/main`
- `repository`: `PSPDFKit/nutrient-dws-client-python`
- `repository_owner`: `PSPDFKit`
- `workflow_ref`: `PSPDFKit/nutrient-dws-client-python/.github/workflows/publish-existing-tag.yml@refs/heads/main`

## Configure PyPI Trusted Publisher

1. Go to https://pypi.org/manage/project/nutrient-dws/settings/publishing/
2. Under "Trusted Publishers", click "Add a new publisher"
3. Select "GitHub" as the publisher type
4. Fill in the following:

### For Workflow Dispatch (Manual Trigger)
- **Repository owner**: `PSPDFKit`
- **Repository name**: `nutrient-dws-client-python`
- **Workflow name**: `publish-existing-tag.yml`
- **Environment name**: (leave empty)

### For Release Workflow
Add another trusted publisher:
- **Repository owner**: `PSPDFKit`
- **Repository name**: `nutrient-dws-client-python`
- **Workflow name**: `release.yml`
- **Environment name**: (leave empty)

### For Simple Manual Workflow
Add another trusted publisher:
- **Repository owner**: `PSPDFKit`
- **Repository name**: `nutrient-dws-client-python`
- **Workflow name**: `publish-manual.yml`
- **Environment name**: (leave empty)

## Important Notes

1. The workflow name must match EXACTLY (including the `.yml` extension)
2. Do NOT include `.github/workflows/` in the workflow name
3. Environment should be left empty unless you're using GitHub environments
4. The repository owner must match the GitHub organization/user exactly (case-sensitive)

## Alternative: Publish from v1.0.2 Tag

If you want to publish directly from the tag, you could:
1. Go to the v1.0.2 tag on GitHub
2. Run the `publish-manual.yml` workflow from that tag
3. This would make the ref claim match `refs/tags/v1.0.2`

## Debugging

To see what claims your workflow is sending:
1. Run the workflow again
2. Check the error message for the exact claims
3. Ensure your PyPI configuration matches those claims exactly

## Quick Test

After configuring the trusted publisher:
1. Try the simplest workflow first: `publish-manual.yml`
2. Run it from the main branch
3. If it works, then try the tag-specific workflows