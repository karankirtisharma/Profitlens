"""Generate small synthetic contract/evaluation inputs; never uses customer data."""

from pathlib import Path

from reportlab.pdfgen import canvas

folder = Path("data/demo")
for customer, name, rate in [
    ("C001", "Northstar Studio", 10000),
    ("C002", "Harbor Retail", 20000),
]:
    pdf = canvas.Canvas(str(folder / f"contract_{customer}.pdf"))
    pdf.setTitle(f"Synthetic contract - {customer}")
    lines = [
        "PROFITLENS - SYNTHETIC SERVICE AGREEMENT",
        f"Customer: {name} ({customer})",
        "For development and evaluation only. No real agreement.",
        "Effective period: 01 September 2026 to 28 February 2027.",
        f"Fixed monthly service rate: INR {rate}.00 before tax.",
        "Fixed monthly discount: INR 0.00. Billing frequency: monthly.",
        "Rates must be manually reviewed before use in pricing checks.",
    ]
    for i, line in enumerate(lines):
        pdf.drawString(55, 780 - i * 28, line)
    pdf.save()
(folder / "invalid_invoices.csv").write_text(
    "invoice_id,customer_id,billing_period,currency,subtotal,discount,tax,refund,total\nBAD-1,C001,2026-09,INR,100,0,0,0,99\nBAD-2,MISSING,2026-09,INR,100,0,0,0,100\n",
    encoding="utf-8",
)
print("Generated two synthetic PDFs and a rejected-import fixture.")
