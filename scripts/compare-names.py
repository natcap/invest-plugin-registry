# /// script
# requires-python = ">=3.6"
# dependencies = [
#   requests
# ]
# ///
import argparse
import difflib
import json
import os
import sys
import tomllib

import requests


REGISTRY_URL = 'https://natcap.github.io/invest-plugin-registry'


def _get_project_names_from_registry():
    resp = requests.get(f'{REGISTRY_URL}/metadata.json')
    resp.raise_for_status()

    return list(resp.json()['data'].keys())


def main(args=None):
    parser = argparse.ArgumentParser(os.path.basename(__file__))
    parser.add_argument("NEW_PLUGIN_JSON")
    parser.add_argument("MAIN_PLUGINS_JSON")
    parser.add_argument("NEW_PYPROJECT_TOML")
    parser.add_argument("TARGET_FILE")

    parsed_args = parser.parse_args(args)
    print(parsed_args)

    with open(parsed_args.NEW_PLUGIN_JSON, "r") as f:
        new_plugin_data = json.load(f)
    with open(parsed_args.MAIN_PLUGINS_JSON, "r") as f:
        main_plugins_data = json.load(f)

    new_name = new_plugin_data['plugin_name'].lower()
    existing_names = [plugin['plugin_name'].lower() for plugin in main_plugins_data]

    with open(parsed_args.NEW_PYPROJECT_TOML, 'rb') as tomlfile:
        pyproject_data = tomllib.load(tomlfile)
    pkg_name = pyproject_data['project']['name']
    existing_packages = _get_project_names_from_registry()

    with open(parsed_args.TARGET_FILE, 'w') as target_file:
        for user_provided_string, label, existing_strings in [
                (new_name, 'human-readable name', existing_names),
                (pkg_name, 'package name', existing_packages)]:
            matches = difflib.get_close_matches(user_provided_string, existing_strings, cutoff=0.85)
            if matches:
                best_match = matches[0]
                score = difflib.SequenceMatcher(None, new_name, best_match).ratio()
                if score == 1.0:
                    target_file.write(f"❌ plugin has the same {label} as an existing plugin\n")
                    parser.exit(1, f"Failing because plugin {label} is not unique")
                else:
                    target_file.write(
                        f"ℹ️  plugin {label} was found to be similar to existing plugin name(s): "
                        f"{matches}\n")
            else:
                target_file.write(f"✅ plugin {label} is unique!\n")


if __name__ == "__main__":
    main(sys.argv[1:])
