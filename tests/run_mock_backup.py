#!/usr/bin/env python3
"""Run backup tool with mocked API data.

This script sets up mocking for the Harvest API client and then runs
the actual backup tool CLI, allowing you to test all features with
mock/test data without needing a real Harvest API token.

Usage:
    python tests/run_mock_backup.py [all CLI options]

Example:
    python tests/run_mock_backup.py --output ./test_backup
    python tests/run_mock_backup.py --output ./test_backup --verbose
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import both harvest_backup and tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# Import the mock client - we need to patch before importing modules that use HarvestAPIClient
from tests.fixtures.mock_client import MockHarvestAPIClient

# Set fake PAT in environment (required by CLI)
os.environ["HARVEST_PAT"] = "test_token_fake_pat_for_local_testing"

# Import modules so we can patch them (dependencies must be installed)
import harvest_backup.api.client as client_module
import harvest_backup.api.accounts as accounts_module
import harvest_backup.backup.executor as executor_module

# Monkey patch the class in the modules - replace before CLI imports it
client_module.HarvestAPIClient = MockHarvestAPIClient
accounts_module.HarvestAPIClient = MockHarvestAPIClient
executor_module.HarvestAPIClient = MockHarvestAPIClient

# Now import and run the CLI - it will use MockHarvestAPIClient instead of the real one
# The CLI will handle all argument parsing
from harvest_backup.cli import main as cli_main

# Call the actual CLI main function - it will use MockHarvestAPIClient
# because we patched it before the CLI module imported it
cli_main()
