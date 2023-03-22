**Create chat completion**

URL: `https://api.openai.com/v1/chat/completions`

Creates a completion for the chat message.

**Request body**

- `model` (string, required): ID of the model to use.
- `messages` (array, required): The messages to generate chat completions for, in the chat format.
- `temperature` (number, optional, default: 1): Sampling temperature between 0 and 2.
- `top_p` (number, optional, default: 1): Nucleus sampling with top_p probability mass.
- `n` (integer, optional, default: 1): Number of chat completion choices to generate.
- `stream` (boolean, optional, default: false): Send partial message deltas as server-sent events.
- `stop` (string or array, optional, default: null): Up to 4 sequences where the API will stop generating tokens.
- `max_tokens` (integer, optional, default: inf): Maximum number of tokens to generate in the chat completion.
- `presence_penalty` (number, optional, default: 0): Number between -2.0 and 2.0 to penalize new tokens based on their presence in the text so far.
- `frequency_penalty` (number, optional, default: 0): Number between -2.0 and 2.0 to penalize new tokens based on their frequency in the text so far.
- `logit_bias` (map, optional, default: null): Modify the likelihood of specified tokens appearing in the completion by mapping token IDs to bias values from -100 to 100.
- `user` (string, optional): A unique identifier representing your end-user, helping OpenAI to monitor and detect abuse.