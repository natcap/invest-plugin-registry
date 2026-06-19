# /// script
# requires-python = ">=3.6"
# dependencies = [
#     "pytest",
# ]
# ///
import argparse
import functools
import hashlib
import json
import logging
import os
import shutil
import tempfile
import textwrap
import unittest

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def _hashdict(source_dict):
    """Hash the contents of a dict for easier comparison."""
    encoded_data = json.dumps(source_dict).encode('utf-8')
    return hashlib.sha256(encoded_data, usedforsecurity=False).hexdigest()


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('pr_plugins_json', default='plugins.json')  # filepath to the local plugins json
    parser.add_argument('reference_plugins_json', default='main_plugins.json')
    parser.add_argument('target_json', default='new_content.json')

    parsed_args = parser.parse_args(args)

    try:
        with open(parsed_args.reference_plugins_json) as reference_json_file:
            reference_json = json.load(reference_json_file)
            LOGGER.debug(f"Reference json: {reference_json}")
    except json.JSONDecodeError as error:
        LOGGER.exception(f"Could not parse JSON file: {error}")
        parser.exit(1, "Could not parse the reference JSON file")

    try:
        with open(parsed_args.pr_plugins_json) as pr_json_file:
            pr_json = json.load(pr_json_file)
            LOGGER.debug(f"PR json: {pr_json}")
    except json.JSONDecodeError as error:
        LOGGER.exception(f"Could not parse JSON file: {error}")
        parser.exit(1, "Could not parse the PR JSON file")

    # Fail if no change to the pr json file.
    if pr_json == reference_json:
        parser.exit(2, "No changes found in the plugins json file.")

    # Fail if there isn't 1 more item in the pr json file than the reference.
    _serialize = functools.partial(json.dumps, sort_keys=True)
    pr_json_set = set(_serialize(d) for d in pr_json)
    reference_json_set = set(_serialize(d) for d in reference_json)

    # make sure that the only change is to the PR json
    if not (len(pr_json_set - reference_json_set) == 1 and
            len(reference_json_set - pr_json_set) == 0):
        parser.exit(
            3, ("Expected exactly 1 new object and that the reference JSON "
                "is unchanged"))

    # Compare individual entries to ensure all entries are unchanged
    source_data_hashed = {}
    for data_dict in reference_json:
        source_data_hashed[_hashdict(data_dict)] = data_dict

    nonmatching_data = []
    for data_dict in pr_json:
        data_hash = _hashdict(data_dict)
        if data_hash not in source_data_hashed:
            nonmatching_data.append(data_dict)

    if len(nonmatching_data) != 1:
        parser.exit(
            4, (
            "Some data in the json file has been modified relative to "
            f"{parsed_args._reference_git_ref}"))

    # We should now be confident that only the one object remains.
    # Extract it and return the git URL.
    # The entry (and all others) is linted in a different script.
    with open(parsed_args.target_json, 'w') as target_json_file:
        target_json_file.write(
            json.dumps(nonmatching_data[0], indent=4, sort_keys=True))


class TestExtractModifiedJSON(unittest.TestCase):
    """Test suite for the extract-modified-json CLI functionality."""

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.reference_file = os.path.join(self.tempdir, 'ref.json')
        with open(self.reference_file, 'w') as ref_json:
            # Most basic reference json file has no data in it, just an empty
            # list.
            json.dump([], ref_json)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_extracted_changes(self):
        """Verify behavior when changes work as expected."""
        new_plugin_json_data = [
            {
                "repo_url": "https://github.com/natcap/invest-routedem-tfa-range.git",
                "plugin_name": "RouteDEM with TFA Range",
                "version": "1.0.0",
                "plugin_type": "invest_model_variant",
                "keywords": ["RouteDEM", "hydrology", "streams", "routing"]
            }
        ]
        new_plugin_data_file_path = os.path.join(self.tempdir, 'new.json')
        with open(new_plugin_data_file_path, 'w') as new_plugin_file:
            json.dump(new_plugin_json_data, new_plugin_file)

        target_json_file_path = os.path.join(self.tempdir, 'target.json')

        main([new_plugin_data_file_path, self.reference_file,
              target_json_file_path])

        with open(target_json_file_path, 'r') as target_json_file:
            self.assertEqual(new_plugin_json_data[0], json.load(target_json_file))

    def test_no_changes(self):
        """Verify behavior when no changes found."""
        # When no changes, then new file is a copy of the reference json.
        new_file = os.path.join(self.tempdir, 'new_file.json')
        shutil.copy(self.reference_file, new_file)

        target_file = os.path.join(self.tempdir, 'target.json')
        with self.assertRaises(SystemExit):
            main([new_file, self.reference_file, target_file])

    def test_invalid_pr_json(self):
        """Verify error when pr json could not be parsed."""
        # Need to write out a json object that isn't valid json.
        new_filepath = os.path.join(self.tempdir, 'newfile.json')
        with open(new_filepath, 'w') as new_file:
            new_file.write(textwrap.dedent(
                """\
                [
                {
                    "foo": "bar",
                },
                ]
                """))

        target_file = os.path.join(self.tempdir, 'target.json')
        with self.assertRaises(SystemExit):
            main([new_filepath, self.reference_file, target_file])

    def test_invalid_reference_json(self):
        """Verify error when reference json could not be parsed."""
        with open(self.reference_file, 'w') as ref_file:
            ref_file.write(textwrap.dedent(
                """\
                [],
                """))

        new_filepath = os.path.join(self.tempdir, 'newfile.json')
        with open(new_filepath, 'w') as new_file:
            json.dump({}, new_file)

        target_file = os.path.join(self.tempdir, 'target.json')
        with self.assertRaises(SystemExit):
            main([new_filepath, self.reference_file, target_file])

    def test_both_files_changed(self):
        """Verify error when both files were changed."""
        reference_data = [{"foo": "bar"}]
        with open(self.reference_file, 'w') as ref_file:
            json.dump(reference_data, ref_file)

        new_data = [{"1": "2"}]
        new_filepath = os.path.join(self.tempdir, 'new.json')
        with open(new_filepath, 'w') as new_file:
            json.dump(new_data, new_file)

        target_file = os.path.join(self.tempdir, 'target.json')

        with self.assertRaises(SystemExit):
            main([new_filepath, self.reference_file, target_file])


if __name__ == '__main__':
    main()
