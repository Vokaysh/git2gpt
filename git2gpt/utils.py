import argparse
import sys
from typing import List, Callable

def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--prompt",
        type=str,
        required=False,
        help="User prompt for specific desired changes"
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--ask",
        action="store_true",
        help="Ask a question about the code, rather than modify it",
    )
    parser.add_argument(
        "--editor",
        action="store_true",
        help="Open a temporary file with the user's preferred $EDITOR for providing the prompt",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force operation even with unstaged changes",
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=0.0,
        help="Specify the temperature for GPT-4 suggestions (default: 0.7)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display the current version of git2gpt",
    )

def validate_arguments(args: argparse.Namespace) -> None:
    if args.version:
        print(f'git2gpt version {version}')
        sys.exit(0)

    if not args.prompt:
        print('Error: No prompt provided. Please provide a prompt using --prompt or --editor.')
        sys.exit(1)

    if not args.force and git_operations.check_unstaged_changes(args.repo):
        print('Error: Unstaged changes detected. Please commit or stash them before running this script. To force the operation, use -f/--force flag.')
        sys.exit(1)

def get_user_decision(prompt: str, valid_choices: List[str]) -> str:
    while True:
        decision = input(prompt).lower()
        if decision in valid_choices:
            return decision
        else:
            print(f"Invalid choice. Please enter one of the following: {', '.join(valid_choices)}")

def print_execution_time_statistics(api_time: float) -> None:
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nExecution time statistics:")
    print(f"  WebAPI request: {api_time:.2f} seconds")
    print(f"  Total execution time: {total_time:.2f} seconds")