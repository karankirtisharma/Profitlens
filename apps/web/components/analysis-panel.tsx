"use client";

import { useState } from "react";
import { api, type RecordData } from "../lib/workspace";

type Finding = {
  id: string;
  rule: string;
  actual: string;
  expected: string;
  difference: string;
  unit: string;
  formula: string;
  source_ids: string[];
  limitation: string;
};
type Item = {
  customer_id: string;
  billing_period: string;
  currency: string;
  net_billed_revenue: string | null;
  attributed_cost: string | null;
  contribution: string | null;
  margin_percent: string | null;
  profitability_status: string;
  completeness: string;
  cost_input_hash: string;
  warnings: { code: string; message: string }[];
  findings: Finding[];
  previous: {
    billing_period: string;
    contribution: string | null;
    margin_percent: string | null;
    profitability_status: string;
  } | null;
  invoice_lines: { id: string; net_billed_revenue: string }[];
  expense_lines: { id: string; amount: string }[];
};
type Passage = {
  source_id: string;
  content: string;
  filename: string;
  page: number;
  source_url: string;
};
type Result = {
  status: string;
  summary?: string;
  reason?: string;
  limitations: string[];
  verification_errors: string[];
  answer: { citations: { source_id: string; quote: string }[] } | null;
};
type Investigation = {
  id: string;
  stale?: boolean;
  reason?: string;
  result: Result | null;
  evidence?: { passages: Passage[] };
};
type History = {
  id: string;
  question: string;
  billing_period: string;
  status: string;
};

