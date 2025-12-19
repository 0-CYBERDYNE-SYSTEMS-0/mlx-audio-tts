"""
TTS Service Manager - Manages the lifecycle of the MLX-Audio TTS service.
Provides programmatic control over starting, stopping, and monitoring the service.
"""
import os
import sys
import time
import signal
import subprocess
import logging
import psutil
import socket
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import (
    PID_FILE, LOG_FILE, SERVER_HOST, SERVER_PORT,
    BASE_DIR, PRODUCTION_MODE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages the TTS service lifecycle programmatically.
    """

    def __init__(self):
        """Initialize TTS service manager."""
        self.pid_file = PID_FILE
        self.log_file = LOG_FILE
        self.host = SERVER_HOST
        self.port = SERVER_PORT

    def is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, port))
                return True
            except OSError:
                return False

    def find_available_port(self, start_port: int = 8000, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port."""
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port):
                return port
        raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts - 1}")

    def is_service_running(self) -> bool:
        """Check if the TTS service is currently running."""
        # Check PID file
        if not os.path.exists(self.pid_file):
            return False

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            if not psutil.pid_exists(pid):
                # PID file exists but process doesn't
                os.remove(self.pid_file)
                return False

            # Check if it's our process
            process = psutil.Process(pid)
            if 'python' not in process.name().lower():
                os.remove(self.pid_file)
                return False

            # Check if the service is responding
            if self._health_check():
                return True
            else:
                logger.warning(f"Process {pid} exists but service not responding")
                return False

        except (ValueError, FileNotFoundError, psutil.NoSuchProcess):
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            return False

    def _health_check(self) -> bool:
        """Check if the service health endpoint responds."""
        try:
            import requests
            response = requests.get(f"http://{self.host}:{self.port}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_service(
        self,
        production: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        wait_for_ready: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Start the TTS service.

        Args:
            production: Start in production mode
            host: Host to bind to (overrides config)
            port: Port to bind to (overrides config)
            wait_for_ready: Wait for service to be ready
            timeout: Timeout for waiting for service to be ready

        Returns:
            Dictionary with status information
        """
        if self.is_service_running():
            return {
                "status": "already_running",
                "message": f"TTS service is already running on {self.host}:{self.port}"
            }

        # Determine host and port
        host = host or self.host
        port = port or self.port

        # Find available port if the requested port is taken
        if not self.is_port_available(port):
            available_port = self.find_available_port(port)
            logger.warning(f"Port {port} is in use, using port {available_port}")
            port = available_port

        logger.info(f"Starting TTS service in {'production' if production else 'development'} mode")

        # Prepare environment
        env = os.environ.copy()
        if production:
            env["TTS_PRODUCTION"] = "true"
            env["TTS_HOST"] = host
            env["TTS_PORT"] = str(port)

        # Prepare command
        backend_dir = os.path.join(BASE_DIR, 'backend')
        main_module = os.path.join(backend_dir, 'main.py')

        cmd = [
            sys.executable,
            "-m", "uvicorn",
            "backend.main:app" if production else main_module,
            "--host", host,
            "--port", str(port),
            "--access-log" if production else "--no-access-log",
        ]

        if production:
            cmd.append("--log-level=info")
            # In production, we might want to run as a module
            cmd[1] = "-m"
            cmd[2] = "uvicorn"
            cmd[3] = "backend.main:app"
        else:
            cmd.append("--reload")

        # Start the process
        try:
            # Create log directory if it doesn't exist
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            with open(self.log_file, 'a') as log_f:
                process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    env=env,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )

            # Write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))

            logger.info(f"Started TTS service with PID {process.pid}")

            # Wait for service to be ready
            if wait_for_ready:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if self._health_check():
                        logger.info(f"TTS service is ready at http://{host}:{port}")
                        return {
                            "status": "started",
                            "pid": process.pid,
                            "host": host,
                            "port": port,
                            "url": f"http://{host}:{port}"
                        }
                    time.sleep(1)

                # Service didn't start properly
                self.stop_service()
                raise RuntimeError(f"TTS service failed to start within {timeout} seconds")

            return {
                "status": "started",
                "pid": process.pid,
                "host": host,
                "port": port,
                "url": f"http://{host}:{port}"
            }

        except Exception as e:
            logger.error(f"Failed to start TTS service: {e}")
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            raise

    def stop_service(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Stop the TTS service.

        Args:
            timeout: Timeout for graceful shutdown

        Returns:
            Dictionary with status information
        """
        if not self.is_service_running():
            return {
                "status": "not_running",
                "message": "TTS service is not running"
            }

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            logger.info(f"Stopping TTS service (PID: {pid})")

            try:
                process = psutil.Process(pid)

                # Try graceful shutdown first
                process.terminate()

                # Wait for process to terminate
                try:
                    process.wait(timeout=timeout)
                    logger.info("TTS service stopped gracefully")
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning("Graceful shutdown timed out, forcing kill")
                    process.kill()
                    process.wait(timeout=5)
                    logger.info("TTS service killed")

            except psutil.NoSuchProcess:
                logger.info("Process already terminated")

            # Clean up PID file
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)

            return {
                "status": "stopped",
                "message": "TTS service stopped successfully"
            }

        except Exception as e:
            logger.error(f"Error stopping TTS service: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def restart_service(self, **kwargs) -> Dict[str, Any]:
        """Restart the TTS service."""
        logger.info("Restarting TTS service")
        self.stop_service()
        time.sleep(2)  # Brief pause
        return self.start_service(**kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the TTS service."""
        if not self.is_service_running():
            return {
                "status": "stopped",
                "host": self.host,
                "port": self.port,
                "pid_file": self.pid_file,
                "log_file": self.log_file
            }

        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Get process details
            process = psutil.Process(pid)
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()

            # Get service health
            import requests
            try:
                health_response = requests.get(f"http://{self.host}:{self.port}/health", timeout=5)
                health = health_response.json() if health_response.status_code == 200 else None
            except:
                health = None

            return {
                "status": "running",
                "pid": pid,
                "host": self.host,
                "port": self.port,
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "uptime": time.time() - process.create_time(),
                "health": health,
                "log_file": self.log_file
            }

        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def tail_logs(self, lines: int = 50) -> str:
        """Get the last N lines from the service log."""
        if not os.path.exists(self.log_file):
            return "Log file does not exist"

        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error reading log file: {e}"


# Convenience function for ensuring service is running
def ensure_tts_service(
    auto_start: bool = True,
    production: bool = True,
    **kwargs
) -> TTSManager:
    """
    Ensure TTS service is running, start it if needed.

    Args:
        auto_start: Automatically start service if not running
        production: Start in production mode
        **kwargs: Additional arguments for start_service

    Returns:
        TTSManager instance
    """
    manager = TTSManager()

    if not manager.is_service_running():
        if auto_start:
            logger.info("TTS service not running, starting it...")
            result = manager.start_service(production=production, **kwargs)
            if result["status"] != "started":
                raise RuntimeError(f"Failed to start TTS service: {result}")
        else:
            logger.warning("TTS service is not running")

    return manager


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TTS Service Manager")
    parser.add_argument("command", choices=["start", "stop", "restart", "status", "logs"])
    parser.add_argument("--port", type=int, help="Port to use")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--dev", action="store_true", help="Start in development mode")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for service to be ready")
    parser.add_argument("--log-lines", type=int, default=50, help="Number of log lines to show")

    args = parser.parse_args()

    manager = TTSManager()

    if args.command == "start":
        result = manager.start_service(
            production=not args.dev,
            host=args.host,
            port=args.port,
            wait_for_ready=not args.no_wait
        )
        print(json.dumps(result, indent=2))

    elif args.command == "stop":
        result = manager.stop_service()
        print(json.dumps(result, indent=2))

    elif args.command == "restart":
        result = manager.restart_service(
            production=not args.dev,
            host=args.host,
            port=args.port
        )
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "logs":
        logs = manager.tail_logs(args.log_lines)
        print(logs)