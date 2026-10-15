"""Small Ollama REST client; no cloud services are used."""
import requests


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def tags(self) -> list[str]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=8)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except (requests.RequestException, ValueError, KeyError) as exc:
            raise OllamaError(f"Ollama is unreachable or returned invalid data: {exc}") from exc

    def embed(self, texts: list[str], model: str, batch_size: int = 16) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            try:
                response = requests.post(f"{self.base_url}/api/embed",
                    json={"model": model, "input": batch}, timeout=self.timeout)
                response.raise_for_status()
                data = response.json().get("embeddings", [])
                if len(data) != len(batch) or any(not isinstance(v, list) or not v for v in data):
                    raise OllamaError("Ollama returned missing or invalid embeddings.")
                vectors.extend(data)
            except requests.RequestException as exc:
                raise OllamaError(f"Embedding request failed: {exc}") from exc
        return vectors

    def generate(self, prompt: str, model: str) -> str:
        try:
            response = requests.post(f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0}}, timeout=self.timeout)
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            if not answer:
                raise OllamaError("Ollama returned an empty answer.")
            return answer
        except requests.RequestException as exc:
            raise OllamaError(f"Answer generation failed: {exc}") from exc
