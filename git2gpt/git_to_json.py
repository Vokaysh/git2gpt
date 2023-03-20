import tarfile
import json
import io
import subprocess
import os
import sys
import string
import argparse


def is_binary_data(data):
    """Simple heuristic to check if data is binary."""
    text_chars = bytearray({ord(c) for c in string.printable})
    return bool(data.translate(None, text_chars))


def tar_to_json(tar_stream):
    json_structure = []

    with tarfile.open(mode="r|*", fileobj=tar_stream) as tar:
        for member in tar:
            if member.isfile():
                content = b""
                extracted_file = tar.extractfile(member)
                while True:
                    chunk = extracted_file.read(1024)
                    if not chunk:
                        break
                    content += chunk
                    if is_binary_data(content):
                        content = "<binary content>"
                        break
                if not isinstance(content, str):
                    content = content.decode(errors="replace")

            else:
                content = None

            json_structure.append(
                {
                    "name": member.name,
                    "type": "file" if member.isfile() else "directory",
                    "size": member.size,
                    "content": content,
                }
            )

    return json.dumps(json_structure, indent=2)


def git_archive_to_json(repo_path):
    os.chdir(repo_path)
    git_archive = subprocess.check_output(["git", "archive", "HEAD"])
    tar_stream = io.BytesIO(git_archive)
    return tar_to_json(tar_stream)