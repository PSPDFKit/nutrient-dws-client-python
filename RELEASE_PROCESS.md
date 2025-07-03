# Release Process

This document describes how to release a new version of nutrient-dws to PyPI using GitHub's trusted publishing.

## Prerequisites

1. PyPI account with maintainer access to nutrient-dws
2. GitHub repository configured as a trusted publisher on PyPI
3. Write access to the GitHub repository

## Automatic Release Process (Recommended)

### For New Releases

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Commit changes: `git commit -m "chore: prepare release v1.0.x"`
4. Create and push tag: `git tag v1.0.x && git push origin v1.0.x`
5. Create GitHub release:
   - Go to https://github.com/PSPDFKit/nutrient-dws-client-python/releases/new
   - Select the tag you just created
   - Add release notes
   - Click "Publish release"
6. The `Release` workflow will automatically trigger and upload to PyPI

### For Existing Tags (like v1.0.2)

1. Go to Actions tab in GitHub
2. Select "Publish Existing Tag to PyPI" workflow
3. Click "Run workflow"
4. Enter the tag name (e.g., `v1.0.2`)
5. Click "Run workflow"
6. Monitor the workflow progress

## Manual Trigger

You can also manually trigger the release workflow:
1. Go to Actions tab
2. Select "Release" workflow  
3. Click "Run workflow"
4. Select branch/tag and run

## Verification

After publishing:
1. Check PyPI: https://pypi.org/project/nutrient-dws/
2. Test installation: `pip install nutrient-dws==1.0.x`
3. Verify the GitHub release page shows the release

## Troubleshooting

### Trusted Publisher Issues
- Ensure the GitHub repository is configured as a trusted publisher on PyPI
- Check that the workflow has `id-token: write` permission
- Verify the PyPI project name matches exactly

### Build Issues
- Ensure `pyproject.toml` is valid
- Check that all required files are present
- Verify Python version compatibility

## Security Notes

- No API tokens or passwords are needed with trusted publishing
- GitHub Actions uses OIDC to authenticate with PyPI
- This is more secure than storing PyPI tokens as secrets