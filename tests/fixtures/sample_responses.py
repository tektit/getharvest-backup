"""Sample API responses for testing."""

SAMPLE_ACCOUNTS_RESPONSE = {
    "user": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "[email protected]",
    },
    "accounts": [
        {"id": 12345, "name": "Test Company", "product": "harvest"},
        {"id": 67890, "name": "Another Company", "product": "harvest"},
        {"id": 99999, "name": "Forecast Account", "product": "forecast"},
    ],
}

SAMPLE_CLIENTS_RESPONSE = {
    "clients": [
        {"id": 1, "name": "Client 1", "is_active": True},
        {"id": 2, "name": "Client 2", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_CLIENT_DETAIL_RESPONSE = {
    "id": 1,
    "name": "Client 1",
    "is_active": True,
    "address": "123 Main St",
}

SAMPLE_CLIENT_CONTACTS_RESPONSE = {
    "contacts": [
        {"id": 1, "client_id": 1, "first_name": "Jane", "last_name": "Smith"},
        {"id": 2, "client_id": 1, "first_name": "Bob", "last_name": "Jones"},
    ],
}

SAMPLE_COMPANY_RESPONSE = {
    "id": 12345,
    "name": "Test Company",
    "week_start_day": "Monday",
}

SAMPLE_TIME_ENTRIES_RESPONSE = {
    "time_entries": [
        {"id": 100, "project_id": 1, "task_id": 1, "hours": 2.5},
        {"id": 101, "project_id": 1, "task_id": 1, "hours": 3.0},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

