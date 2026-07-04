import tiktoken


MAX_TOKENS = 2000

encoder = tiktoken.encoding_for_model(
    "gpt-3.5-turbo"
)


def count_tokens(text: str) -> int:

    return len(
        encoder.encode(text)
    )