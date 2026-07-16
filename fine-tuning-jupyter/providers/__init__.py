"""Provider registry with lazy loading to avoid import errors for missing packages."""

import importlib

# Registry: provider_name -> (module_name, required_env_vars)
PROVIDER_REGISTRY = {
    "whisper_local": ("whisper_local", []),
    "openai_whisper": ("openai_whisper", ["OPENAI_API_KEY"]),
    "assemblyai": ("assemblyai_stt", ["ASSEMBLYAI_API_KEY"]),
    "deepgram": ("deepgram_stt", ["DEEPGRAM_API_KEY"]),
    "google_stt": ("google_stt", ["GOOGLE_APPLICATION_CREDENTIALS"]),
    "gpt4o_audio": ("gpt4o_audio", ["OPENAI_API_KEY"]),
    "gemini_audio": ("gemini_audio", ["GEMINI_API_KEY"]),
    "whisper_finetuned": ("whisper_finetuned", []),
}


def get_provider(name: str):
    """Import a provider on demand and return its transcribe callable.

    Raises KeyError if name is unknown, ImportError if the module can't be loaded.
    """
    if name not in PROVIDER_REGISTRY:
        raise KeyError(f"Unknown provider: {name}")
    module_name, _ = PROVIDER_REGISTRY[name]
    mod = importlib.import_module(f".{module_name}", package="providers")
    return mod.transcribe


# Backward-compatible lazy PROVIDERS dict for CLI evaluate.py
class _LazyProviders(dict):
    """Dict that loads provider modules on first access."""

    def __init__(self):
        super().__init__()
        self._loaded = False

    def _load_all(self):
        if self._loaded:
            return
        self._loaded = True
        for name in PROVIDER_REGISTRY:
            try:
                self[name] = get_provider(name)
            except (ImportError, Exception) as e:
                import sys
                print(f"Warning: could not load provider '{name}': {e}", file=sys.stderr)

    def __getitem__(self, key):
        if not self._loaded:
            self._load_all()
        return super().__getitem__(key)

    def __contains__(self, key):
        if not self._loaded:
            self._load_all()
        return super().__contains__(key)

    def __iter__(self):
        if not self._loaded:
            self._load_all()
        return super().__iter__()

    def keys(self):
        if not self._loaded:
            self._load_all()
        return super().keys()

    def values(self):
        if not self._loaded:
            self._load_all()
        return super().values()

    def items(self):
        if not self._loaded:
            self._load_all()
        return super().items()

    def __len__(self):
        if not self._loaded:
            self._load_all()
        return super().__len__()


PROVIDERS = _LazyProviders()
