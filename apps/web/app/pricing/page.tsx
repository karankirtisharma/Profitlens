import Link from "next/link";

const plans = [
  {
    name: "Explore",
    price: "₹0",
    audience: "Understand a small export",
    features: [
      "1 workspace · 1 user",
      "500 source records per month",
      "Reviewed imports and source evidence",
      "Sales, spending and cash-flow views",
      "No included hosted AI credits",
    ],
  },
  {
    name: "Review",
    price: "₹299",
    audience: "A monthly review for a small business",
    features: [
      "1 workspace · 3 users",
      "2,000 source records per month",
      "Reusable mappings and private documents",
      "100 bounded AI questions per month",
      "Financial investigations with evidence",
    ],
  },
  {
    name: "Collaborate",
    price: "₹699",
    audience: "Review records with your finance team",
    features: [
      "1 workspace · 5 users",
      "5,000 source records per month",
      "300 bounded AI questions per month",
      "Customer-scoped analyst access",
      "Shared review of sources and findings",
    ],
  },
];

export default function Pricing() {
  return (
    <main className="pricing-page">
      <nav className="button-row" aria-label="Pricing navigation">
        <Link href="/">← ProfitLens workspace</Link>
        <a href="#plan-details">Compare plans</a>
      </nav>
      <header className="pricing-heading">
        <span className="tag">Proposed pilot pricing · INR</span>
        <h1>
          Understand your numbers.
          <br />
          See the proof.
        </h1>
        <p>
          Review business exports, inspect their evidence and understand what is
          still missing. Start with the data you have; contracts are optional.
        </p>
      </header>
      <p className="alert" role="note">
        Pricing preview only. Subscriptions, payment collection and plan quotas
        are not active. Your existing demo access is unchanged. These proposed
        prices and allowances need operating-cost and user validation before
        launch.
      </p>
      <section
        id="plan-details"
        className="pricing-grid"
        aria-label="Three proposed plans"
      >
        {plans.map((plan) => (
          <article key={plan.name} className="panel glass pricing-card">
            <h2>{plan.name}</h2>
            <p>{plan.audience}</p>
            <p className="plan-price">
              {plan.price}
              <small> / workspace / month</small>
            </p>
            <ul>
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <Link className="secondary" href="/">
              Open existing demo
            </Link>
          </article>
        ))}
      </section>
      <section className="panel glass">
        <h2>One clear review workflow</h2>
        <ol>
          <li>Upload CSV, TSV, XLSX, JSON or a supported text PDF.</li>
          <li>
            Review the field mapping and financial meaning before importing.
          </li>
          <li>
            Explore recorded amounts and open the source behind an answer.
          </li>
        </ol>
        <p>
          Bank money-in/out observations are not automatically revenue or
          expenses. Profit requires a verified revenue-and-cost basis. Missing
          costs never become zero.
        </p>
        <details>
          <summary>What is available today, and what is still limited?</summary>
          <p>
            The prototype supports source imports, reviewed mappings, private
            documents, scoped access and configured AI explanations. AI credits,
            monthly billing, subscription management and tier enforcement are
            not implemented. No accounting-system sync, scanned-PDF OCR, tax
            filing or automatic bank reconciliation is offered. Hosted files are
            limited to 4 MB, imports to 2,000 rows and each workspace to the
            existing 10,000-observation import boundary. Monthly allowances
            above are proposals, not increases to those technical limits.
          </p>
        </details>
        <details>
          <summary>
            Why not promise unlimited AI or “cheaper than everyone”?
          </summary>
          <p>
            Model calls and storage incur costs. The proposed plans use bounded
            allowances; there is no automatic overage charge. Costs, applicable
            taxes and final commercial terms must be confirmed before paid
            subscriptions open. Zoho Books also offers a free plan; ProfitLens
            does not claim to replace its accounting or compliance features.
          </p>
        </details>
      </section>
    </main>
  );
}
