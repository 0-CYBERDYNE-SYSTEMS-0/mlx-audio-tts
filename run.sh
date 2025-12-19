#!/bin/bash

# MLX-Audio TTS Web Application Launcher
echo "🚀 Starting MLX-Audio TTS Web Application with UV..."
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: UV not found. Please install UV first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install/update dependencies with UV
echo "📦 Installing dependencies with UV..."
uv sync

# Check if MLX-Audio is available (requires special handling for miniconda3)
if ! uv run python -c "import mlx_audio" 2>/dev/null; then
    echo "⚠️  MLX-Audio not found through UV, falling back to miniconda3..."

    # Fall back to miniconda3 for MLX-Audio specifically
    PYTHON_PATH="/Users/scrimwiggins/miniconda3/bin/python3"
    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Error: Python not found at $PYTHON_PATH"
        echo "   Please install MLX-Audio in your UV environment:"
        echo "   uv add mlx-audio"
        exit 1
    fi

    # Install MLX-Audio with miniconda3 if needed
    if ! $PYTHON_PATH -c "import mlx_audio" 2>/dev/null; then
        echo "Installing MLX-Audio with miniconda3..."
        $PYTHON_PATH -m pip install mlx-audio
    fi

    # Start server with miniconda3
    echo ""
    echo "=========================================="
    echo "🎤 MLX-Audio TTS Generator (miniconda3 mode)"
    echo "=========================================="
    echo "📂 Project: $(pwd)"
    echo "🐍 Python: $PYTHON_PATH"
    echo "🌐 Server: http://localhost:8000"
    echo "=========================================="
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    $PYTHON_PATH -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
else
    # Start server with UV
    echo ""
    echo "=========================================="
    echo "🎤 MLX-Audio TTS Generator (UV mode)"
    echo "=========================================="
    echo "📂 Project: $(pwd)"
    echo "🐍 Python: $(uv run python --version)"
    echo "🌐 Server: http://localhost:8000"
    echo "=========================================="
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi
