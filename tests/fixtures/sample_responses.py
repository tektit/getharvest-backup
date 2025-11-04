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

SAMPLE_COMPANY_RESPONSE = {
    "id": 12345,
    "name": "Test Company",
    "week_start_day": "Monday",
    "full_domain": "testcompany.harvestapp.com",
    "base_uri": "https://testcompany.harvestapp.com",
}

SAMPLE_COMPANY_RESPONSE_2 = {
    "id": 67890,
    "name": "Another Company",
    "week_start_day": "Tuesday",
    "full_domain": "anothercompany.harvestapp.com",
    "base_uri": "https://anothercompany.harvestapp.com",
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

SAMPLE_CONTACTS_RESPONSE = {
    "contacts": [
        {"id": 1, "client_id": 1, "first_name": "Jane", "last_name": "Smith"},
        {"id": 2, "client_id": 1, "first_name": "Bob", "last_name": "Jones"},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_PROJECTS_RESPONSE = {
    "projects": [
        {"id": 100, "name": "Project 1", "client_id": 1, "is_active": True},
        {"id": 101, "name": "Project 2", "client_id": 2, "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_PROJECT_USER_ASSIGNMENTS_RESPONSE = {
    "user_assignments": [
        {"id": 1, "project_id": 100, "user_id": 1},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_PROJECT_TASK_ASSIGNMENTS_RESPONSE = {
    "task_assignments": [
        {"id": 1, "project_id": 100, "task_id": 1},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_TASKS_RESPONSE = {
    "tasks": [
        {"id": 1, "name": "Task 1", "is_active": True},
        {"id": 2, "name": "Task 2", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_TIME_ENTRIES_RESPONSE = {
    "time_entries": [
        {"id": 100, "project_id": 100, "task_id": 1, "hours": 2.5},
        {"id": 101, "project_id": 100, "task_id": 1, "hours": 3.0},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_USERS_RESPONSE = {
    "users": [
        {"id": 1, "first_name": "Alice", "last_name": "Smith", "email": "[email protected]"},
        {"id": 2, "first_name": "Bob", "last_name": "Jones", "email": "[email protected]"},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 2,
    "page": 1,
    "links": {},
}

SAMPLE_USER_BILLABLE_RATES_RESPONSE = {
    "billable_rates": [
        {"id": 1, "user_id": 1, "amount": 100.0},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_USER_COST_RATES_RESPONSE = {
    "cost_rates": [
        {"id": 1, "user_id": 1, "amount": 50.0},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_USER_PROJECT_ASSIGNMENTS_RESPONSE = {
    "project_assignments": [
        {"id": 1, "user_id": 1, "project_id": 100},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_USER_TEAMMATES_RESPONSE = {
    "teammates": [
        {"id": 2, "user_id": 1},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_USERS_ME_RESPONSE = {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "[email protected]",
}

SAMPLE_USERS_ME_PROJECT_ASSIGNMENTS_RESPONSE = {
    "project_assignments": [
        {"id": 1, "user_id": 1, "project_id": 100},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_EXPENSES_RESPONSE = {
    "expenses": [
        {"id": 200, "project_id": 100, "amount": 50.0, "notes": "Lunch"},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_EXPENSE_CATEGORIES_RESPONSE = {
    "expense_categories": [
        {"id": 300, "name": "Meals", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_INVOICES_RESPONSE = {
    "invoices": [
        {
            "id": 400,
            "client_id": 1,
            "client_key": "abc123def456",
            "subject": "Invoice 1",
            "amount": 1000.0,
        },
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_INVOICE_ITEM_CATEGORIES_RESPONSE = {
    "invoice_item_categories": [
        {"id": 500, "name": "Development", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_ESTIMATES_RESPONSE = {
    "estimates": [
        {
            "id": 600,
            "client_id": 1,
            "client_key": "xyz789ghi012",
            "subject": "Estimate 1",
            "amount": 5000.0,
        },
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_ESTIMATE_ITEM_CATEGORIES_RESPONSE = {
    "estimate_item_categories": [
        {"id": 700, "name": "Consulting", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

SAMPLE_ROLES_RESPONSE = {
    "roles": [
        {"id": 800, "name": "Developer", "is_active": True},
    ],
    "per_page": 100,
    "total_pages": 1,
    "total_entries": 1,
    "page": 1,
    "links": {},
}

# PDF Test Data
# Sample PDF content for invoices (minimal valid PDF structure)
SAMPLE_INVOICE_PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"1 0 obj\n"
    b"<<\n"
    b"/Type /Catalog\n"
    b"/Pages 2 0 R\n"
    b">>\n"
    b"endobj\n"
    b"2 0 obj\n"
    b"<<\n"
    b"/Type /Pages\n"
    b"/Kids [3 0 R]\n"
    b"/Count 1\n"
    b">>\n"
    b"endobj\n"
    b"3 0 obj\n"
    b"<<\n"
    b"/Type /Page\n"
    b"/Parent 2 0 R\n"
    b"/MediaBox [0 0 612 792]\n"
    b"/Contents 4 0 R\n"
    b"/Resources <<\n"
    b"/Font <<\n"
    b"/F1 <<\n"
    b"/Type /Font\n"
    b"/Subtype /Type1\n"
    b"/BaseFont /Helvetica\n"
    b">>\n"
    b">>\n"
    b">>\n"
    b">>\n"
    b"endobj\n"
    b"4 0 obj\n"
    b"<<\n"
    b"/Length 44\n"
    b">>\n"
    b"stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"100 700 Td\n"
    b"(Invoice 1 - Test Company) Tj\n"
    b"ET\n"
    b"endstream\n"
    b"endobj\n"
    b"xref\n"
    b"0 5\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000317 00000 n \n"
    b"trailer\n"
    b"<<\n"
    b"/Size 5\n"
    b"/Root 1 0 R\n"
    b">>\n"
    b"startxref\n"
    b"410\n"
    b"%%EOF"
)

# Sample PDF content for estimates
SAMPLE_ESTIMATE_PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"1 0 obj\n"
    b"<<\n"
    b"/Type /Catalog\n"
    b"/Pages 2 0 R\n"
    b">>\n"
    b"endobj\n"
    b"2 0 obj\n"
    b"<<\n"
    b"/Type /Pages\n"
    b"/Kids [3 0 R]\n"
    b"/Count 1\n"
    b">>\n"
    b"endobj\n"
    b"3 0 obj\n"
    b"<<\n"
    b"/Type /Page\n"
    b"/Parent 2 0 R\n"
    b"/MediaBox [0 0 612 792]\n"
    b"/Contents 4 0 R\n"
    b"/Resources <<\n"
    b"/Font <<\n"
    b"/F1 <<\n"
    b"/Type /Font\n"
    b"/Subtype /Type1\n"
    b"/BaseFont /Helvetica\n"
    b">>\n"
    b">>\n"
    b">>\n"
    b">>\n"
    b"endobj\n"
    b"4 0 obj\n"
    b"<<\n"
    b"/Length 45\n"
    b">>\n"
    b"stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"100 700 Td\n"
    b"(Estimate 1 - Test Company) Tj\n"
    b"ET\n"
    b"endstream\n"
    b"endobj\n"
    b"xref\n"
    b"0 5\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000317 00000 n \n"
    b"trailer\n"
    b"<<\n"
    b"/Size 5\n"
    b"/Root 1 0 R\n"
    b">>\n"
    b"startxref\n"
    b"411\n"
    b"%%EOF"
)
