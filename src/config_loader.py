"""Load API keys from config/api_keys.py."""

import importlib.util
import sys
from pathlib import Path


def load_api_keys(config_path=None):
    """Return a dict of API keys from config/api_keys.py.

    Keys returned: CENSUS_API_KEY, BEA_API_KEY, EIA_API_KEY, FBI_API_KEY.
    Missing or empty keys are returned as empty strings.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "config" / "api_keys.py"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"API key file not found: {config_path}\n"
            "Copy config/api_keys.py.template to config/api_keys.py and add your keys."
        )

    spec = importlib.util.spec_from_file_location("api_keys", config_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    expected = ["CENSUS_API_KEY", "BEA_API_KEY", "EIA_API_KEY", "FBI_API_KEY"]
    keys = {}
    for name in expected:
        keys[name] = getattr(mod, name, "")
    return keys
