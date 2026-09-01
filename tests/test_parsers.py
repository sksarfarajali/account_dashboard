from app.parsers.axis import AxisParser
from app.parsers.hdfc import HdfcParser
from app.parsers.icici import IciciParser
from app.parsers.registry import parse_email


def test_hdfc_debit_parses():
    body = (
        "Update! INR 1,250.00 debited from HDFC Bank XX1234 on 25-AUG-25. "
        "Info: UPI-SWIGGY-swiggy@ybl. Avl bal INR 45,000.00"
    )
    result = HdfcParser().parse("Update on your account", body)

    assert result is not None
    assert result.amount == 1250.00
    assert result.type == "debit"
    assert result.account_ref == "1234"
    assert result.date.year == 2025 and result.date.month == 8 and result.date.day == 25
    assert "SWIGGY" in result.merchant


def test_icici_credit_parses():
    body = (
        "Dear Customer, Rs 850.00 has been credited to your ICICI Bank Account "
        "XX5678 on 20-Aug-2025 through NEFT from ACME CORP. Avl Bal: Rs 1,20,000.00"
    )
    result = IciciParser().parse("Credit Alert", body)

    assert result is not None
    assert result.amount == 850.00
    assert result.type == "credit"
    assert result.account_ref == "5678"
    assert result.merchant == "ACME CORP"


def test_axis_card_spend_parses():
    body = "Axis Bank Alert: INR 320.50 spent on your Credit Card XX9012 at AMAZON on 18-08-2025 12:30:45"
    result = AxisParser().parse("Card Alert", body)

    assert result is not None
    assert result.amount == 320.50
    assert result.type == "debit"
    assert result.merchant == "AMAZON"
    assert result.account_ref == "9012"


def test_registry_routes_by_sender():
    body = (
        "Update! INR 500.00 debited from HDFC Bank XX0001 on 01-JAN-25. "
        "Info: UPI-TEST-test@ybl. Avl bal INR 1,000.00"
    )
    result = parse_email("alerts@hdfcbank.net", "Update", body)

    assert result is not None
    assert result.amount == 500.00


def test_registry_falls_back_to_generic_for_unknown_bank():
    body = "Rs 99.00 was debited from your account for a purchase."
    result = parse_email("noreply@somebank.example.com", "Alert", body)

    assert result is not None
    assert result.amount == 99.00
    assert result.type == "debit"


def test_non_transaction_email_returns_none():
    body = "Thanks for banking with us. No transactions this week."
    result = HdfcParser().parse("Newsletter", body)

    assert result is None
