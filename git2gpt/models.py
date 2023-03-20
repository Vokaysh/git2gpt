from dotenv import load_dotenv
load_dotenv() # this must run before openai is imported

import openai
import tiktoken
import time

# stores configuration information for each type of model
model_data = {
    'gpt-4': {
        'window_size': 8192,
        'cost': {
            'prompt_tokens': 0.03 / 1000,
            'completion_tokens': 0.06 / 1000,
        },
    },  
    'gpt-4-32k': {
        'window_size': 32768,
        'cost': {
            'prompt_tokens': 0.06 / 1000,
            'completion_tokens': 0.012 / 1000,
        },
    },
    'gpt-3.5-turbo': {
        'window_size': 4096,
        'cost': {
            'prompt_tokens': 0.002 / 1000,
            'completion_tokens': 0.002 / 1000
        },
    }
}

# TODO: This seems to be overcounting by ~3 tokens at least with gpt-4.0
def count_tokens(messages, model):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    # this is how gpt-3.5-turbo-0301 works, might be different for future models.
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens

def get_response(messages, temperature=0.0, model="gpt-4"):
    print(f'Model: {model}')

    model_config = model_data[model]
    prompt_tokens = count_tokens(messages, model)
    avail_tokens = model_config["window_size"] - prompt_tokens
    print(f"Request {prompt_tokens} tokens, {avail_tokens} available for completion.")

    start_time = time.time()
    response = openai.ChatCompletion.create(
        model=model,
        max_tokens=avail_tokens,
        temperature=temperature,
        messages=messages,
    )
    time_taken = time.time() - start_time
    print(f'Request duration: {time_taken:.2f} seconds')

    prompt_tokens = response["usage"]["prompt_tokens"]
    prompt_cost = prompt_tokens * model_config["cost"]["prompt_tokens"]
    print(f'{prompt_tokens:5d} prompt tokens used. Cost: ${prompt_cost:.6f}')

    completion_tokens = response["usage"]["completion_tokens"]
    completion_cost = completion_tokens * model_config["cost"]["completion_tokens"]
    print(f'{completion_tokens:5d} completion tokens used. Cost: ${completion_cost:.6f}')

    total_tokens = response["usage"]["prompt_tokens"] + response["usage"]["completion_tokens"]
    total_cost = prompt_cost + completion_cost
    print(f'{total_tokens:5d} tokens total. Total cost: ${total_cost:.6f}')

    return response["choices"][0]["message"]["content"]