#!/usr/bin/env python3
"""
Simple wrapper script to handle MLX-Audio setup with UV.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for the application."""

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print("🚀 Starting MLX-Audio TTS Web Application...")

    # Try to run with UV environment first
    try:
        # Check if we can import required modules in UV environment
        result = subprocess.run([
            "uv", "run", "python", "-c",
            "import fastapi, uvicorn; print('✅ UV environment ready')"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("📦 Using UV environment")
            print(result.stdout.strip())

            # Try to check MLX-Audio
            mlx_result = subprocess.run([
                "uv", "run", "python", "-c", "import mlx_audio; print('✅ MLX-Audio available')"
            ], capture_output=True, text=True)

            if mlx_result.returncode == 0:
                print("🎯 MLX-Audio available in UV environment")
                print(mlx_result.stdout.strip())
                print("🌐 Starting server at http://localhost:8000")
                subprocess.run([
                    "uv", "run", "uvicorn", "backend.main:app",
                    "--host", "0.0.0.0", "--port", "8000", "--reload"
                ])
            else:
                print("⚠️  MLX-Audio not available in UV, trying miniconda3 fallback...")
                fallback_to_miniconda()
        else:
            print("❌ UV environment setup failed")
            print(result.stderr)
            sys.exit(1)

    except FileNotFoundError:
        print("❌ UV not found. Please install UV:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

def fallback_to_miniconda():
    """Fallback to miniconda3 for MLX-Audio."""
    python_path = "/Users/scrimwiggins/miniconda3/bin/python3"

    if not os.path.exists(python_path):
        print(f"❌ Python not found at {python_path}")
        print("   Please install MLX-Audio in your UV environment:")
        print("   uv add mlx-audio")
        sys.exit(1)

    print(f"🐍 Using miniconda3: {python_path}")

    # Install MLX-Audio if needed
    try:
        subprocess.run([python_path, "-c", "import mlx_audio"], check=True)
        print("✅ MLX-Audio available")
    except subprocess.CalledProcessError:
        print("📦 Installing MLX-Audio...")
        subprocess.run([python_path, "-m", "pip", "install", "mlx-audio"])

    print("🌐 Starting server at http://localhost:8000")
    subprocess.run([
        python_path, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ])

if __name__ == "__main__":
    main()