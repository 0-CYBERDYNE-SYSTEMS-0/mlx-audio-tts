#!/bin/bash

# MLX-Audio TTS Service Installation Script
# Sets up the TTS service for background operation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on Apple Silicon
check_architecture() {
    if [[ $(uname -m) != "arm64" ]]; then
        print_error "MLX-Audio requires Apple Silicon (arm64) architecture"
        exit 1
    fi
    print_success "Apple Silicon architecture detected"
}

# Check if we're on macOS
check_os() {
    if [[ $(uname) != "Darwin" ]]; then
        print_error "MLX-Audio only supports macOS"
        exit 1
    fi
    print_success "macOS detected"
}

# Check Python installation
check_python() {
    # Look for Python in miniconda3 first (as required by the application)
    PYTHON_PATH="/Users/scrimwiggins/miniconda3/bin/python3"

    if [[ -x "$PYTHON_PATH" ]]; then
        print_success "Found Python at $PYTHON_PATH"
        export PYTHON_PATH
    else
        # Check if python3 is available
        if command -v python3 &> /dev/null; then
            PYTHON_PATH=$(which python3)
            print_warning "Using system Python at $PYTHON_PATH"
            print_warning "MLX-Audio may require miniconda3 installation"
        else
            print_error "Python 3 not found. Please install Python 3.12+"
            exit 1
        fi
    fi
}

# Install UV package manager if not present
install_uv() {
    if command -v uv &> /dev/null; then
        print_success "UV package manager is already installed"
    else
        print_status "Installing UV package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"

        # Add to shell profile if not already there
        if ! grep -q 'cargo/bin' ~/.zshrc 2>/dev/null; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
        fi

        print_success "UV installed successfully"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies with UV..."

    if command -v uv &> /dev/null; then
        uv sync
        print_success "Dependencies installed with UV"
    else
        print_warning "UV not found, using pip..."
        $PYTHON_PATH -m pip install -r requirements.txt
    fi

    # Install MLX-Audio with the correct Python
    print_status "Installing MLX-Audio..."
    $PYTHON_PATH -m pip install mlx-audio
    print_success "MLX-Audio installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating service directories..."

    mkdir -p logs
    mkdir -p pids
    mkdir -p uploads
    mkdir -p outputs

    # Set permissions
    chmod 755 logs pids uploads outputs

    print_success "Directories created"
}

# Create helper scripts
create_helper_scripts() {
    print_status "Creating helper scripts..."

    # Create start_tts_service script
    cat > start_tts_service.sh << 'EOF'
#!/bin/bash
# Start TTS Service

cd "$(dirname "$0")"

# Activate environment if using UV
if command -v uv &> /dev/null; then
    export PATH="$HOME/.cargo/bin:$PATH"
    uv run python -m backend.main --production
else
    /Users/scrimwiggins/miniconda3/bin/python3 -m backend.main --production
fi
EOF

    # Create stop_tts_service script
    cat > stop_tts_service.sh << 'EOF'
#!/bin/bash
# Stop TTS Service

cd "$(dirname "$0")"
python3 service/tts_manager.py stop
EOF

    # Create status_tts_service script
    cat > status_tts_service.sh << 'EOF'
#!/bin/bash
# Check TTS Service Status

cd "$(dirname "$0")"
python3 service/tts_manager.py status
EOF

    # Make scripts executable
    chmod +x start_tts_service.sh stop_tts_service.sh status_tts_service.sh

    print_success "Helper scripts created"
}

# Test the installation
test_installation() {
    print_status "Testing TTS service installation..."

    # Test import
    if $PYTHON_PATH -c "import mlx_audio; print('MLX-Audio imported successfully')" 2>/dev/null; then
        print_success "MLX-Audio is working"
    else
        print_warning "MLX-Audio import failed - this might be expected until first use"
    fi

    # Test service manager
    if $PYTHON_PATH -c "from service.tts_manager import TTSManager; print('Service manager imported successfully')" 2>/dev/null; then
        print_success "Service manager is working"
    else
        print_error "Service manager import failed"
        exit 1
    fi

    # Test client
    if $PYTHON_PATH -c "from client.tts_client import TTSClient; print('TTS client imported successfully')" 2>/dev/null; then
        print_success "TTS client is working"
    else
        print_error "TTS client import failed"
        exit 1
    fi
}

# Create example agent integration
create_example() {
    print_status "Creating example agent integration..."

    cat > example_agent.py << 'EOF'
#!/usr/bin/env python3
"""
Example agent using TTS integration
"""

from scripts.agent_integration import initialize_tts, speak

def main():
    print("Initializing TTS...")
    tts = initialize_tts(auto_start=True)

    print("Generating speech...")
    audio = speak("Hello! I am an AI assistant with voice capabilities.")

    print(f"Generated {len(audio)} bytes of audio")

    # Here you would:
    # 1. Play the audio through speakers
    # 2. Or save it to a file
    # 3. Or stream it to a client

    # Example: Save to file
    with open("output.wav", "wb") as f:
        f.write(audio)
    print("Audio saved to output.wav")

if __name__ == "__main__":
    main()
EOF

    chmod +x example_agent.py

    print_success "Example agent created"
}

# Print final instructions
print_instructions() {
    echo
    print_success "Installation complete!"
    echo
    echo "Quick Start:"
    echo "-----------"
    echo "1. Start the TTS service:"
    echo "   ./start_tts_service.sh"
    echo
    echo "2. Check service status:"
    echo "   ./status_tts_service.sh"
    echo
    echo "3. Stop the service:"
    echo "   ./stop_tts_service.sh"
    echo
    echo "4. Run the example agent:"
    echo "   ./example_agent.py"
    echo
    echo "5. Test the client:"
    echo "   python3 -c \"from client.tts_client import create_speech; audio = create_speech('Hello world'); print(f'Generated {len(audio)} bytes')\""
    echo
    echo "Integration in Your Agent:"
    echo "--------------------------"
    echo "from scripts.agent_integration import initialize_tts, speak"
    echo
    echo "# Initialize at startup"
    echo "initialize_tts(auto_start=True)"
    echo
    echo "# Generate speech anytime"
    echo "audio = speak('Your text here')"
    echo
    print_warning "Note: The TTS service runs on http://localhost:8000 by default"
    print_warning "Make sure port 8000 is available"
}

# Main installation flow
main() {
    echo "=========================================="
    echo "MLX-Audio TTS Service Installation"
    echo "=========================================="
    echo

    check_architecture
    check_os
    check_python

    echo
    print_status "Starting installation..."
    echo

    install_uv
    install_dependencies
    create_directories
    create_helper_scripts
    test_installation
    create_example

    echo
    print_instructions

    echo
    print_success "TTS service is ready to use!"
}

# Run installation
main "$@"