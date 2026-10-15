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
function sources(list: RecordData[]) {
  if (!list.length) return "No records yet";
  const counts = new Map<string, number>();
  for (const record of list) {
    const name =
      record.source?.type === "csv"
        ? record.source.filename || "CSV import"
        : "manual entry";
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  return [...counts].map(([name, count]) => `${name} × ${count}`).join("  ·  ");
}

export function Overview({ customers, data, canWrite, changeView }: Props) {
  const { animate } = useExperience();
  const [range, setRange] = useState("6");
  const [active, setActive] = useState<string | null>(null);
  const { invoices, expenses, contracts } = data;
  const reviewed = contracts.filter((c) => c.state === "reviewed").length;
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
      value: customers.length,
      origin: sources(customers),
      view: "customers" as View,
    },
    {
      label: "Invoices",
      name: "invoice records",
      value: invoices.length,
      origin: sources(invoices),
      view: "invoices" as View,
    },
    {
      label: "Expenses",
      name: "expense records",
      value: expenses.length,
      origin: sources(expenses),
      view: "expenses" as View,
    },
    {
      label: "Contracts",
      name: "contract documents",
      value: contracts.length,
      origin: contracts.length
        ? `${reviewed} of ${contracts.length} with reviewed terms`
        : canWrite
          ? "Upload a contract PDF"
          : "No contract PDFs yet",
      view: "contracts" as View,
    },
  ];
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
  const capped = metrics.some((m) => m.value === 200);
  const current =
    active && months.includes(active) ? active : months[months.length - 1];
  const enter = (index: number) => ({
    initial: animate ? { opacity: 0, transform: "translateY(10px)" } : false,
    animate: { opacity: 1, transform: "translateY(0px)" },
    transition: animate
      ? { duration: 0.5, delay: index * 0.06, ease }
      : { duration: 0 },
  });
  return (
    <div className="overview">
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
                {m.value === 200 && "+"}
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
              <p>Invoices and expenses counted per billing month.</p>
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
                      aria-pressed={active === month}
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
            {capped
              ? "One or more lists reached the 200-record preview limit."
              : "Based on the accessible records loaded from this workspace."}
          </p>
        </motion.section>
        <motion.section
          className="panel glass evidence-panel"
          aria-labelledby="evidence-heading"
          {...enter(3)}
        >
          <h2 id="evidence-heading">Contract readiness</h2>
          <div className="evidence-count">
            <strong>
              {reviewed}/{contracts.length}
            </strong>
            <span>documents with reviewed monthly terms</span>
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
              ? `${contracts.length - reviewed} of ${contracts.length} documents still need verified monthly terms.`
              : "Upload a contract to begin reviewing its source text and monthly terms."}
          </p>
          <button className="secondary" onClick={() => changeView("contracts")}>
            Open contract library
            <ArrowUpRight size={15} />
          </button>
        </motion.section>
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
