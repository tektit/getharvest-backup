"""File writer for backup data with incremental backup support."""

import hashlib
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

# Constants
HASH_DISPLAY_LENGTH = 16  # Number of hex characters to show in log messages


class BackupWriter:
    """Writer for backup files with incremental support."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize backup writer.

        Args:
            output_dir: Base output directory for backups
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track artifacts for incremental backup
        self.artifacts_manifest_file = self.output_dir / ".artifacts_manifest.json"
        self.artifacts_manifest: dict[str, dict[str, str]] = self._load_artifacts_manifest()

    def _load_artifacts_manifest(self) -> dict[str, dict[str, str]]:
        """Load artifacts manifest from disk.

        Returns:
            Dictionary mapping account_id -> artifact_path -> hash
        """
        if not self.artifacts_manifest_file.exists():
            return {}

        try:
            with self.artifacts_manifest_file.open() as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load artifacts manifest: {e}")
            return {}

    def _save_artifacts_manifest(self) -> None:
        """Save artifacts manifest to disk."""
        try:
            with NamedTemporaryFile(mode="w", dir=self.output_dir, delete=False, suffix=".json") as f:
                json.dump(self.artifacts_manifest, f, indent=2)
                temp_path = Path(f.name)

            # Atomic write
            temp_path.replace(self.artifacts_manifest_file)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save artifacts manifest: {e}")

    def _get_manifest_key(self, endpoint_name: str, artifact_id: str) -> str:
        """Get manifest key in new format.

        Args:
            endpoint_name: Endpoint name
            artifact_id: Artifact ID

        Returns:
            Manifest key string
        """
        return f"{endpoint_name}:{artifact_id}"

    def _get_manifest_hash(
        self, account_id: int, endpoint_name: str, artifact_id: str
    ) -> str | None:
        """Get hash from manifest for given artifact.

        Args:
            account_id: Harvest account ID
            endpoint_name: Endpoint name
            artifact_id: Artifact ID

        Returns:
            Hash string or None if not found
        """
        account_manifest = self.artifacts_manifest.get(str(account_id), {})
        manifest_key = self._get_manifest_key(endpoint_name, artifact_id)
        return account_manifest.get(manifest_key)


    def write_json(
        self,
        account_id: int,
        endpoint_name: str,
        filename: str,
        data: dict | list,
    ) -> Path:
        """Write JSON data to file.

        Args:
            account_id: Harvest account ID
            endpoint_name: Endpoint name (e.g., "clients")
            filename: Output filename (e.g., "list.json", "123.json")
            data: Data to write

        Returns:
            Path to written file
        """
        account_dir = self.output_dir / f"harvest_account_{account_id}" / endpoint_name
        account_dir.mkdir(parents=True, exist_ok=True)

        file_path = account_dir / filename

        # Write JSON with proper formatting
        try:
            with NamedTemporaryFile(mode="w", dir=account_dir, delete=False, suffix=".json") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                temp_path = Path(f.name)

            # Atomic write
            temp_path.replace(file_path)
            logger.debug(f"Wrote JSON: {file_path}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to write JSON {file_path}: {e}")
            raise

        return file_path

    def write_binary(
        self,
        account_id: int,
        endpoint_name: str,
        artifact_id: str,
        filename: str,
        content: bytes,
        content_hash: str | None = None,
    ) -> Path | None:
        """Write binary file (PDF, etc.) with incremental backup.

        Args:
            account_id: Harvest account ID
            endpoint_name: Endpoint name (e.g., "invoices")
            artifact_id: Artifact ID (e.g., invoice ID)
            filename: Output filename (e.g., "123.pdf")
            content: Binary content
            content_hash: Optional pre-calculated hash (e.g., from JSON data).
                         If None, hash is calculated from binary content.

        Returns:
            Path to written file, or None if skipped (already exists)
        """
        account_dir = self.output_dir / f"harvest_account_{account_id}" / endpoint_name
        artifacts_dir = account_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        file_path = artifacts_dir / filename

        # Calculate hash of content (use provided hash or calculate from binary)
        if content_hash is None:
            content_hash = hashlib.sha256(content).hexdigest()

        # Check if file already exists and matches
        if file_path.exists():
            existing_hash = self._get_manifest_hash(account_id, endpoint_name, artifact_id)

            if existing_hash == content_hash:
                logger.debug(
                    f"Skipping artifact (unchanged): {file_path} "
                    f"(JSON hash: {content_hash[:HASH_DISPLAY_LENGTH]}...)"
                )
                return None

            if existing_hash:
                logger.debug(
                    f"Invoice/estimate data changed: {file_path} "
                    f"(old JSON hash: {existing_hash[:HASH_DISPLAY_LENGTH]}..., "
                    f"new JSON hash: {content_hash[:HASH_DISPLAY_LENGTH]}...)"
                )
        else:
            logger.debug(f"PDF does not exist: {file_path} (will download)")

        # Write binary file
        try:
            with NamedTemporaryFile(mode="wb", dir=artifacts_dir, delete=False) as f:
                f.write(content)
                temp_path = Path(f.name)

            # Atomic write
            temp_path.replace(file_path)
            logger.debug(f"Saved PDF: {file_path} (JSON hash: {content_hash[:HASH_DISPLAY_LENGTH]}...)")

            # Update manifest
            if str(account_id) not in self.artifacts_manifest:
                self.artifacts_manifest[str(account_id)] = {}
            manifest_key = self._get_manifest_key(endpoint_name, artifact_id)
            self.artifacts_manifest[str(account_id)][manifest_key] = content_hash
            self._save_artifacts_manifest()
        except (IOError, OSError) as e:
            logger.error(f"Failed to write binary {file_path}: {e}")
            raise

        return file_path

    def should_download_binary(
        self,
        account_id: int,
        endpoint_name: str,
        artifact_id: str,
        filename: str,
        content_hash: str,
    ) -> bool:
        """Check if a binary file needs to be downloaded based on manifest and file existence.

        This allows checking before downloading to avoid unnecessary network requests.
        Downloads are needed if:
        - File doesn't exist on disk (missing PDF)
        - File exists but hash doesn't match manifest (changed content)
        - File exists but not in manifest (missing manifest entry)

        Args:
            account_id: Harvest account ID
            endpoint_name: Endpoint name (e.g., "invoices")
            artifact_id: Artifact ID (e.g., invoice ID)
            filename: Output filename (e.g., "123.pdf")
            content_hash: Hash of the content (e.g., JSON hash for invoices)

        Returns:
            True if file should be downloaded, False if it can be skipped
        """
        # Build file path to check existence
        account_dir = self.output_dir / f"harvest_account_{account_id}" / endpoint_name
        artifacts_dir = account_dir / "artifacts"
        file_path = artifacts_dir / filename
        
        # If file doesn't exist on disk, we definitely need to download it
        if not file_path.exists():
            return True

        # File exists - check manifest hash to see if content has changed
        existing_hash = self._get_manifest_hash(account_id, endpoint_name, artifact_id)

        # If hash matches, we can skip (file exists and content unchanged)
        if existing_hash == content_hash:
            return False

        # Hash doesn't match or manifest entry missing - need to download
        # (could be changed content, missing manifest entry, or corrupted file)
        return True

    def write_accounts_list(self, accounts: list[dict]) -> Path:
        """Write accounts list to root directory.

        Args:
            accounts: List of account dictionaries

        Returns:
            Path to written file
        """
        file_path = self.output_dir / "accounts.json"

        try:
            with NamedTemporaryFile(mode="w", dir=self.output_dir, delete=False, suffix=".json") as f:
                json.dump({"accounts": accounts}, f, indent=2, ensure_ascii=False)
                temp_path = Path(f.name)

            temp_path.replace(file_path)
            logger.debug(f"Wrote accounts list: {file_path}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to write accounts list {file_path}: {e}")
            raise

        return file_path

