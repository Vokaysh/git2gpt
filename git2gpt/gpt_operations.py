import time
from typing import List, Dict, Any, Tuple

from git2gpt import models, utils


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

def send_request(snapshot: str, prompt: str, question: bool = False, temperature: float = 0.0, timeout: float = None) -> Tuple[str, float]:
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