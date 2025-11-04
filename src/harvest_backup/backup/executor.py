"""Backup executor that orchestrates backup for all accounts and endpoints."""

import hashlib
import json
import logging

import httpx

from harvest_backup.api.accounts import discover_accounts
from harvest_backup.api.client import HarvestAPIClient
from harvest_backup.api.endpoints import ENDPOINTS, Endpoint
from harvest_backup.api.exceptions import HarvestAuthenticationError
from harvest_backup.backup.writer import BackupWriter
from harvest_backup.models.account import Account

logger = logging.getLogger(__name__)

# Constants
HARVEST_DOMAIN_SUFFIX = ".harvestapp.com"
METADATA_FIELDS_TO_EXCLUDE = {"updated_at"}  # Exclude updated_at as it changes on every access
HTTP_STATUS_UNPROCESSABLE_ENTITY = 422


class BackupExecutor:
    """Executor for backing up all Harvest accounts."""

    def __init__(self, client: HarvestAPIClient, writer: BackupWriter) -> None:
        """Initialize backup executor.

        Args:
            client: Harvest API client
            writer: Backup file writer
        """
        self.client = client
        self.writer = writer

    async def backup_all(self) -> None:
        """Back up all Harvest accounts."""
        logger.info("Starting backup of all Harvest accounts...")

        try:
            accounts = await discover_accounts(self.client)
        except Exception as e:
            logger.error(f"Error discovering accounts: {e}", exc_info=True)
            raise

        if not accounts:
            raise ValueError("No Harvest accounts found")

        # Write accounts list
        accounts_data = [
            {"id": acc.id, "name": acc.name, "product": acc.product} for acc in accounts
        ]
        self.writer.write_accounts_list(accounts_data)

        # Backup each account
        for account in accounts:
            await self._backup_account(account)

        logger.info("Backup completed successfully")

    async def _backup_account(self, account: Account) -> None:
        """Back up a single account.

        Args:
            account: Account to back up (must have company_data populated)
        """
        logger.info(f"Backing up account {account.id} ({account.name})...")

        # Company data and subdomain should already be fetched and attached to account
        logger.debug(f"Using subdomain for account {account.id}: {account.subdomain}")

        # Backup each endpoint
        for endpoint in ENDPOINTS.values():
            try:
                await self._backup_endpoint(account, endpoint)
            except HarvestAuthenticationError:
                raise  # Propagate authentication errors immediately
            except Exception as e:
                logger.error(
                    f"Error backing up {endpoint.name} for account {account.id}: {e}", exc_info=True
                )
                continue

        logger.info(f"Completed backup for account {account.id}")

    async def _backup_single_resource_endpoint(self, account: Account, endpoint: Endpoint) -> None:
        """Back up a single-resource endpoint (like /v2/company).

        Args:
            account: Account object with company_data populated
            endpoint: Endpoint definition
        """
        try:
            # For company endpoint, use data already attached to account
            if endpoint.name == "company":
                data = account.company_data
            else:
                data = await self.client.get(endpoint.path, account.id)

            self.writer.write_json(account.id, endpoint.name, "data.json", data)
        except Exception as e:
            logger.error(f"Error backing up {endpoint.name}: {e}", exc_info=True)

    async def _collect_items_from_pagination(
        self, endpoint: Endpoint, account: Account
    ) -> tuple[list[dict], set[int]]:
        """Collect all items from paginated endpoint.

        Args:
            endpoint: Endpoint definition
            account: Account object

        Returns:
            Tuple of (all_items list, item_ids set)
        """
        all_items = []
        item_ids = set()

        async for item in self.client.get_paginated(endpoint.path, account.id):
            if isinstance(item, dict):
                item_id = item.get("id")
                if item_id:
                    item_ids.add(item_id)
                all_items.append(item)

        return all_items, item_ids

    async def _backup_individual_items(
        self, account: Account, endpoint: Endpoint, all_items: list[dict]
    ) -> None:
        """Back up individual item files from list data.

        Args:
            account: Account object
            endpoint: Endpoint definition
            all_items: List of all items
        """
        if not endpoint.has_detail:
            return

        for item in all_items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("id")
            if not item_id:
                continue

            try:
                self.writer.write_json(
                    account.id,
                    endpoint.name,
                    f"{item_id}.json",
                    item,
                )
            except Exception as e:
                logger.warning(f"Error writing {endpoint.name} item {item_id}: {e}")

    async def _backup_nested_resources(
        self, account: Account, endpoint: Endpoint, item_ids: set[int]
    ) -> None:
        """Back up nested resources for endpoint.

        Args:
            account: Account object
            endpoint: Endpoint definition
            item_ids: Set of item IDs to backup nested resources for
        """
        if not endpoint.has_nested or not endpoint.nested_paths or not item_ids:
            return

        for nested_path_template in endpoint.nested_paths:
            for item_id in item_ids:
                nested_path = nested_path_template.replace("{id}", str(item_id))
                try:
                    nested_items = []
                    async for item in self.client.get_paginated(nested_path, account.id):
                        nested_items.append(item)

                    if not nested_items:
                        continue

                    # Write nested resource with item_id prefix
                    nested_name = nested_path.split("/")[-1]  # e.g., "contacts"
                    self.writer.write_json(
                        account.id,
                        endpoint.name,
                        f"{item_id}_{nested_name}.json",
                        nested_items,
                    )
                except Exception as e:
                    if self._is_422_error(e):
                        logger.debug(
                            f"Skipping nested {nested_path} for {item_id}: "
                            "422 Unprocessable Entity (expected for non-managers)"
                        )
                    else:
                        logger.warning(f"Error backing up nested {nested_path} for {item_id}: {e}")

    async def _backup_endpoint(self, account: Account, endpoint: Endpoint) -> None:
        """Back up a single endpoint.

        Args:
            account: Account object with company_data and subdomain populated
            endpoint: Endpoint definition
        """
        logger.debug(f"Backing up {endpoint.name} for account {account.id}...")

        # Handle single-resource endpoints (like /v2/company)
        if not endpoint.has_list and not endpoint.has_detail:
            await self._backup_single_resource_endpoint(account, endpoint)
            return

        # Collect all items from paginated list
        all_items, item_ids = await self._collect_items_from_pagination(endpoint, account)

        # Write list (this contains all the data)
        if not all_items:
            return

        self.writer.write_json(account.id, endpoint.name, "list.json", all_items)

        # Create individual item files synthetically from list data
        await self._backup_individual_items(account, endpoint, all_items)

        # Backup nested resources
        await self._backup_nested_resources(account, endpoint, item_ids)

        # Download PDFs via client links (for invoices and estimates)
        if endpoint.name in ["invoices", "estimates"]:
            await self._backup_pdfs(account, endpoint.name, all_items)

    def _is_422_error(self, error: Exception) -> bool:
        """Check if exception is a 422 Unprocessable Entity error.

        422 errors are expected for some endpoints (e.g., teammates for non-managers).

        Args:
            error: Exception to check

        Returns:
            True if error is a 422 status code
        """
        return (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == HTTP_STATUS_UNPROCESSABLE_ENTITY
        )

    def _calculate_item_hash(self, item: dict) -> str:
        """Calculate hash for an item excluding updated_at field.

        Used for incremental PDF backup - hash is based on business data,
        not PDF binary, to avoid false positives from PDF metadata changes.
        Excludes updated_at as it changes on every access/update even when
        the actual invoice/estimate content hasn't changed.
        Includes created_at as a change in creation time indicates a significant
        change that requires re-downloading the PDF.

        Args:
            item: Item dictionary

        Returns:
            SHA-256 hash hex digest
        """
        item_for_hash = {k: v for k, v in item.items() if k not in METADATA_FIELDS_TO_EXCLUDE}
        item_json = json.dumps(item_for_hash, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(item_json.encode("utf-8")).hexdigest()

    def _build_client_link_url(self, subdomain: str, endpoint_name: str, client_key: str) -> str:
        """Build client link URL for PDF download.

        Args:
            subdomain: Account subdomain
            endpoint_name: Endpoint name ("invoices" or "estimates")
            client_key: Client key from item

        Returns:
            Full client link URL
        """
        return f"https://{subdomain}{HARVEST_DOMAIN_SUFFIX}/client/{endpoint_name}/{client_key}.pdf"

    async def _backup_pdfs(self, account: Account, endpoint_name: str, items: list[dict]) -> None:
        """Download PDFs for invoices or estimates using client links.

        Args:
            account: Account object with subdomain populated
            endpoint_name: Endpoint name ("invoices" or "estimates")
            items: List of invoice/estimate items
        """
        for item in items:
            if not isinstance(item, dict):
                continue

            item_id = item.get("id")
            client_key = item.get("client_key")

            if not item_id or not client_key:
                continue

            try:
                # Skip if subdomain is not available
                if not account.subdomain:
                    logger.debug(f"Skipped PDF (no subdomain): {endpoint_name} {item_id}")
                    continue

                json_hash = self._calculate_item_hash(item)

                # Check if PDF needs to be downloaded before making network request
                filename = f"{item_id}.pdf"
                if not self.writer.should_download_binary(
                    account.id, endpoint_name, str(item_id), filename, json_hash
                ):
                    logger.debug(f"Skipped PDF (unchanged): {endpoint_name} {item_id}")
                    continue

                # Download PDF
                client_url = self._build_client_link_url(
                    account.subdomain, endpoint_name, client_key
                )
                pdf_content = await self.client.download_client_link(client_url)

                # Write PDF file (write_binary will handle incremental backup logic)
                result = self.writer.write_binary(
                    account.id,
                    endpoint_name,
                    str(item_id),
                    filename,
                    pdf_content,
                    content_hash=json_hash,
                )

                if result is not None:
                    logger.verbose(
                        f"Downloaded PDF: {endpoint_name} {item_id} ({len(pdf_content)} bytes)"
                    )

            except Exception as e:
                logger.warning(f"Failed to download PDF for {endpoint_name} {item_id}: {e}")
                continue
