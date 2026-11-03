"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Download, FileText, Search } from "lucide-react";
import { api, message, type Contract, type View } from "../lib/workspace";
import styles from "./workspace-hubs.module.css";

type Document = {
  id: string;
  filename: string;
  state: string;
  format?: string;
  created_at?: string;
};
type Entry = Document & {
  category: "Source file" | "Contract";
  download: string;
};

export function DocumentLibrary({
  base,
  canWrite,
  navigate,
}: {
  base: string;
  canWrite: boolean;
  navigate: (view: View) => void;
}) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      canWrite
        ? api<Document[]>(`${base}/sources`, { signal: controller.signal })
        : Promise.resolve([]),
      api<Contract[]>(`${base}/contracts`, { signal: controller.signal }),
    ])
      .then(([sources, contracts]) => {
        if (controller.signal.aborted) return;
        setEntries([
          ...sources.map((d) => ({
            ...d,
            category: "Source file" as const,
            download: `${base}/sources/${encodeURIComponent(d.id)}/file`,
          })),
          ...contracts.map((d) => ({
            ...d,
            category: "Contract" as const,
            format: "pdf",
            download: `${base}/contracts/${encodeURIComponent(d.id)}/file`,
          })),
        ]);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(message(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [base, canWrite]);
  const filtered = entries.filter(
    (d) =>
      (!category || d.category === category) &&
      (!status || d.state === status) &&
      d.filename.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <section className="panel glass" aria-label="Document library">
      <div className={styles.heading}>
        <div>
          <h2>Your document library</h2>
          <p>Original files and contract evidence, with protected downloads.</p>
        </div>
        {canWrite && (
          <button className="primary" onClick={() => navigate("data")}>
            Upload source file <ArrowRight size={16} />
          </button>
        )}
      </div>
      <div className="form-grid">
        <label>
          Find a document
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by filename"
          />
        </label>
        <label>
          Document type
          <select
            aria-label="Document type"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All types</option>
            <option>Source file</option>
            <option>Contract</option>
          </select>
        </label>
        <label>
          Review status
          <select
            aria-label="Review status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            {[...new Set(entries.map((d) => d.state))].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <p role="alert" className="alert error">
          {error}
        </p>
      )}
      {loading ? (
        <p role="status">Loading documents…</p>
      ) : (
        <>
          <p>
            {filtered.length} files shown.{" "}
            {canWrite
              ? "Showing up to 100 recent source uploads and 200 accessible contracts. Filters search these loaded files."
              : "Up to 200 contracts for your assigned customers are available here. Full source files require finance access."}
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>File</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={`${d.category}-${d.id}`}>
                    <td>
                      <FileText size={15} /> {d.filename}
                    </td>
                    <td>
                      {d.category} · {d.format?.toUpperCase() || "File"}
                    </td>
                    <td>
                      <span className="badge">{d.state}</span>
                    </td>
                    <td>
                      <a
                        className="secondary"
                        href={`/api${d.download}`}
                        aria-label={`Download ${d.filename}`}
                      >
                        <Download size={14} /> Download
                      </a>
                    </td>
                  </tr>
                ))}
                {!filtered.length && (
                  <tr>
                    <td colSpan={4}>
                      No documents match. Try another filter or import a
                      supported source.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
      <div className={styles.heading}>
        <button className="secondary" onClick={() => navigate("contracts")}>
          Review contract terms
        </button>
        <button className="secondary" onClick={() => navigate("data")}>
          Review source mappings
        </button>
      </div>
    </section>
  );
}

export function ReportsHub({
  canWrite,
  navigate,
}: {
  canWrite: boolean;
  navigate: (view: View) => void;
}) {
  const reports: {
    view: View;
    title: string;
    description: string;
    basis: string;
  }[] = [
    {
      view: "data",
      title: "Monthly business review",
      description:
        "Compare recorded sales or spending with the previous month. Inspect the records behind each change.",
      basis: "Source observations · missing months stay unavailable",
    },
    {
      view: "finance",
      title: "Revenue & attributed costs",
      description:
        "Review customer-period revenue and recorded costs, with data-quality warnings.",
      basis: "Verified invoice and cost ledger",
    },
    {
      view: "analysis",
      title: "Profitability & evidence",
      description:
        "Investigate contribution, margin changes and reviewed contract pricing using linked evidence.",
      basis: "Profit requires sufficient cost evidence",
    },
    ...(canWrite
      ? [
          {
            view: "accounts" as View,
            title: "Receivables & payables",
            description:
              "Track explicitly enrolled invoices and vendor bills, partial settlements and balances still due.",
            basis: "Recorded settlements · not a bank balance or profit report",
          },
        ]
      : []),
  ];
  return (
    <section aria-label="Report library">
      <div className={styles.cards}>
        {reports.map((r) => (
          <button
            key={r.view}
            className={`panel glass ${styles.card}`}
            onClick={() => navigate(r.view)}
          >
            <Search size={22} />
            <h2>{r.title}</h2>
            <p>{r.description}</p>
            <small>{r.basis}</small>
            <span>
              Open report <ArrowRight size={16} />
            </span>
          </button>
        ))}
      </div>
      <p className={styles.note}>
        Each report keeps its own financial meaning. Sales, spending, cash
        movements and commitments are not combined into an unsupported profit
        figure.
      </p>
    </section>
  );
}

export function QuickStart({
  canWrite,
  navigate,
}: {
  canWrite: boolean;
  navigate: (view: View) => void;
}) {
  return (
    <section
      className={`panel glass ${styles.quick}`}
      aria-label="Workspace shortcuts"
    >
      <div>
        <h2>What would you like to do?</h2>
        <p>Choose a task. Your workspace and access stay with you.</p>
      </div>
      <div className={styles.actions}>
        {canWrite && (
          <button className="primary" onClick={() => navigate("data")}>
            Import & review data
          </button>
        )}
        <button className="secondary" onClick={() => navigate("reports")}>
          Explore reports
        </button>
        <button className="secondary" onClick={() => navigate("documents")}>
          Find a document
        </button>
        {canWrite && (
          <button className="secondary" onClick={() => navigate("accounts")}>
            Track money due
          </button>
        )}
      </div>
    </section>
  );
}
