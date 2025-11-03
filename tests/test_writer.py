"""Tests for backup writer."""

import json
from pathlib import Path

import pytest

from harvest_backup.backup.writer import BackupWriter, calculate_file_hash


def test_calculate_file_hash(tmp_path: Path) -> None:
    """Test file hash calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    hash1 = calculate_file_hash(test_file)
    hash2 = calculate_file_hash(test_file)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest length


def test_writer_init(tmp_path: Path) -> None:
    """Test backup writer initialization."""
    writer = BackupWriter(tmp_path)
    assert writer.output_dir == tmp_path
    assert tmp_path.exists()


def test_writer_write_json(tmp_path: Path) -> None:
    """Test writing JSON files."""
    writer = BackupWriter(tmp_path)

    data = {"key": "value", "number": 42}
    file_path = writer.write_json(12345, "clients", "test.json", data)

    assert file_path.exists()
    assert file_path == tmp_path / "harvest_account_12345" / "clients" / "test.json"

    with file_path.open() as f:
        loaded_data = json.load(f)

    assert loaded_data == data


def test_writer_write_json_dry_run(tmp_path: Path) -> None:
    """Test writing JSON in dry-run mode."""
    writer = BackupWriter(tmp_path)

    data = {"key": "value"}
    file_path = writer.write_json(12345, "clients", "test.json", data, dry_run=True)

    # In dry-run, file shouldn't exist
    assert not file_path.exists()


def test_writer_write_binary_incremental(tmp_path: Path) -> None:
    """Test incremental binary file writing."""
    writer = BackupWriter(tmp_path)

    content1 = b"PDF content 1"
    file_path1 = writer.write_binary(12345, "invoices", "100", "100.pdf", content1)

    assert file_path1 is not None
    assert file_path1.exists()

    # Write same content again - should be skipped
    file_path2 = writer.write_binary(12345, "invoices", "100", "100.pdf", content1)

    assert file_path2 is None  # Skipped because it already exists

    # Write different content - should overwrite
    content2 = b"PDF content 2 - updated"
    file_path3 = writer.write_binary(12345, "invoices", "100", "100.pdf", content2)

    assert file_path3 is not None
    assert file_path3.exists()

    # Verify content was updated
    assert file_path3.read_bytes() == content2


def test_writer_write_accounts_list(tmp_path: Path) -> None:
    """Test writing accounts list."""
    writer = BackupWriter(tmp_path)

    accounts = [{"id": 12345, "name": "Test Company", "product": "harvest"}]
    file_path = writer.write_accounts_list(accounts)

    assert file_path.exists()
    assert file_path == tmp_path / "accounts.json"

    with file_path.open() as f:
        data = json.load(f)

    assert data["accounts"] == accounts


def test_writer_directory_structure(tmp_path: Path) -> None:
    """Test that directory structure is created correctly."""
    writer = BackupWriter(tmp_path)

    writer.write_json(12345, "clients", "list.json", [])
    writer.write_json(67890, "projects", "list.json", [])

    assert (tmp_path / "harvest_account_12345" / "clients").exists()
    assert (tmp_path / "harvest_account_67890" / "projects").exists()

