from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    search_api_key: str | None
    search_provider: str
    max_results: int
    top_k: int


def _load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        search_api_key=os.getenv("SEARCH_API_KEY"),
        search_provider=os.getenv("SEARCH_PROVIDER", "mock"),
        max_results=int(os.getenv("MAX_RESULTS", "20")),
        top_k=int(os.getenv("TOP_K", "5")),
    )


settings = _load_settings()