export function AnalysisPanel({
  base,
  customers,
  canWrite,
  initialCustomer = "",
  initialPeriod = "",
}: {
  base: string;
  customers: RecordData[];
  canWrite: boolean;
  initialCustomer?: string;
  initialPeriod?: string;
}) {
  const [customer, setCustomer] = useState(initialCustomer);
  const [period, setPeriod] = useState(initialPeriod);
  const [row, setRow] = useState<Item | null>(null);
  const [question, setQuestion] = useState(
    "What do the monthly service contract and recorded margin show?",
  );
  const [reviewNote, setReviewNote] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [passages, setPassages] = useState<Passage[] | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(
    null,
  );
  const [history, setHistory] = useState<History[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await action();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }
  function reset() {
    setRow(null);
    setPassages(null);
    setInvestigation(null);
    setHistory([]);
    setReviewed(false);
    setReviewNote("");
  }
  async function load() {
    const result = await api<{ items: Item[] }>(
      `${base}/profitability?customer_id=${encodeURIComponent(customer)}${period ? `&billing_period=${encodeURIComponent(period)}` : ""}`,
    );
    setRow(result.items[0] || null);
    if (!result.items.length)
      setMessage(
        "No financial period is available. Import invoices or expenses first.",
      );
    setReviewed(false);
    setPassages(null);
    setInvestigation(null);
  }
  const query = row
    ? `customer_id=${encodeURIComponent(row.customer_id)}&billing_period=${encodeURIComponent(row.billing_period)}&q=${encodeURIComponent(question)}`
    : "";
  return (
    <div className="view-stack finance-view analysis-view">
      <section className="panel glass">
        <h2>Customer-period profitability</h2>
        <p className="finance-note">
          Revenue excludes tax and subtracts discounts and refunds. Contribution
          subtracts recorded direct costs; it is not net profit.
        </p>
        <form
          className="form-grid"
          onSubmit={(e) => {
            e.preventDefault();
            void run(load);
          }}
        >
          <label>
            Analysis customer
            <select
              required
              value={customer}
              disabled={busy}
              onChange={(e) => {
                setCustomer(e.target.value);
                reset();
              }}
            >
              <option value="">Select a customer</option>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name || c.customer_id} · {c.customer_id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Analysis month
            <input
              type="month"
              value={period}
              disabled={busy}
              onChange={(e) => {
                setPeriod(e.target.value);
                reset();
              }}
            />
          </label>
          <button className="primary" disabled={busy || !customer}>
            {busy ? "Working…" : "Load analysis"}
          </button>
        </form>
        <p className="finance-note">
          Leave the month blank to use the latest recorded period. Thresholds:
          pricing difference &gt; 1 currency unit, cost increase &gt; 25%,
          margin decline &gt; 10 percentage points. Thresholds are configurable
          through the API.
        </p>
        {error && <p role="alert">{error}</p>}
        {message && <p role="status">{message}</p>}
      </section>
      {row && (
        <>
          <section className="panel glass" aria-label="Profitability results">
            <h2>
              {row.customer_id} · {row.billing_period}
            </h2>
            <p className="tag">
              {row.profitability_status} · costs {row.completeness}
            </p>
            <dl className="finance-metrics">
              {[
                ["Net billed revenue", row.net_billed_revenue],
                ["Recorded costs", row.attributed_cost],
                ["Contribution", row.contribution],
                ["Margin", row.margin_percent],
              ].map(([name, value]) => (
                <div key={name}>
                  <dt>{name}</dt>
                  <dd>
                    {value === null
                      ? "Unavailable"
                      : `${value} ${name === "Margin" ? "%" : row.currency}`}
                  </dd>
                </div>
              ))}
            </dl>
            {row.previous && (
              <p>
                Prior month ({row.previous.billing_period}): contribution{" "}
                {row.previous.contribution ?? "unavailable"}; margin{" "}
                {row.previous.margin_percent ?? "unavailable"}% ·{" "}
                {row.previous.profitability_status}.
              </p>
            )}
            <p className="finance-note">
              {row.profitability_status === "confirmed"
                ? "An authorized user reviewed these exact cost inputs. This is an attestation, not an external audit."
                : "Provisional amounts may omit costs. Missing costs are never treated as zero."}
            </p>
            <details>
              <summary>Calculation sources and quality warnings</summary>
              <ul>
                {row.invoice_lines.map((i) => (
                  <li key={i.id}>
                    <a
                      href={`/api${base}/records/invoices/${encodeURIComponent(i.id)}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Invoice {i.id}
                    </a>
                    : net billed {i.net_billed_revenue}
                  </li>
                ))}
                {row.expense_lines.map((e) => (
                  <li key={e.id}>
                    <a
                      href={`/api${base}/records/expenses/${encodeURIComponent(e.id)}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Expense {e.id}
                    </a>
                    : {e.amount}
                  </li>
                ))}
              </ul>
              <ul>
                {row.warnings.map((w, i) => (
                  <li key={i}>{w.message}</li>
                ))}
              </ul>
            </details>
            {canWrite && row.profitability_status !== "unavailable" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void run(async () => {
                    await api(
                      `${base}/profitability/${encodeURIComponent(row.customer_id)}/${row.billing_period}/cost-review`,
                      {
                        method: "PUT",
                        body: JSON.stringify({
                          input_hash: row.cost_input_hash,
                          note: reviewNote,
                        }),
                      },
                    );
                    await load();
                    setMessage(
                      "Cost review saved. Editing the source expenses will invalidate it.",
                    );
                  });
                }}
              >
                <label>
                  <input
                    type="checkbox"
                    checked={reviewed}
                    onChange={(e) => setReviewed(e.target.checked)}
                    required
                    disabled={busy}
                  />{" "}
                  I reviewed all direct costs for this customer and month.
                </label>
                <label>
                  Review note
                  <input
                    value={reviewNote}
                    minLength={10}
                    maxLength={500}
                    required
                    disabled={busy}
                    onChange={(e) => setReviewNote(e.target.value)}
                    placeholder="Describe how you checked completeness"
                  />
                </label>
                <button className="secondary" disabled={busy || !reviewed}>
                  Confirm reviewed costs
                </button>
              </form>
            )}
          </section>
          <section className="panel glass">
            <h2>Discrepancies for review</h2>
            {row.findings.length === 0 ? (
              <p>
                No configured rule triggered. This does not establish that the
                records are error-free. Cost and margin comparisons require
                confirmed costs in both months.
              </p>
            ) : (
              row.findings.map((f) => (
                <article key={f.id} className="finance-note">
                  <h3>{f.rule.replaceAll("_", " ")}</h3>
                  <p>
                    Observed {f.actual}; reference {f.expected}; difference{" "}
                    {f.difference} {f.unit}.
                  </p>
                  <p>{f.formula}</p>
                  <p>Sources: {f.source_ids.join(", ")}</p>
                  <p>{f.limitation}</p>
                </article>
              ))
            )}
          </section>
          <section className="panel glass">
            <h2>Contract evidence & investigations</h2>
            <p>
              Search uses page-attributed BM25 lexical retrieval, restricted to
              this customer and reviewed contracts covering the month. It can
              miss paraphrases.
            </p>
            <label>
              Business question
              <textarea
                value={question}
                minLength={5}
                maxLength={1000}
                disabled={busy}
                onChange={(e) => {
                  setQuestion(e.target.value);
                  setPassages(null);
                  setInvestigation(null);
                }}
              />
            </label>
            <div className="heading-actions">
              <button
                className="secondary"
                disabled={busy || question.trim().length < 5}
                onClick={() =>
                  void run(async () => {
                    const r = await api<{ items: Passage[] }>(
                      `${base}/evidence/search?${query}`,
                    );
                    setPassages(r.items);
                  })
                }
              >
                Find contract evidence
              </button>
              <button
                className="primary"
                disabled={busy || question.trim().length < 5}
                onClick={() =>
                  void run(async () => {
                    setInvestigation(null);
                    const r = await api<Investigation>(
                      `${base}/investigations`,
                      {
                        method: "POST",
                        body: JSON.stringify({
                          customer_id: row.customer_id,
                          billing_period: row.billing_period,
                          question,
                        }),
                      },
                    );
                    setInvestigation(r);
                  })
                }
              >
                Generate with configured AI
              </button>
              <button
                className="secondary"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    setHistory(
                      await api<History[]>(
                        `${base}/investigations?customer_id=${encodeURIComponent(row.customer_id)}`,
                      ),
                    );
                    setMessage("Recent investigations loaded.");
                  })
                }
              >
                Load history
              </button>
              {canWrite && (
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      const r = await api<{
                        documents: number;
                        passages: number;
                      }>(`${base}/evidence/reindex`, { method: "POST" });
                      setMessage(
                        `Indexed ${r.documents} documents into ${r.passages} passages.`,
                      );
                    })
                  }
                >
                  Index existing contracts
                </button>
              )}
            </div>
            <p className="finance-note">
              AI generation sends the authorized question, financial evidence
              and selected contract text to the backend-configured provider. A
              configured key/model and complete evidence are required. Values
              and quotes are checked; relevance still requires human review.
            </p>
            {passages &&
              (passages.length ? (
                passages.map((p) => (
                  <blockquote key={p.source_id}>
                    <p>{p.content}</p>
                    <a href={p.source_url} target="_blank" rel="noreferrer">
                      {p.filename} · page {p.page}
                    </a>
                  </blockquote>
                ))
              ) : (
                <p>
                  No matching reviewed evidence found. Review the contract dates
                  or try more specific wording.
                </p>
              ))}
            {investigation && (
              <article aria-live="polite">
                <h3>
                  {investigation.stale
                    ? "Stale investigation"
                    : investigation.result?.status.replaceAll("_", " ")}
                </h3>
                <p>{investigation.reason || investigation.result?.reason}</p>
                <p>{investigation.result?.summary}</p>
                {investigation.result?.answer?.citations.map((c, i) => {
                  const p = investigation.evidence?.passages.find(
                    (p) => p.source_id === c.source_id,
                  );
                  return (
                    <blockquote key={i}>
                      <p>{c.quote}</p>
                      {p && (
                        <a href={p.source_url} target="_blank" rel="noreferrer">
                          {p.filename} · page {p.page}
                        </a>
                      )}
                    </blockquote>
                  );
                })}
                <ul>
                  {investigation.result?.limitations.map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              </article>
            )}
            {history.length > 0 && (
              <ul>
                {history.map((h) => (
                  <li key={h.id}>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() =>
                        void run(async () => {
                          setInvestigation(
                            await api<Investigation>(
                              `${base}/investigations/${h.id}`,
                            ),
                          );
                        })
                      }
                    >
                      {h.billing_period} · {h.question} · {h.status}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
