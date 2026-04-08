"""PostgreSQL mock data loader for local development.

Usage: uv run python scripts/seed_database.py
"""

import asyncio

from sqlalchemy import text

from app.infrastructure.database import async_session_factory
from app.infrastructure.mapping import start_mappers


COSTUMERS = [
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "costumer_code": "CST-2001",
        "company_name": "Northwind Retail GmbH",
        "contact_name": "Emma Clark",
        "email": "emma.clark@northstar-industries.com",
        "segment": "enterprise",
        "annual_contract_value_eur": 420000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "costumer_code": "CST-2002",
        "company_name": "Alpine Components AG",
        "contact_name": "Liam Nguyen",
        "email": "liam.nguyen@northstar-industries.com",
        "segment": "mid-market",
        "annual_contract_value_eur": 185000,
        "is_active": True,
    },
    {
        "id": "00000000-0000-4000-8000-000000000003",
        "costumer_code": "CST-2003",
        "company_name": "Helios Medical Supplies",
        "contact_name": "Sofia Rossi",
        "email": "sofia.rossi@northstar-industries.com",
        "segment": "enterprise",
        "annual_contract_value_eur": 610000,
        "is_active": True,
    },
]

DOCUMENTS = [
    {
        "id": "00000000-0000-4000-8000-000000000201",
        "title": "Q1 2026 Financial Summary",
        "source": "ERP Finance DB",
        "source_type": "postgres",
        "content_preview": "Revenue: EUR 12.4M, COGS: EUR 7.1M, Gross Margin: 42.7%, EBITDA: EUR 2.3M.",
        "metadata_json": '{"department":"Finance","classification":"internal-confidential","fiscal_quarter":"2026-Q1","currency":"EUR"}',
    },
    {
        "id": "00000000-0000-4000-8000-000000000202",
        "title": "Payroll March 2026",
        "source": "Payroll SFTP Drop",
        "source_type": "sftp",
        "content_preview": "Total gross payroll: EUR 1.18M across 342 employees. Overtime cost: EUR 94K.",
        "metadata_json": '{"department":"HR","classification":"restricted","period":"2026-03","currency":"EUR"}',
    },
    {
        "id": "00000000-0000-4000-8000-000000000203",
        "title": "2026 CAPEX Plan",
        "source": "Executive KPI Sheets",
        "source_type": "google_sheets",
        "content_preview": "Planned CAPEX: EUR 3.8M. Factory automation line: EUR 1.6M; IT modernization: EUR 920K.",
        "metadata_json": '{"department":"Operations","classification":"internal-confidential","fiscal_year":2026,"currency":"EUR"}',
    },
]

EMPLOYEES = [
    {
        "id": "00000000-0000-4000-8000-000000000301",
        "employee_number": "EMP-1001",
        "full_name": "Olivia Becker",
        "department": "Finance",
        "job_title": "Senior Financial Analyst",
        "base_salary_eur": 78000,
        "bonus_target_pct": 12.5,
        "manager_name": "Emma Clark",
        "is_active": True,
        "hired_at": "2022-03-01T00:00:00Z",
    },
    {
        "id": "00000000-0000-4000-8000-000000000302",
        "employee_number": "EMP-1002",
        "full_name": "Jakob Meier",
        "department": "Operations",
        "job_title": "Plant Operations Lead",
        "base_salary_eur": 86500,
        "bonus_target_pct": 10.0,
        "manager_name": "Noah Bauer",
        "is_active": True,
        "hired_at": "2021-11-15T00:00:00Z",
    },
    {
        "id": "00000000-0000-4000-8000-000000000303",
        "employee_number": "EMP-1003",
        "full_name": "Mila Vogt",
        "department": "HR",
        "job_title": "HR Business Partner",
        "base_salary_eur": 69500,
        "bonus_target_pct": 8.0,
        "manager_name": "Sofia Rossi",
        "is_active": True,
        "hired_at": "2023-01-09T00:00:00Z",
    },
]


