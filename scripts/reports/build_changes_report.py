from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/pdf/ProfitLens_Project_Changes_and_Test_Evidence_2026-11-03.pdf"
NAVY = HexColor("#13283D")
TEAL = HexColor("#157B80")
MUTED = HexColor("#516477")
PALE = HexColor("#EDF5F5")
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TitlePL",
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=32,
        textColor=NAVY,
        spaceAfter=16,
    )
)
styles.add(
    ParagraphStyle(
        name="HeadPL",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=NAVY,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="SubPL",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=TEAL,
        spaceBefore=10,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyPL",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=NAVY,
        spaceAfter=9,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallPL",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=MUTED,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="CodePL",
        fontName="Courier",
        fontSize=8,
        leading=12,
        textColor=NAVY,
        backColor=PALE,
        borderPadding=9,
        spaceAfter=12,
    )
)
story = []


def p(s, style="BodyPL"):
    return Paragraph(s, styles[style])


def add(s, style="BodyPL"):
    story.append(p(s, style))


def heading(n, t):
    if story:
        story.append(PageBreak())
    add(f"{n:02d} / PROJECT UPDATE", "SmallPL")
    add(t, "TitlePL")


def sub(t, s):
    add(t, "SubPL")
    add(s)


def table(headers, rows, widths):
    data = [[p(x, "SmallPL") for x in headers]] + [
        [p(x, "SmallPL") for x in row] for row in rows
    ]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, HexColor("#DCE5E9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))


def flow(items):
    table(["WORKFLOW"], [["  >  ".join(items)]], [499])


def footer(c, d):
    c.setStrokeColor(TEAL)
    c.line(48, 46, 547, 46)
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    c.drawString(
        48, 32, "PROFITLENS  |  Evidence-based project briefing  |  3 November 2026"
    )
    c.drawRightString(547, 32, f"{d.page} / 6")


heading(1, "ProfitLens\nProject Changes &amp;\nTesting Evidence".replace("\n", "<br/>"))
add(
    "A simple guide to the upgraded product, its purpose and its verified limits.",
    "HeadPL",
)
sub(
    "The project in one sentence",
    "ProfitLens helps a small business review its financial records, understand changes and open the evidence behind a figure before making a decision.",
)
sub(
    "What changed in the direction",
    "The original project focused on customer invoices, attributed costs and PDF contracts. It now also accepts source data that does not contain all those entities, and adds a small set of reviewed billing and purchasing workflows. Missing records remain missing; they are not invented to fill a dashboard.",
)
table(
    ["Before", "Now in the release branch"],
    [
        (
            "Fixed customer/invoice/expense view",
            "A focused overview adapts to the available records and their financial meaning.",
        ),
        (
            "Profit investigation as the main journey",
            "Investigation plus reviewed recurring billing, purchase orders and tracked payments.",
        ),
        (
            "Disconnected or sparse demos",
            "A complete synthetic workflow fixture plus a separate licensed real-expenditure sample.",
        ),
        (
            "Temptation to treat every amount as income",
            "Sales, expenditure, commitments, payments and verified revenue stay distinct.",
        ),
    ],
    [165, 334],
)
sub(
    "Who it is for",
    "Small B2B service businesses and finance reviewers who work with exports and documents, need a monthly review, and want to check the source of an unusual amount. This is a college prototype, not a replacement for every accounting or tax workflow.",
)
add(
    "<b>Release boundary:</b> code commit 7402602 is pushed in PR #2. GitHub CI passed. The PR is still open; the new frontend preview failed and the new hosted demo publication is pending. Database migration alone does not prove the new application is live.",
    "SmallPL",
)

heading(2, "The new working workflows")
sub(
    "1. Recurring invoices",
    "Set a fixed customer charge on a monthly, quarterly or yearly schedule. Generate due drafts, inspect them and issue an invoice only after review. Issuing also creates a tracked unpaid receivable.",
)
flow(["Schedule", "Generate due drafts", "Review", "Issue invoice", "Track receivable"])
add(
    "Repeated generation or issue requests do not create the same occurrence twice. Short months preserve the original billing-day anchor. Pause schedules or skip drafts. Drafts do not count as revenue."
)
sub(
    "2. Purchase orders",
    "Create an order for a vendor, using catalogue items or custom lines. Approve it as a commitment. When the matching supplier invoice arrives, confirm a full match and record its bill.",
)
flow(
    [
        "Draft order",
        "Approve commitment",
        "Receive supplier invoice",
        "Confirm matching bill",
    ]
)
add(
    "A purchase order is not automatically an expense. A recorded bill becomes a payable; it does not automatically become a customer delivery cost. Partial payments can reduce its outstanding balance."
)
sub(
    "3. Money tracking and evidence",
    "Vendors, items and bills remain separate records. A payment can be allocated across compatible tracked documents for the same party. Mistaken payment entries can be voided with a reason; their history remains.",
)
table(
    ["Value", "Meaning"],
    [
        (
            "Outstanding balance",
            "Document total minus reviewed opening-paid amount minus active payment allocations.",
        ),
        (
            "Contribution",
            "Net billed customer revenue minus attributed costs, subject to cost completeness.",
        ),
        (
            "Contribution margin",
            "Contribution divided by net revenue; unavailable when the denominator or required evidence does not support it.",
        ),
    ],
    [150, 349],
)
add(
    "<b>Limits:</b> due drafts are generated by an explicit user action, not an unattended scheduler. No automatic emails or money collection. Purchase orders support full-order bill conversion, not partial delivery or partial billing.",
    "SmallPL",
)

heading(3, "How the upgraded system works")
flow(
    [
        "Next.js / React UI",
        "FastAPI validation and permissions",
        "PostgreSQL records",
        "Source-linked review",
    ]
)
sub(
    "Data first, calculations second",
    "Imports preserve source files and raw fields. Users review mappings and validation results before confirmation. Financial calculations use Decimal/NUMERIC. The AI explains available evidence; it does not calculate the official ledger or create missing relationships.",
)
table(
    ["Component", "Responsibility / current evidence"],
    [
        (
            "Web interface",
            "Grouped navigation, source explorer, financial overview, forms, review dialogs and in-popup assistant.",
        ),
        (
            "FastAPI backend",
            "Validate records, check workspace/role permissions, manage transactions and expose deterministic calculations.",
        ),
        (
            "PostgreSQL",
            "Separate business entities, organization-scoped foreign keys, audit events and four new planning tables.",
        ),
        (
            "Private source storage",
            "Authorized original-file access. Hosted storage is private; source links are not public document links.",
        ),
        (
            "AI and retrieval",
            "Existing evidence-based chat and source references. Operational payment/order balances are not yet part of chat scope.",
        ),
    ],
    [145, 354],
)
sub(
    "What the dashboard now emphasizes",
    "Financial activity over actual recorded months, evidence coverage, tracked balances and pending review tasks. It avoids repeating the full import explorer on the home page. Exact figures remain available; absent months are not silently filled with zero.",
)
sub(
    "Compatibility with clear boundaries",
    "Current import code supports CSV, TSV, XLSX, JSON and supported text-based PDFs. This release directly re-tested the new CSV datasets and synthetic contract PDFs. That does not establish compatibility with every export, scanned document, complex invoice PDF or accounting system.",
)
sub(
    "What makes ProfitLens useful",
    "Its defensible contribution is the connection between reviewed inputs, meaning-labelled financial figures and inspectable evidence. It is not a claim to have invented AI, to match every Zoho Books feature, or to be proven cheaper or more accurate than competitors.",
)
add(
    "Key code: planning.py, planning_schema.py, dashboard.py; web planning-panel.tsx and overview.tsx. Migration: 20261103_planning. Existing architecture is retained; no new microservices or paid infrastructure were added.",
    "SmallPL",
)

heading(4, "A clear demonstration story")
table(
    ["Dataset", "What it demonstrates", "What it cannot prove"],
    [
        (
            "ProfitLens Studio\nSynthetic fixture",
            "8 fictional customers; 37 invoices after recurring issue; 72 costs; 4 reviewed contracts; 2 schedules; 3 purchase orders; partial payments.",
            "Real customer adoption, actual savings or real-company profitability.",
        ),
        (
            "DWP spending 2026\nReal public data",
            "600 expenditure records across July-September. Real source references, preserved raw fields, monthly spending and exact totals.",
            "Sales, profit, linked contracts, customer costs or purchase-order history that the source does not provide.",
        ),
    ],
    [122, 215, 162],
)
sub(
    "A five-minute panel demonstration",
    "1. Open the synthetic workspace and explain the financial chart and evidence gaps.<br/>2. Generate/review a recurring draft; issue it and inspect the receivable.<br/>3. Approve a purchase order and record its matching bill; inspect the payable.<br/>4. Import the separate new-import CSV through preview and confirm.<br/>5. Switch to real data, inspect expenditure by month and open a supporting raw record/source.",
)
add(
    "<b>Important:</b> these refreshed fixtures are locally tested and prepared for publication. They have not yet been verified in the hosted dashboard. Earlier demo records will be preserved behind an archive toggle, not deleted.",
    "SmallPL",
)
sub(
    "What to say when asked about incomplete data",
    "“This source only supplies expenditure. ProfitLens can show and trace that spending, but it cannot claim profit without compatible revenue and cost evidence. The separate synthetic workspace demonstrates the complete linked workflow.”",
)
sub(
    "Next priorities",
    "Resolve the Vercel frontend preview failure, merge the verified release, publish the isolated demo workspaces and run hosted smoke tests. Then improve audited bill corrections and evaluate whether unattended recurring generation is useful within the project scope.",
)
add(
    "Still outside the delivered scope: general ledger, tax filing, bank feeds, stock management, quotes, payroll, automated payment collection and full Zoho Books parity. Pricing shown in the existing product represents proposed pilot plans, not active subscriptions.",
    "SmallPL",
)

heading(5, "Proof 1 / Executed software tests")
add("Evidence page 1 of 2. Actual results, not example numbers.", "HeadPL")
table(
    ["Executed check", "Observed result", "Evidence / boundary"],
    [
        (
            "Fresh focused rerun\n3 November 2026",
            "6 passed in 3.38 seconds",
            "planning, showcase and real_refresh tests; isolated local PostgreSQL test database.",
        ),
        (
            "GitHub CI\nrun 41646449021",
            "199 backend passed; 3 skipped\n27 browser passed",
            "Remote CI log retrieved again for this report. Private downloaded data is absent in CI.",
        ),
        (
            "Earlier full local run",
            "202 passed in 19.50 seconds",
            "Recorded release execution; not rerun in full for this PDF. Local datasets were present.",
        ),
        (
            "Hosted operations baseline",
            "47 checks recorded as passed",
            "Earlier operations-hosted-results.json; prior release only, not the new recurring/PO deployment.",
        ),
    ],
    [143, 146, 210],
)
sub(
    "Exact output from the fresh local test run",
    "The six tests cover the new workflows and actual DWP import. The result below was produced during preparation of this report:",
)
add("...... [100%]<br/>6 passed in 3.38s", "CodePL")
sub(
    "What those tests actually check",
    "<b>Recurring:</b> leap-year/month-end anchoring; three due drafts; repeat generation returns zero new drafts; repeat issuance returns the existing invoice; pause/resume and invalid-input rejection.<br/><b>Purchase orders:</b> exact rounded total 26.03; conversion blocked before approval; retry-safe conversion; partial payments; cancellation and required attestations.<br/><b>Permissions:</b> analyst requests return 403 and foreign-workspace requests return 404 in the tested routes.",
)
add(
    "<b>Reproduce:</b> configure an isolated test database, then run:<br/>python -m pytest tests/test_planning.py tests/test_showcase.py tests/test_real_refresh.py -q",
    "SmallPL",
)
add(
    '<link href="https://github.com/karankirtisharma/Profitlens/actions/runs/41646449021" color="#157B80">Open the actual GitHub CI run</link> | <link href="https://github.com/karankirtisharma/Profitlens/pull/2" color="#157B80">Inspect the release PR</link>',
    "SmallPL",
)
add(
    "These checks prove the covered behaviors under their test conditions. They are not a security certification, load benchmark, usability study or proof that every possible financial edge case is handled.",
    "SmallPL",
)

heading(6, "Proof 2 / Real data and release safety")
add(
    "Evidence page 2 of 2. Real records, independently checked amounts and honest deployment status.",
    "HeadPL",
)
sub(
    "Dataset identity and licence",
    "UK Department for Work and Pensions, spending over GBP 25,000, July-September 2026. Public releases dated 30 October 2026; downloaded 3 November. Open Government Licence v3.0. Original row counts: 11,947 / 8,501 / 9,750. The demonstration takes the first 200 rows per month in source order.",
)
table(
    ["Selected period", "Records", "Ground-truth expenditure (GBP)"],
    [
        ("July 2026", "200", "151,208,875.66"),
        ("August 2026", "200", "175,331,555.00"),
        ("September 2026", "200", "213,141,583.00"),
        ("Selected subset total", "600", "539,682,013.66"),
    ],
    [170, 70, 259],
)
add(
    "This is a selected subset total, not total departmental spending and not a representative estimate. Paid date remains paid date. Payment numbers are retained, but are not assumed unique invoices or contract links.",
    "SmallPL",
)
sub(
    "Executed real-data assertions",
    "Preview returned no issues. Confirmation repeated safely. Stored record count was 600; aggregate and monthly totals matched ground truth. Verified revenue remained unavailable. Original URL/row provenance was retained. Authorized file download matched uploaded bytes; a foreign-workspace download was rejected.",
)
sub(
    "Migration proof and remaining deployment gap",
    "Private backup manifest records 402,484 bytes and revision 20261103_planning. The migration check reports existing selected business values unchanged. This is a limited preservation check, not a restore rehearsal. Backup restoration has not been tested.<br/><br/>PR #2 remains open. API preview succeeded; frontend preview failed. The refreshed hosted workspaces have not been published or verified. No new hosted AI test is claimed in this report.",
)
add(
    "Evidence files: tests/test_real_refresh.py; tests/test_showcase.py; scripts/datasets/dwp_refresh.py; private ground-truth.json and planning-migration-check.json. Raw data and the private database backup are deliberately excluded from GitHub.",
    "SmallPL",
)
add(
    '<link href="https://www.gov.uk/government/publications/dwp-spending-over-25000-july-2026" color="#157B80">DWP July source</link> | <link href="https://www.gov.uk/government/publications/dwp-spending-over-25000-august-2026" color="#157B80">August source</link> | <link href="https://www.gov.uk/government/publications/dwp-spending-over-25000-september-2026" color="#157B80">September source</link><br/><link href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" color="#157B80">Open Government Licence v3.0</link>. Contains public sector information licensed under OGL v3.0.',
    "SmallPL",
)
OUT.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(
    str(OUT),
    pagesize=(595.28, 841.89),
    rightMargin=48,
    leftMargin=48,
    topMargin=49,
    bottomMargin=62,
    title="ProfitLens: Project Changes & Testing Evidence",
    author="ProfitLens Project Team",
).build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
