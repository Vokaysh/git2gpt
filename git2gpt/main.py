import argparse
import sys
import logging
import datetime

from git2gpt import git_operations, gpt_operations, utils
from git2gpt.version import version


def setup_logging() -> None:
    log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print(f"Logging webapi requests and responses to {log_filename}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Modify a git repo using GPT-4 suggestions or ask a question about the code."
    )
    utils.add_arguments(parser)
    args = parser.parse_args()

    if args.version:
        print(f'git2gpt version {version}')
        sys.exit(0)

    utils.validate_arguments(args)

    setup_logging()

    repo_path = args.repo
    prompt = args.prompt
    ask_question = args.ask
    force = args.force
    temperature = args.temperature

    snapshot = git_operations.get_repo_snapshot(repo_path)
    timeout = 0  # Set a default timeout value (in seconds)
    
    output, api_time = gpt_operations.send_request(snapshot, prompt, question=ask_question, temperature=temperature, timeout=timeout)

    if ask_question:
        print(f'Answer: {output}')
    else:
        mutations = gpt_operations.parse_mutations(output)
        git_operations.apply_gpt_mutations(repo_path, mutations)
        git_operations.display_diff(repo_path)
        decision = utils.get_user_decision("Do you want to keep the changes? (y/n): ", ['y', 'n'])
        if decision.lower() == 'y':
            git_operations.commit_changes(repo_path, f"git2gpt: {prompt}")
        else:
            print("No changes will be committed.")
            print("To discard the changes, run the following git command:")
            print("    git reset --hard HEAD")

    utils.print_execution_time_statistics(api_time)


if __name__ == "__main__":
    main()