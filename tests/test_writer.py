"""Tests for backup writer."""

import json
from pathlib import Path

import pytest

from harvest_backup.backup.writer import BackupWriter


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


def test_should_download_binary_missing_file(tmp_path: Path) -> None:
    """Test that should_download_binary returns True for missing files."""
    writer = BackupWriter(tmp_path)
    
    # File doesn't exist - should download
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", "abc123hash"
    )
    
    assert should_download is True


def test_should_download_binary_hash_matches(tmp_path: Path) -> None:
    """Test that should_download_binary returns False when hash matches."""
    import hashlib
    
    writer = BackupWriter(tmp_path)
    
    # Write a PDF file first
    content = b"%PDF-1.4\nfake pdf content"
    content_hash = hashlib.sha256(content).hexdigest()
    
    writer.write_binary(
        12345, "invoices", "100", "100.pdf", content, content_hash=content_hash
    )
    
    # Check with matching hash - should skip
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", content_hash
    )
    
    assert should_download is False


def test_should_download_binary_hash_mismatch(tmp_path: Path) -> None:
    """Test that should_download_binary returns True when hash doesn't match."""
    import hashlib
    
    writer = BackupWriter(tmp_path)
    
    # Write a PDF file first
    content = b"%PDF-1.4\nfake pdf content"
    content_hash = hashlib.sha256(content).hexdigest()
    
    writer.write_binary(
        12345, "invoices", "100", "100.pdf", content, content_hash=content_hash
    )
    
    # Check with different hash - should download
    different_hash = "different_hash_value_12345"
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", different_hash
    )
    
    assert should_download is True


def test_should_download_binary_file_exists_no_manifest(tmp_path: Path) -> None:
    """Test that should_download_binary returns True when file exists but not in manifest."""
    writer = BackupWriter(tmp_path)
    
    # Create the file manually (not through write_binary, so no manifest entry)
    artifacts_dir = tmp_path / "harvest_account_12345" / "invoices" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    pdf_file = artifacts_dir / "100.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\nfake pdf")
    
    # Check - file exists but not in manifest, should download
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", "some_hash"
    )
    
    assert should_download is True


def test_should_download_binary_with_hash(tmp_path: Path) -> None:
    """Test that should_download_binary works with hash matching."""
    import hashlib
    
    writer = BackupWriter(tmp_path)
    
    # Write a PDF file first
    content = b"%PDF-1.4\nfake pdf content"
    content_hash = hashlib.sha256(content).hexdigest()
    
    writer.write_binary(
        12345, "invoices", "100", "100.pdf", content, content_hash=content_hash
    )
    
    # Check with matching hash - should skip
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", content_hash
    )
    
    assert should_download is False
    
    # Check with different hash - should download
    different_hash = "different_hash_value"
    should_download = writer.should_download_binary(
        12345, "invoices", "100", "100.pdf", different_hash
    )
    
    assert should_download is True

