import io
import json
import os
import string
import subprocess
import tarfile
from typing import List, Dict, Any


def is_binary_data(data : bytes) -> bool:
    """Simple heuristic to check if data is binary."""
    text_chars = bytearray({ord(c) for c in string.printable})
    return bool(data.translate(None, text_chars))


def get_snapshot(tar_stream : io.BytesIO) -> List[Dict[str, Any]]:
    """Takes a tar stream and returns a list of dicts with the file name and content."""
    snapshot = []
    with tarfile.open(mode="r|*", fileobj=tar_stream) as tar:
        for member in tar:
            if not member.isfile():
                continue

            content = b""
            extracted_file = tar.extractfile(member)
            while True:
                chunk = extracted_file.read(1024)
                if not chunk:
                    break
                if is_binary_data(chunk):
                    content = "<binary content>"
                    break
                content += chunk
            if isinstance(content, bytes):
                content = content.decode(errors="replace")
            snapshot.append({
                "name": member.name,
                "content": content,
            })
    return snapshot

def get_repo_snapshot(repo_path: str) -> str:
    os.chdir(repo_path)
    git_archive = subprocess.check_output(["git", "archive", "HEAD"])
    tar_stream = io.BytesIO(git_archive)
    return json.dumps(get_snapshot(tar_stream))


def get_tracked_files(repo_path: str) -> List[str]:
    os.chdir(repo_path)
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    tracked_files = result.stdout.splitlines()
    return tracked_files


def apply_gpt_mutations(repo_path: str, mutations: List[Dict[str, Any]]) -> None:
    os.chdir(repo_path)
    for mutation in mutations:
        action = mutation["action"]
        file_path = mutation["file_path"]
        if action == "add":
            with open(file_path, "w") as f:
                f.write(mutation["content"])
            subprocess.run(["git", "add", file_path])
        elif action == "modify":
            with open(file_path, "w") as f:
                f.write(mutation["content"])
            subprocess.run(["git", "add", file_path])
        elif action == "delete":
            if os.path.isfile(file_path):
                os.remove(file_path)
                subprocess.run(["git", "rm", file_path])
            elif os.path.isdir(file_path):
                try:
                    os.rmdir(file_path)
                    subprocess.run(["git", "rm", "-rf", file_path])
                except OSError as e:
                    print(
                        f"Error while trying to remove the directory {file_path}: {e}"
                    )


def commit_changes(repo_path: str, commit_message: str) -> None:
    os.chdir(repo_path)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", commit_message])
