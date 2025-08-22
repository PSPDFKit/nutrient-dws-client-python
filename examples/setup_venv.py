#!/usr/bin/env python3
"""
Setup script for creating and configuring the examples virtual environment.
This script creates a virtual environment and installs the nutrient-dws package
from the built distribution files.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        raise

def main():
    # Get the current directory (examples folder)
    examples_dir = Path(__file__).parent
    project_root = examples_dir.parent
    dist_dir = project_root / "dist"

    print(f"Setting up virtual environment in: {examples_dir}")

    # Create virtual environment
    venv_path = examples_dir / "example_venv"
    if venv_path.exists():
        print("Virtual environment already exists. Removing...")
        import shutil
        shutil.rmtree(venv_path)

    print("Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", "example_venv"], cwd=examples_dir)

    # Determine the python executable in the venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    run_command([str(pip_exe), "install", "--upgrade", "pip"])

    # Install the wheel and tar.gz files
    wheel_file = dist_dir / "nutrient_dws-2.0.0-py3-none-any.whl"
    tar_file = dist_dir / "nutrient_dws-2.0.0.tar.gz"

    if wheel_file.exists():
        print("Installing nutrient-dws from wheel...")
        run_command([str(pip_exe), "install", str(wheel_file)])
    elif tar_file.exists():
        print("Installing nutrient-dws from tar.gz...")
        run_command([str(pip_exe), "install", str(tar_file)])
    else:
        print("Error: Neither wheel nor tar.gz file found in dist directory")
        print("Please build the package first using: python -m build")
        sys.exit(1)

    # Install example requirements
    requirements_file = examples_dir / "requirements.txt"
    if requirements_file.exists():
        print("Installing example requirements...")
        run_command([str(pip_exe), "install", "-r", str(requirements_file)])

    print("\n" + "="*50)
    print("Virtual environment setup complete!")
    print(f"Virtual environment location: {venv_path}")
    print("\nTo activate the virtual environment:")
    if sys.platform == "win32":
        print(f"  {venv_path / 'Scripts' / 'activate.bat'}")
    else:
        print(f"  source {venv_path / 'bin' / 'activate'}")

    print("\nTo run examples:")
    print("  python src/direct_method.py")
    print("  python src/workflow.py")

if __name__ == "__main__":
    main()
