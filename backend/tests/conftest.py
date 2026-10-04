"""
Pytest fixtures for unit and integration testing.
Provides in-memory SQLite database sessions and sample test documents.
"""

import io
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import docx
from pypdf import PdfWriter

from backend.app.core.database import Base
from backend.app.models.complaint import Complaint
from backend.app.models.user import User


from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def test_db_engine():
    """In-memory SQLite database engine for testing with shared StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Provides a fresh database transaction per test function."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_txt_bytes():
    """Sample plain text complaint bytes."""
    text = (
        "Subject: Urgent Road Repair Needed\n\n"
        "There is a deep pothole on MG Road near building 4B.\n"
        "Vehicles are losing balance and two-wheelers have met with accidents.\n"
        "Please fix this road immediately."
    )
    return text.encode("utf-8")


@pytest.fixture
def sample_marathi_txt_bytes():
    """Sample Marathi text complaint bytes."""
    text = (
        "विषय: पाणी पुरवठा खंडित तक्रार\n\n"
        "आमच्या कॉलनीत गेल्या ४ दिवसांपासून पिण्याचे पाणी येत नाही.\n"
        "पाईपलाईन गळती झाली असून त्वरित दुरुस्ती करावी ही नम्र विनंती."
    )
    return text.encode("utf-8")


@pytest.fixture
def sample_docx_bytes():
    """Generate in-memory valid DOCX bytes."""
    doc = docx.Document()
    doc.add_heading("Grievance: Overflowing Garbage Dustbin", 0)
    doc.add_paragraph("The public waste bin in ward 12 has been overflowing for three days.")
    doc.add_paragraph("Foul smell is spreading and stray animals are scattering waste on the street.")
    
    # Add table
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Location"
    table.cell(0, 1).text = "Shivaji Nagar"
    table.cell(1, 0).text = "Urgency"
    table.cell(1, 1).text = "High"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def sample_pdf_bytes():
    """Generate in-memory valid PDF bytes using pypdf."""
    from pypdf import PageObject
    writer = PdfWriter()
    # Add a blank page with some text or create standard page
    # Since pypdf Writer can create a page, or we can use pdfplumber/reportlab or write minimal valid PDF stream
    # Let's create a minimal valid PDF with text stream
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"5 0 obj << /Length 73 >> stream\n"
        b"BT /F1 12 Tf 100 700 Td (Street lights on Main Street are not functioning at night.) Tj ET\n"
        b"endstream\nendobj\nxref\n0 6\n0000000000 65535 f \n"
        b"0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000244 00000 n \n0000000318 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n443\n%%EOF"
    )
    return pdf_content
