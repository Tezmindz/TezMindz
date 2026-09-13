import json
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


def get_plugins_directory() -> Path:
    """
    Returns the absolute path to the frontend/static/games/plugins directory.
    """
    # BASE_DIR is Backend, parent is project root
    plugins_dir = settings.BASE_DIR.parent / "frontend" / "static" / "games" / "plugins"
    return plugins_dir


def discover_game_plugins():
    """
    Auto-discovers all game plugins by scanning frontend/static/games/plugins/
    for subdirectories containing game.manifest.json.

    Returns a dict mapping plugin_id -> manifest dict.
    """
    plugins_dir = get_plugins_directory()
    discovered = {}

    if not plugins_dir.exists() or not plugins_dir.is_dir():
        return discovered

    for entry in plugins_dir.iterdir():
        if entry.is_dir():
            manifest_file = entry / "game.manifest.json"
            if manifest_file.exists() and manifest_file.is_file():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                        plugin_id = manifest.get("id") or entry.name
                        manifest["id"] = plugin_id
                        manifest["directory"] = entry.name
                        discovered[plugin_id] = manifest
                except Exception as e:
                    logger.warning("Failed to load plugin manifest at %s: %s", manifest_file, e)

    return discovered


def get_plugin_choices():
    """
    Returns choices tuple for Django ModelChoiceField or CharField in admin.
    """
    plugins = discover_game_plugins()
    choices = []
    for plugin_id, manifest in sorted(plugins.items(), key=lambda x: x[1].get("name", x[0])):
        name = manifest.get("name", plugin_id)
        choices.append((plugin_id, f"{name} ({plugin_id})"))

    # Also keep legacy choices if needed for backward compatibility
    legacy_choices = [
        ("fraction_pizza", "Fraction pizza (fraction_pizza)"),
        ("house_builder", "House builder (house_builder)"),
        ("number_train", "Number train (number_train)"),
        ("science_sim", "Science simulation (science_sim)"),
        ("matching", "Matching game (matching)"),
        ("other", "Other (other)"),
    ]
    seen = {c[0] for c in choices}
    for val, label in legacy_choices:
        if val not in seen:
            choices.append((val, label))

    return choices
