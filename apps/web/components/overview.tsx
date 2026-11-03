"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  Database,
  FileText,
  Info,
} from "lucide-react";
import { Contract, RecordData, View } from "../lib/workspace";
import { useExperience } from "./experience";

export type OverviewData = {
  invoices: RecordData[];
  expenses: RecordData[];
  contracts: Contract[];
  summary?: {
    currency: string;
    counts: Record<string, number>;
    record_months?: {
      billing_period: string;
      invoice_count: number;
      expense_count: number;
    }[];
    reported_count: number | null;
    reported_sales: string | null;
    verified_net_revenue: string | null;
    months: {
      billing_period: string;
      invoice_count: number;
      reported_count: number;
      reported_sales: string | null;
      verified_net_revenue: string | null;
    }[];
    top_reported_customers: {
      customer_id: string;
      reported_sales: string;
      invoice_count: number;
    }[];
  };
};
type Props = {
  customers: RecordData[];
  data: OverviewData;
  canWrite: boolean;
  changeView: (view: View) => void;
};
const monthLabel = (month: string) =>
  new Intl.DateTimeFormat("en", {
    month: "short",
    year: "2-digit",
    timeZone: "UTC",
  }).format(new Date(`${month}-01T00:00:00Z`));
const ease = [0.23, 1, 0.32, 1] as const;
// Names the files a set of records came from, for the source tab behind a figure.
function sources(list: RecordData[], total = list.length) {
  if (!list.length)
    return total ? "Source details not loaded" : "No records yet";
  const counts = new Map<string, number>();
  for (const record of list) {
    const name =
      record.source?.type === "csv"
        ? record.source.filename || "CSV import"
        : "manual entry";
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const names = [...counts]
    .map(([name, count]) => `${name} × ${count}`)
    .join("  ·  ");
  return list.length < total
    ? `${list.length} of ${total} sources loaded · ${names}`
    : names;
}

export function Overview({ customers, data, canWrite, changeView }: Props) {
  const { animate } = useExperience();
  const [range, setRange] = useState("6");
  const [active, setActive] = useState<string | null>(null);
  const { invoices, expenses, contracts, summary } = data;
  const count = (kind: string, loaded: number) =>
    summary?.counts[kind] ?? loaded;
  const contractCount = count("contracts", contracts.length);
  const reviewed =
    summary?.counts.reviewed_contracts ??
    contracts.filter((c) => c.state === "reviewed").length;
  const partialContractReview =
    summary?.counts.reviewed_contracts === undefined &&
    contractCount > contracts.length;
  const reviewDenominator = partialContractReview
    ? contracts.length
    : contractCount;
  const completeActivity = summary?.record_months !== undefined;
  const grouped = new Map<string, { invoices: number; expenses: number }>();
  for (const [kind, list] of [
    ["invoices", invoices],
    ["expenses", expenses],
  ] as const) {
    for (const record of list) {
      const month = String(record.billing_period || "");
      if (!/^\d{4}-\d{2}$/.test(month)) continue;
      const counts = grouped.get(month) || { invoices: 0, expenses: 0 };
      counts[kind] += 1;
      grouped.set(month, counts);
    }
  }
  if (summary?.record_months) {
    grouped.clear();
    for (const month of summary.record_months) {
      grouped.set(month.billing_period, {
        invoices: month.invoice_count,
        expenses: month.expense_count,
      });
    }
  }
  const months = [...grouped.keys()].sort().slice(-Number(range));
  const maximum = Math.max(
    1,
    ...months.map((month) =>
      Math.max(grouped.get(month)!.invoices, grouped.get(month)!.expenses),
    ),
  );
  const metrics = [
    {
      label: "Customers",
      name: "customers",
      value: count("customers", customers.length),
      origin: sources(customers, count("customers", customers.length)),
      view: "customers" as View,
    },
    {
      label: "Invoices",
      name: "invoice records",
      value: count("invoices", invoices.length),
      origin: sources(invoices, count("invoices", invoices.length)),
      view: "invoices" as View,
    },
    {
      label: "Expenses",
      name: "expense records",
      value: count("expenses", expenses.length),
      origin: sources(expenses, count("expenses", expenses.length)),
      view: "expenses" as View,
    },
    {
      label: "Contracts",
      name: "contract documents",
      value: contractCount,
      origin: contractCount
        ? `${reviewed} of ${reviewDenominator}${partialContractReview ? " loaded documents" : ""} with reviewed terms`
        : canWrite
          ? "Upload a contract PDF"
          : "No contract PDFs yet",
      view: "contracts" as View,
    },
  ].filter(
    (m) =>
      m.value > 0 ||
      (!summary?.counts.financial_facts &&
        (m.view === "customers" || m.view === "invoices")),
  );
  // The records these figures count, shown on the pane behind the inventory.
  const nameOf = (id: string) =>
    customers.find((c) => c.customer_id === id)?.name || id;
  const amount = (value: unknown) =>
    Number(value).toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  const ledger = [
    ...invoices.map((r) => [
      String(r.invoice_id),
      nameOf(r.customer_id),
      amount(r.total),
    ]),
    ...expenses.map((r) => [
      String(r.expense_id),
      nameOf(r.customer_id),
      amount(r.amount),
    ]),
  ];
  const counted = (
    ledger.length
      ? ledger
      : customers.map((r) => [r.customer_id, String(r.name), ""])
  ).slice(0, 6);
  const capped = summary
    ? count("invoices", invoices.length) > invoices.length ||
      count("expenses", expenses.length) > expenses.length
    : invoices.length === 200 || expenses.length === 200;
  const reportedMaximum = Math.max(
    1,
    ...(summary?.months ?? []).map((month) =>
      Math.abs(Number(month.reported_sales ?? 0)),
    ),
  );
  const negativeReported = summary?.months.some(
    (month) => Number(month.reported_sales ?? 0) < 0,
  );
  const current =
    active && months.includes(active) ? active : months[months.length - 1];
  const enter = (index: number) => ({
    initial: animate ? { opacity: 0, transform: "translateY(10px)" } : false,
    animate: { opacity: 1, transform: "translateY(0px)" },
    transition: animate
      ? { duration: 0.5, delay: index * 0.06, ease }
      : { duration: 0 },
  });
  if (
    summary?.counts.financial_facts &&
    !count("invoices", invoices.length) &&
    !count("expenses", expenses.length)
  )
    return (
      <section className="panel glass">
        <h2>Source-first workspace</h2>
        <p>
          {summary.counts.source_documents} original uploads ·{" "}
          {summary.counts.financial_facts} financial observations ·{" "}
          {summary.counts.review_tasks} source reviews pending
        </p>
        <p>
          Explore available records below. Missing invoices, costs and contracts
          are not invented to fill a dashboard.
        </p>
      </section>
    );
  return (
    <div className="overview">
      {summary && (
        <section className="panel glass">
          <h2>Data workspace</h2>
          <p>
            {summary.counts.source_documents || 0} retained source documents ·{" "}
            {summary.counts.financial_facts || 0} typed observations ·{" "}
            {summary.counts.review_tasks || 0} source reviews pending
          </p>
          <p>
            Documents and observations do not require customers or contracts.
            Amounts are grouped by financial meaning; profit is calculated only
            from the separate verified financial workflow.
          </p>
          <button className="primary" onClick={() => changeView("data")}>
            Explore source data & insights <ArrowUpRight size={15} />
          </button>
        </section>
      )}
      {summary && (
        <section
          className="panel glass"
          aria-label="Available financial insights"
        >
          <h2>What these records can tell you</h2>
          <div className="form-grid">
            {summary.reported_sales !== null && (
              <div>
                <p className="muted">Reported sales · tax basis unknown</p>
                <h2>
                  {summary.currency} {summary.reported_sales}
                </h2>
                <p>
                  {summary.reported_count} source sales invoices. Not net
                  revenue, cash received or profit.
                </p>
              </div>
            )}
            {summary.verified_net_revenue !== null && (
              <div>
                <p className="muted">Recorded net billed revenue</p>
                <h2>
                  {summary.currency} {summary.verified_net_revenue}
                </h2>
                <p>
                  Verified-breakdown invoices only; any reported sales are
                  excluded.
                </p>
              </div>
            )}
            <div>
              <p className="muted">Data coverage</p>
              <p>
                {summary.counts.expenses
                  ? "Recorded customer costs available; completeness requires review."
                  : "Costs unknown — contribution and margin unavailable."}
              </p>
              <p>
                {summary.counts.contracts
                  ? "Contracts present — pricing checks require applicable reviewed terms."
                  : "Contracts not provided. Optional for sales reporting; pricing compliance unavailable."}
              </p>
            </div>
          </div>
        </section>
      )}
      {!!summary?.reported_count && (
        <div className="insight-grid">
          <section className="panel glass" aria-label="Reported sales by month">
            <h2>Reported sales by month</h2>
            <p>
              Imported selection only · {summary.currency} · unknown tax basis
            </p>
            <div className="sales-bars">
              {summary.months
                .filter((m) => m.reported_sales !== null)
                .map((m) => (
                  <div key={m.billing_period}>
                    <span>{monthLabel(m.billing_period)}</span>
                    <div className="sales-track">
                      <span
                        style={{
                          width: `${(100 * Math.abs(Number(m.reported_sales))) / reportedMaximum}%`,
                        }}
                      />
                    </div>
                    <strong>{m.reported_sales}</strong>
                  </div>
                ))}
            </div>
            <p className="chart-note">
              Sales movements in this cohort are observations, not evidence of
              their cause or whole-company growth.
              {negativeReported &&
                " Bar lengths show absolute amounts; displayed values preserve negative signs."}
            </p>
          </section>
          <section className="panel glass">
            <h2>Leading customers by reported sales</h2>
            <p>Anonymous source IDs; ranking within this imported selection.</p>
            <ol className="doc-stack">
              {summary.top_reported_customers.map((c) => (
                <li key={c.customer_id}>
                  <span>{nameOf(c.customer_id)}</span>
                  <strong>
                    {summary.currency} {c.reported_sales}
                  </strong>
                  <small>{c.invoice_count} invoices</small>
                </li>
              ))}
            </ol>
            <button
              className="secondary"
              onClick={() => changeView("invoices")}
            >
              Inspect sales invoice sources <ArrowUpRight size={15} />
            </button>
          </section>
        </div>
      )}
      <div className="inventory-stack">
        {counted.length > 0 && (
          <div className="inventory-depth glass" aria-hidden="true">
            {counted.map(([id, name, total], index) => (
              <span className="depth-row" key={`${id}-${index}`}>
                <b>{id}</b>
                <span>{name}</span>
                {total && <i>{total}</i>}
              </span>
            ))}
          </div>
        )}
        <section className="inventory glass" aria-label="Record inventory">
          {metrics.map((m, index) => (
            <motion.button
              className={`metric ${m.value === 0 ? "is-empty" : ""}`}
              key={m.label}
              onClick={() => changeView(m.view)}
              aria-label={`View ${m.name}`}
              {...enter(index)}
            >
              <span className="metric-label">{m.label}</span>
              <span className="metric-value">
                {m.value.toLocaleString()}
                {!summary && m.value === 200 && "+"}
              </span>
              <span className="metric-origin">{m.origin}</span>
              <ArrowUpRight className="metric-go" size={17} />
            </motion.button>
          ))}
        </section>
      </div>
      <div className="insight-grid">
        <motion.section
          className="panel glass activity-panel"
          aria-labelledby="activity-heading"
          {...enter(2)}
        >
          <div className="chart-heading">
            <div>
              <h2 id="activity-heading">Records by billing month</h2>
              <p>
                {completeActivity || !capped
                  ? "Invoices and expenses counted per billing month."
                  : "Loaded preview only — not all workspace records."}
              </p>
            </div>
            <select
              aria-label="Chart month range"
              value={range}
              onChange={(e) => {
                setRange(e.target.value);
                setActive(null);
              }}
            >
              <option value="6">Up to 6 recorded months</option>
              <option value="12">Up to 12 recorded months</option>
            </select>
          </div>
          <div className="chart-summary">
            <div className="chart-legend">
              <span>
                <i className="invoice-dot" /> Invoices
              </span>
              <span>
                <i className="expense-dot" /> Expenses
              </span>
            </div>
            <span className="chart-readout" aria-live="polite">
              {current
                ? `${monthLabel(current)} · ${grouped.get(current)!.invoices} invoices, ${grouped.get(current)!.expenses} expenses`
                : "No billing records yet"}
            </span>
          </div>
          {months.length ? (
            <div
              className={`bar-chart ${months.length <= 2 ? "compact" : ""}`}
              role="group"
              aria-label="Invoice and expense record counts"
            >
              <div className="chart-axis" aria-hidden="true">
                <span>{maximum}</span>
                <span>{Math.floor(maximum / 2)}</span>
                <span>0</span>
              </div>
              <div className="chart-plot">
                <div className="chart-gridlines" aria-hidden="true">
                  <i />
                  <i />
                  <i />
                </div>
                <div className="chart-columns">
                  {months.map((month, index) => (
                    <button
                      key={month}
                      className={`chart-column ${current === month ? "selected" : ""}`}
                      onClick={() => setActive(month)}
                      aria-pressed={current === month}
                      aria-label={`${monthLabel(month)}: ${grouped.get(month)!.invoices} invoices, ${grouped.get(month)!.expenses} expenses`}
                    >
                      <span className="chart-bars" aria-hidden="true">
                        {(["invoices", "expenses"] as const).map((kind) => (
                          <span
                            className={`bar-slot ${kind}`}
                            key={kind}
                            style={{
                              height: `${(grouped.get(month)![kind] / maximum) * 100}%`,
                            }}
                          >
                            <motion.span
                              className="chart-bar"
                              initial={
                                animate ? { transform: "scaleY(0)" } : false
                              }
                              animate={{ transform: "scaleY(1)" }}
                              transition={{
                                duration: animate ? 0.7 : 0,
                                delay: animate
                                  ? 0.15 +
                                    index * 0.05 +
                                    (kind === "expenses" ? 0.04 : 0)
                                  : 0,
                                ease,
                              }}
                            />
                          </span>
                        ))}
                      </span>
                      <span className="chart-month">{monthLabel(month)}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="chart-empty">
              <Database size={26} strokeWidth={1.2} />
              <p>Every clear picture starts with a record.</p>
              <button
                className="text-button"
                onClick={() => changeView(canWrite ? "imports" : "invoices")}
              >
                {canWrite ? "Import your first records" : "Browse invoices"}
                <ArrowRight size={14} />
              </button>
            </div>
          )}
          <p className="chart-note">
            Record counts, not financial performance.{" "}
            {completeActivity
              ? "Counts include all accessible workspace records, not just the loaded preview."
              : capped
                ? "Chart uses up to 200 loaded invoices and 200 loaded expenses; inventory totals above cover all accessible records."
                : "Based on the accessible records loaded from this workspace."}
          </p>
        </motion.section>
        {contractCount > 0 ? (
          <motion.section
            className="panel glass evidence-panel"
            aria-labelledby="evidence-heading"
            {...enter(3)}
          >
            <h2 id="evidence-heading">Contract readiness</h2>
            <div className="evidence-count">
              <strong>
                {reviewed}/{reviewDenominator}
              </strong>
              <span>
                {partialContractReview
                  ? "loaded documents with reviewed monthly terms"
                  : "documents with reviewed monthly terms"}
              </span>
            </div>
            {contracts.length > 0 && (
              <ul className="doc-stack" aria-label="Latest contracts">
                {contracts.slice(0, 3).map((c) => (
                  <li key={c.id}>
                    <FileText size={15} />
                    <span className="mono">{c.filename}</span>
                    <span className={`tag ${c.state}`}>{c.state}</span>
                  </li>
                ))}
              </ul>
            )}
            <p>
              {contracts.length
                ? `${reviewDenominator - reviewed} of ${reviewDenominator}${partialContractReview ? " loaded" : ""} documents still need verified monthly terms.`
                : "Upload a contract to begin reviewing its source text and monthly terms."}
            </p>
            {partialContractReview && (
              <p>
                Readiness for {contractCount - contracts.length} additional
                documents is not included in this preview.
              </p>
            )}
            <button
              className="secondary"
              onClick={() => changeView("contracts")}
            >
              Open contract library
              <ArrowUpRight size={15} />
            </button>
          </motion.section>
        ) : (
          <section className="panel glass">
            <h2>Optional evidence, honest results</h2>
            <p>
              No contract documents have been supplied. You can still explore
              customers, sales and recorded expenses.
            </p>
            <p>
              Contract compliance is unavailable until applicable terms are
              reviewed. Missing costs never become zero.
            </p>
            <button
              className="secondary"
              onClick={() => changeView(canWrite ? "imports" : "invoices")}
            >
              {canWrite ? "Import more records" : "Browse available records"}
              <ArrowUpRight size={15} />
            </button>
          </section>
        )}
      </div>
      <div className="scope-note">
        <Info size={16} />
        <p>
          <strong>Financial analysis with traceable evidence.</strong> Review
          revenue, costs, contribution and margin in the analysis screens. Ask
          ProfitLens about accessible records; verify AI interpretations against
          the linked sources. Missing costs remain unknown.
        </p>
      </div>
    </div>
  );
}
