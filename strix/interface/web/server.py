"""
Web server entry point for Strix web interface.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from strix.interface.utils import check_docker_connection
from .api import app


logger = logging.getLogger(__name__)


def validate_environment() -> bool:
    """Validate required environment variables for web interface."""
    console = Console()
    missing_vars = []
    
    if not os.getenv("STRIX_LLM"):
        missing_vars.append("STRIX_LLM")
    
    has_base_url = any([
        os.getenv("LLM_API_BASE"),
        os.getenv("OPENAI_API_BASE"),
        os.getenv("LITELLM_BASE_URL"),
        os.getenv("OLLAMA_API_BASE"),
    ])
    
    if not os.getenv("LLM_API_KEY") and not has_base_url:
        missing_vars.append("LLM_API_KEY")
    
    if missing_vars:
        error_text = Text()
        error_text.append("❌ ", style="bold red")
        error_text.append("MISSING REQUIRED ENVIRONMENT VARIABLES", style="bold red")
        error_text.append("\n\n", style="white")
        
        for var in missing_vars:
            error_text.append(f"• {var}", style="bold yellow")
            error_text.append(" is not set\n", style="white")
        
        error_text.append("\nRequired environment variables:\n", style="white")
        error_text.append("• STRIX_LLM - Model name (e.g., 'openai/gpt-5')\n", style="white")
        error_text.append("• LLM_API_KEY - API key for the LLM provider\n", style="white")
        
        error_text.append("\nExample setup:\n", style="white")
        error_text.append("export STRIX_LLM='openai/gpt-5'\n", style="dim white")
        error_text.append("export LLM_API_KEY='your-api-key-here'\n", style="dim white")
        
        panel = Panel(
            error_text,
            title="[bold red]🛡️  STRIX WEB INTERFACE CONFIGURATION ERROR",
            title_align="center",
            border_style="red",
            padding=(1, 2),
        )
        
        console.print("\n")
        console.print(panel)
        console.print()
        return False
    
    return True


def check_docker() -> bool:
    """Check Docker availability."""
    console = Console()
    
    try:
        check_docker_connection()
        return True
    except Exception as e:
        error_text = Text()
        error_text.append("❌ ", style="bold red")
        error_text.append("DOCKER CONNECTION FAILED", style="bold red")
        error_text.append("\n\n", style="white")
        error_text.append("Could not connect to Docker daemon.\n", style="white")
        error_text.append("Please ensure Docker is running and accessible.\n", style="white")
        error_text.append(f"\nError: {e}", style="dim white")
        
        panel = Panel(
            error_text,
            title="[bold red]🛡️  STRIX WEB INTERFACE DOCKER ERROR",
            title_align="center",
            border_style="red",
            padding=(1, 2),
        )
        
        console.print("\n")
        console.print(panel)
        console.print()
        return False


def display_startup_message(host: str, port: int):
    """Display startup message with access information."""
    console = Console()
    
    startup_text = Text()
    startup_text.append("🦉 ", style="bold white")
    startup_text.append("STRIX WEB INTERFACE STARTED", style="bold green")
    
    access_text = Text()
    access_text.append("🌐 Web Interface: ", style="bold cyan")
    access_text.append(f"http://{host}:{port}", style="bold white")
    
    api_text = Text()
    api_text.append("📚 API Documentation: ", style="bold cyan")
    api_text.append(f"http://{host}:{port}/api/docs", style="bold white")
    
    info_text = Text()
    info_text.append("\n💡 ", style="dim")
    info_text.append("Developers can now access the self-service penetration testing interface", style="dim")
    
    startup_panel = Panel(
        Text.assemble(
            startup_text,
            "\n\n",
            access_text,
            "\n",
            api_text,
            info_text,
        ),
        title="[bold green]🛡️  STRIX CYBERSECURITY AGENT",
        title_align="center",
        border_style="green",
        padding=(1, 2),
    )
    
    console.print("\n")
    console.print(startup_panel)
    console.print()


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Strix Web Interface - Self-service penetration testing for developers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start web interface on default port
  strix-web

  # Start on specific host and port
  strix-web --host 0.0.0.0 --port 8080

  # Start with debug logging
  strix-web --debug
        """,
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the web server (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=12000,
        help="Port to bind the web server (default: 12000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the web interface."""
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Check Docker
    if not check_docker():
        sys.exit(1)
    
    # Display startup message
    display_startup_message(args.host, args.port)
    
    # Configure uvicorn
    uvicorn_config = {
        "app": app,
        "host": args.host,
        "port": args.port,
        "log_level": "debug" if args.debug else "info",
        "access_log": True,
        "reload": args.reload,
    }
    
    # Start the server
    try:
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[bold yellow]🛑 Strix Web Interface stopped by user[/]")
    except Exception as e:
        console = Console()
        console.print(f"\n[bold red]❌ Failed to start web interface: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()