"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Database,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  Users,
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
      value: customers.length,
      caption: "Accessible in your workspace",
      icon: Users,
      view: "customers" as View,
    },
    {
      label: "Invoice records",
      value: invoices.length,
      caption: "Linked to customer accounts",
      icon: FileSpreadsheet,
      view: "invoices" as View,
    },
    {
      label: "Expense records",
      value: expenses.length,
      caption: "Organized by billing month",
      icon: FileText,
      view: "expenses" as View,
    },
    {
      label: "Contract documents",
      value: contracts.length,
      caption: `${reviewed} with reviewed monthly terms`,
      icon: FileCheck2,
      view: "contracts" as View,
    },
  ];
  const capped = metrics.some((m) => m.value === 200);
  const current =
    active && months.includes(active) ? active : months[months.length - 1];
  return (
    <div className="overview">
      <section className="overview-banner glass-panel">
        <div>
          <span className="eyebrow">YOUR BUSINESS, IN FOCUS</span>
          <h2>
            One place for the details
            <br />
            that matter.
          </h2>
          <p>Build clarity with connected records and traceable evidence.</p>
          <button
            className="primary"
            onClick={() => changeView(canWrite ? "imports" : "customers")}
          >
            {canWrite ? "Import business data" : "Browse customers"}
            <ArrowRight size={16} />
          </button>
        </div>
        <div className="banner-art" aria-hidden="true">
          <div className="banner-orbit" />
          <span className="banner-node node-a">
            <Users size={23} />
          </span>
          <span className="banner-node node-b">
            <FileText size={23} />
          </span>
          <div className="banner-emblem">
            <span className="brand-mark">
              <span />
              <span />
              <span />
            </span>
          </div>
          <span className="banner-node node-c">
            <FileCheck2 size={23} />
          </span>
          <span className="banner-caption">CONNECTED BY CUSTOMER</span>
        </div>
      </section>
      <div className="metric-grid grid grid-cols-2 xl:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <motion.button
            className="metric-card"
            key={m.label}
            onClick={() => changeView(m.view)}
            whileHover={animate ? { transform: "translateY(-3px)" } : undefined}
            whileTap={animate ? { transform: "scale(0.985)" } : undefined}
            aria-label={`View ${m.label.toLowerCase()}`}
          >
            <div className="metric-top">
              <span>{m.label}</span>
              <m.icon size={17} strokeWidth={1.5} />
            </div>
            <div className="metric-value">
              {m.value.toLocaleString()}
              {m.value === 200 && "+"}
              <ArrowUpRight size={19} />
            </div>
            <p>{m.caption}</p>
          </motion.button>
        ))}
      </div>
      <div className="insight-grid">
        <section
          className="panel activity-panel"
          aria-labelledby="activity-heading"
        >
          <div className="chart-heading">
            <div>
              <span className="eyebrow">WORKSPACE ACTIVITY</span>
              <h2 id="activity-heading">Records by billing month</h2>
            </div>
            <select
              aria-label="Chart month range"
              value={range}
              onChange={(e) => {
                setRange(e.target.value);
                setActive(null);
              }}
            >
              <option value="6">6 recorded months</option>
              <option value="12">12 recorded months</option>
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
                ? `${monthLabel(current)} · ${grouped.get(current)!.invoices} invoices · ${grouped.get(current)!.expenses} expenses`
                : "No billing records yet"}
            </span>
          </div>
          {months.length ? (
            <div
              className="bar-chart"
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
                      className={`chart-column ${active === month ? "selected" : ""}`}
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
                                duration: animate ? 0.55 : 0,
                                delay: animate ? index * 0.045 : 0,
                                ease: [0.23, 1, 0.32, 1],
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
              <Database size={28} strokeWidth={1} />
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
        </section>
        <section className="panel evidence-panel">
          <span className="eyebrow">DOCUMENT EVIDENCE</span>
          <div className="flex items-start justify-between gap-3">
            <h2>Contract readiness</h2>
            <FileCheck2 size={20} strokeWidth={1.5} />
          </div>
          <div className="evidence-meter">
            <svg viewBox="0 0 150 150" aria-hidden="true">
              <circle cx="75" cy="75" r="62" />
              <motion.circle
                className="meter-value"
                cx="75"
                cy="75"
                r="62"
                pathLength="1"
                strokeDasharray={`${contracts.length ? reviewed / contracts.length : 0} 1`}
                initial={animate ? { opacity: 0 } : false}
                animate={{ opacity: 1 }}
              />
            </svg>
            <div>
              <strong>
                {reviewed}
                <small>/{contracts.length}</small>
              </strong>
              <span>reviewed</span>
            </div>
          </div>
          <p>
            {contracts.length
              ? `${contracts.length - reviewed} documents awaiting verified monthly terms.`
              : "Upload a contract to begin reviewing its source text and monthly terms."}
          </p>
          <button className="secondary" onClick={() => changeView("contracts")}>
            Open contract library
            <ArrowUpRight size={15} />
          </button>
        </section>
      </div>
      <section className="workflow-section">
        <div className="section-heading">
          <h2>A clear path through your data</h2>
          <span className="muted">YOUR WORKFLOW</span>
        </div>
        <div className="workflow-grid">
          {[
            {
              number: "01",
              heading: "Organize",
              text: "Give every invoice and expense a consistent customer identity.",
              view: "customers" as View,
              icon: Users,
            },
            {
              number: "02",
              heading: canWrite ? "Validate & import" : "Explore records",
              text: canWrite
                ? "Review CSV validation and source rows before saving."
                : "Inspect the invoices linked to your assigned customers.",
              view: (canWrite ? "imports" : "invoices") as View,
              icon: FileSpreadsheet,
            },
            {
              number: "03",
              heading: "Review evidence",
              text: "Read private PDFs alongside their reviewed pricing terms.",
              view: "contracts" as View,
              icon: FileCheck2,
            },
          ].map((item) => (
            <button
              className="workflow-card"
              key={item.number}
              onClick={() => changeView(item.view)}
            >
              <div>
                <item.icon size={20} strokeWidth={1.5} />
                <span>{item.number}</span>
              </div>
              <h3>
                {item.heading}
                <ArrowUpRight size={16} />
              </h3>
              <p>{item.text}</p>
            </button>
          ))}
        </div>
      </section>
      <div className="scope-note">
        <Check size={16} />
        <p>
          <strong>Week 3 · Business data foundation.</strong> Financial
          calculations, anomaly detection and AI explanations are planned for
          later releases.
        </p>
      </div>
    </div>
  );
}
