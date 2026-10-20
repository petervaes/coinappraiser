from dotenv import find_dotenv, load_dotenv


def load_environment() -> None:
    """Load the nearest local .env without overriding existing environment values."""
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
