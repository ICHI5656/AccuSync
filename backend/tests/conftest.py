"""
Pytest configuration and fixtures for AccuSync tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from decimal import Decimal

from app.db.base import Base
from app.models.customer_company import CustomerCompany
from app.models.product import Product
from app.models.issuer_company import IssuerCompany


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    # Use in-memory SQLite for fast tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # Clean up
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    # Rollback any changes made during the test
    session.rollback()
    session.close()


@pytest.fixture
def test_issuer(db_session: Session):
    """Create a test issuer company."""
    issuer = IssuerCompany(
        name="テスト請求者株式会社",
        brand_name="テストブランド",
        tax_id="T1234567890123",
        address="東京都千代田区",
        postal_code="100-0001",
        tel="03-1111-2222",
        email="issuer@test.com"
    )
    db_session.add(issuer)
    db_session.commit()
    db_session.refresh(issuer)
    return issuer


@pytest.fixture
def test_customer(db_session: Session):
    """Create a test customer company."""
    customer = CustomerCompany(
        code="TEST001",
        name="テスト株式会社",
        is_individual=False,
        address="東京都渋谷区",
        postal_code="150-0001",
        phone="03-1234-5678",
        email="customer@test.com"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_individual_customer(db_session: Session):
    """Create a test individual customer."""
    customer = CustomerCompany(
        code="IND001",
        name="田中太郎",
        is_individual=True,
        address="東京都新宿区",
        postal_code="160-0001",
        phone="090-1234-5678"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_product_hard_case(db_session: Session):
    """Create a test product (hard case)."""
    product = Product(
        sku="HC001",
        name="ハードケース(テストデザイン)",
        default_price=Decimal("1000"),
        tax_rate=0.10,
        tax_category="taxable",
        unit="個"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def test_product_flip_case(db_session: Session):
    """Create a test product (flip case with mirror)."""
    product = Product(
        sku="FC001",
        name="手帳型カバーmirror(花柄)",
        default_price=Decimal("1500"),
        tax_rate=0.10,
        tax_category="taxable",
        unit="個"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return [
        {
            'customer_name': 'テスト株式会社',
            'address': '東京都渋谷区',
            'phone': '03-1234-5678',
            'product_name': 'ハードケース(テストデザイン)',
            'extracted_memo': 'ハードケース',
            'quantity': '10',
            'unit_price': '800'
        },
        {
            'customer_name': 'テスト株式会社',
            'address': '東京都渋谷区',
            'phone': '03-1234-5678',
            'product_name': '手帳型カバーmirror(花柄)',
            'extracted_memo': '手帳型カバー / mirror',
            'quantity': '5',
            'unit_price': '1200'
        }
    ]
