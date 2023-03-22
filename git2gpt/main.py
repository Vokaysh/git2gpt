import argparse
import json
import subprocess
import time
from typing import List, Dict, Any
import git2gpt.models as models
from git2gpt.models import get_response
from git2gpt.core import apply_gpt_mutations, get_repo_snapshot, get_tracked_files, commit_changes
from git2gpt.version import version
import re
from contextlib import contextmanager
from pathlib import Path
import os
import sys
import tempfile
import logging
import datetime


@contextmanager
def change_directory(path: str):
    original_path = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_path)

def get_user_decision(prompt: str, valid_choices: List[str]) -> str:
    while True:
        decision = input(prompt).lower()
        if decision in valid_choices:
            return decision
        else:
            print(f"Invalid choice. Please enter one of the following: {', '.join(valid_choices)}")

def parse_json(json_string: str) -> Any:
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        tempfile = 'error_log.json'
        with open(tempfile, 'w') as f:
            f.write(json_string)
        print(f"Invalid suggestions saved to {tempfile} for debugging.")
        raise

def parse_mutations(suggestions: str) -> List[Dict[str, Any]]:
    if suggestions.startswith("```"):
        suggestions = suggestions[8:-3]  # strip the "```json\n" and "```"
    suggestions = suggestions.replace("\n", " ")
    suggestions = re.sub(r'\\([^"\\/bfnrt])', r'\1', suggestions)
    mutations = parse_json(suggestions)
    if "error" in mutations[0]:
        print(f"Error: {mutations[0]['error']}")
        sys.exit(1)
    return mutations

def send_request(snapshot: str, prompt: str, question: bool = False, temperature: float = 0.0) -> str:
    messages = [
        {
            "role": "system",
            "content": f"You are a state of the art software development assistant. Here is a snapshot of some source code that you will be assisting a user with: {snapshot}",
        },
    ]
    if question:
        print(f'Asking the following question:\n{prompt}')
        messages.append({
            "role": "user",
            "content": f"Please refer to the source code snapshot and answer the following: {prompt}",
        })
    else:
        messages.append({
            "role": "system",
            "content": """Respond to the user's request with a list of mutations to apply to the repository, using the following JSON format.

A list of mutations. Each mutation in the list must include an action, a file_path, and a content (for insert and update operations). The action can be one of the following strings: 'add', 'modify', 'delete'.
It is extremely important that you do not reply in any way but with an exact JSON string. Do not supply markup or any explanations outside of the code itself.

In the case of an error you may respond with [{"error": "<your error message>"}] instead.  Never embed control characters in a JSON string.  If you do, the JSON parser will fail and you will be unable to respond to the user.
""",
        })
        messages.append({
            "role": "user",
            "content": f"Please carefully and thoroughly make the following changes: {prompt}",
        })
        print(f'Requesting the following changes:\n{prompt}')
    start_time = time.time()
    response = get_response(messages, temperature=temperature)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"WebAPI request took {elapsed_time:.2f} seconds")
    return response, elapsed_time

def display_diff(repo_path: str) -> None:
    tracked_files = get_tracked_files(repo_path)
    with change_directory(repo_path):
        for file in tracked_files:
            subprocess.run(["git", "diff", "--staged", "--", file])

def check_unstaged_changes(repo_path: str) -> bool:
    with change_directory(repo_path):
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return bool(result.stdout.strip())

def setup_logging():
    log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print(f"Logging webapi requests and responses to {log_filename}")

def main():
    parser = argparse.ArgumentParser(
        description="Modify a git repo using GPT-4 suggestions or ask a question about the code."
    )
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
    args = parser.parse_args()

    if args.version:
        print(f'git2gpt version {version}')
        sys.exit(0)

    repo_path = args.repo
    prompt = args.prompt
    ask_question = args.ask
    force = args.force
    temperature = args.temperature
    
    if not prompt:
        print('Error: No prompt provided. Please provide a prompt using --prompt or --editor.')
        sys.exit(1)

    if not force and check_unstaged_changes(repo_path):
        print('Error: Unstaged changes detected. Please commit or stash them before running this script. To force the operation, use -f/--force flag.')
        sys.exit(1)

    setup_logging()

    start_time = time.time()
    snapshot = get_repo_snapshot(repo_path)
    output, api_time = send_request(snapshot, prompt, question=ask_question, temperature=temperature)

    if ask_question:
        print(f'Answer: {output}')
    else:
        mutations = parse_mutations(output)
        apply_gpt_mutations(repo_path, mutations)
        display_diff(repo_path)
        decision = get_user_decision("Do you want to keep the changes? (y/n): ", ['y', 'n'])
        if decision.lower() == 'y':
            commit_changes(repo_path, f"git2gpt: {prompt}")
        else:
            print("No changes will be committed.")
            print("To discard the changes, run the following git command:")
            print("    git reset --hard HEAD")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nExecution time statistics:")
    print(f"  WebAPI request: {api_time:.2f} seconds")
    print(f"  Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()