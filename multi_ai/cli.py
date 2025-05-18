import os
import sys
import argparse
import asyncio
import json
from typing import Dict, Any, Optional, List

from .services.comparator import Comparator
from .utils.helpers import (
    load_env_file,
    format_response,
    save_to_file,
    create_default_env_file,
)
from .config import AVAILABLE_MODELS


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-AI - Compare responses from multiple LLM providers"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare LLM responses")
    compare_parser.add_argument(
        "prompt", help="Prompt to send to the models", nargs="?", default=None
    )
    compare_parser.add_argument(
        "--file", "-f", help="Read prompt from file instead of command line"
    )
    compare_parser.add_argument(
        "--output", "-o", help="Save results to file instead of printing"
    )
    compare_parser.add_argument(
        "--blend",
        "-b",
        action="store_true",
        help="Blend responses instead of selecting one",
    )
    compare_parser.add_argument(
        "--details", "-d", action="store_true", help="Include details in the output"
    )

    # Models for each provider
    compare_parser.add_argument(
        "--openai",
        help=f"OpenAI model to use (default: {AVAILABLE_MODELS['openai']['default']})",
    )
    compare_parser.add_argument(
        "--anthropic",
        help=f"Anthropic model to use (default: {AVAILABLE_MODELS['anthropic']['default']})",
    )
    compare_parser.add_argument(
        "--gemini",
        help=f"Google Gemini model to use (default: {AVAILABLE_MODELS['gemini']['default']})",
    )

    # List models command
    subparsers.add_parser("models", help="List available models")

    # Setup command
    setup_parser = subparsers.add_parser(
        "setup", help="Setup API keys and configuration"
    )
    setup_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing configuration"
    )

    return parser.parse_args()


async def compare(
    prompt: str,
    models: Optional[Dict[str, str]] = None,
    blend: bool = False,
    include_details: bool = True,
) -> Dict[str, Any]:
    """Compare LLM responses."""
    comparator = Comparator(use_blending=blend)
    result = await comparator.compare(prompt, models)
    return format_response(result, include_details)


def setup_config(force: bool = False) -> None:
    """Setup API keys and configuration."""
    env_file = ".env"

    if os.path.exists(env_file) and not force:
        print(f"{env_file} already exists. Use --force to overwrite.")
        return

    create_default_env_file(env_file)
    print(f"Created {env_file} file. Please edit it to add your API keys.")


def list_models() -> None:
    """List available models."""
    print("Available models:")

    for provider, info in AVAILABLE_MODELS.items():
        print(f"\n{provider.upper()} (default: {info['default']})")
        print("-" * (len(provider) + 15))

        for model in info["models"]:
            print(f"  {model['id']} - {model['name']}")


def get_prompt(args) -> str:
    """Get prompt from command line or file."""
    if args.file:
        with open(args.file, "r") as f:
            return f.read()

    if args.prompt:
        return args.prompt

    # If no prompt is provided, read from stdin
    if not sys.stdin.isatty():
        return sys.stdin.read()

    print("Error: No prompt provided. Use positional argument, --file, or pipe input.")
    sys.exit(1)


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    load_env_file()

    if args.command == "models":
        list_models()
        return

    if args.command == "setup":
        setup_config(args.force)
        return

    if args.command == "compare":
        prompt = get_prompt(args)

        # Build model config from args
        models = {}
        if args.openai:
            models["openai"] = args.openai
        if args.anthropic:
            models["anthropic"] = args.anthropic
        if args.gemini:
            models["gemini"] = args.gemini

        # If no models specified, use empty dict for defaults
        if not models:
            models = None

        # Run the comparison
        result = asyncio.run(compare(prompt, models, args.blend, args.details))

        # Save or print the result
        if args.output:
            save_to_file(args.output, result)
            print(f"Results saved to {args.output}")
        else:
            # Just print the result
            print(json.dumps(result, indent=2))
    else:
        print("No command specified. Use 'compare', 'models', or 'setup'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