async def seed() -> None:
    """Load deterministic mock records into PostgreSQL."""
    start_mappers()

    create_costumers_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS costumers (
            id UUID PRIMARY KEY,
            costumer_code VARCHAR(30) UNIQUE NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            contact_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            segment VARCHAR(50) NOT NULL,
            annual_contract_value_eur NUMERIC(12, 2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    create_employees_table_sql = text(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id UUID PRIMARY KEY,
            employee_number VARCHAR(30) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            department VARCHAR(100) NOT NULL,
            job_title VARCHAR(120) NOT NULL,
            base_salary_eur NUMERIC(12, 2) NOT NULL,
            bonus_target_pct NUMERIC(5, 2) NOT NULL,
            manager_name VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            hired_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    costumer_sql = text(
        """
        INSERT INTO costumers (
            id,
            costumer_code,
            company_name,
            contact_name,
            email,
            segment,
            annual_contract_value_eur,
            is_active,
            created_at,
            updated_at
        )
        VALUES (
            CAST(:id AS uuid),
            :costumer_code,
            :company_name,
            :contact_name,
            :email,
            :segment,
            :annual_contract_value_eur,
            :is_active,
            NOW(),
            NOW()
        )
        ON CONFLICT (costumer_code)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            contact_name = EXCLUDED.contact_name,
            email = EXCLUDED.email,
            segment = EXCLUDED.segment,
            annual_contract_value_eur = EXCLUDED.annual_contract_value_eur,
            is_active = EXCLUDED.is_active,
            updated_at = NOW()
        """
    )

    document_sql = text(
        """
        INSERT INTO documents (id, title, source, source_type, content_preview, metadata_json, created_at, updated_at)
        VALUES (CAST(:id AS uuid), :title, :source, :source_type, :content_preview, :metadata_json, NOW(), NOW())
        ON CONFLICT (id)
        DO UPDATE SET
            title = EXCLUDED.title,
            source = EXCLUDED.source,
            source_type = EXCLUDED.source_type,
            content_preview = EXCLUDED.content_preview,
            metadata_json = EXCLUDED.metadata_json,
            updated_at = NOW()
        """
    )

    employee_sql = text(
        """
        INSERT INTO employees (
            id,
            employee_number,
            full_name,
            department,
            job_title,
            base_salary_eur,
            bonus_target_pct,
            manager_name,
            is_active,
            hired_at,
            created_at,
            updated_at
        )
        VALUES (
            CAST(:id AS uuid),
            :employee_number,
            :full_name,
            :department,
            :job_title,
            :base_salary_eur,
            :bonus_target_pct,
            :manager_name,
            :is_active,
            CAST(:hired_at AS timestamptz),
            NOW(),
            NOW()
        )
        ON CONFLICT (employee_number)
        DO UPDATE SET
            full_name = EXCLUDED.full_name,
            department = EXCLUDED.department,
            job_title = EXCLUDED.job_title,
            base_salary_eur = EXCLUDED.base_salary_eur,
            bonus_target_pct = EXCLUDED.bonus_target_pct,
            manager_name = EXCLUDED.manager_name,
            is_active = EXCLUDED.is_active,
            hired_at = EXCLUDED.hired_at,
            updated_at = NOW()
        """
    )

    async with async_session_factory() as session:
        async with session.begin():
            await session.execute(create_costumers_table_sql)
            await session.execute(create_employees_table_sql)

            for costumer in COSTUMERS:
                await session.execute(costumer_sql, costumer)

            for employee in EMPLOYEES:
                await session.execute(employee_sql, employee)

            for doc in DOCUMENTS:
                await session.execute(document_sql, doc)

    print(
        "Seeded/updated "
        f"{len(COSTUMERS)} costumers, "
        f"{len(EMPLOYEES)} employees, "
        f"and {len(DOCUMENTS)} documents."
    )


if __name__ == "__main__":
    asyncio.run(seed())
