"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import { api, message } from "../lib/workspace";
import { Modal } from "./ui";
import "./operations.css";

export type OperationsView =
  "accounts" | "vendors" | "items" | "bills" | "payments";
type Row = Record<string, unknown>;
type BalanceRow = {
  document_id: string;
  party_id: string;
  party_name: string;
  total: string;
  paid: string;
  outstanding: string;
  due_on: string | null;
  status: string;
};
type Balance = {
  total: string;
  current: string;
  overdue: string;
  undated: string;
  rows: BalanceRow[];
  untracked_count?: number;
};
type Summary = {
  currency: string;
  receivables: Balance;
  payables: Balance;
  limitations: string[];
};
type Candidate = {
  invoice_id: string;
  customer_id: string;
  total: string;
  tracked: boolean;
};
type Allocation = { key: number; document_id: string; amount: string };
const headings: Record<OperationsView, string> = {
  accounts: "Receivables & payables",
  vendors: "Vendors",
  items: "Items & services",
  bills: "Vendor bills",
  payments: "Payments",
};
const explanations: Record<OperationsView, string> = {
  accounts:
    "Know what is outstanding, what is overdue, and which balances still need a reviewed starting point.",
  vendors:
    "Maintain an explicit supplier directory. Similar names are never automatically merged.",
  items:
    "Keep a reusable price reference for goods and services. This catalogue does not track stock quantities.",
  bills:
    "Record vendor obligations separately from expenses and cash payments, so amounts are not counted twice.",
  payments:
    "Record received or made payments against exact invoice or bill references, including partial settlements.",
};
const value = (row: Row, key: string) =>
  row[key] == null ? "" : String(row[key]);
// Preserve server decimal strings; display is not financial arithmetic.
const money = (amount: string | null | undefined, currency: string) => {
  if (amount == null) return "Unavailable";
  const [integer, fraction] = amount.split(".");
  return `${currency} ${integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}.${(fraction || "").padEnd(2, "0")}`;
};
const positive = (amount: string) =>
  /^\d+(\.\d+)?$/.test(amount) && /[1-9]/.test(amount);
const localDate = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
};

export function OperationsPanel({
  base,
  view,
  canWrite,
  currency,
}: {
  base: string;
  view: OperationsView;
  canWrite: boolean;
  currency: string;
}) {
  // Parent keys this component by workspace and view so no prior tenant state is retained.
  const [rows, setRows] = useState<Row[]>([]);
  const [vendors, setVendors] = useState<Row[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [editor, setEditor] = useState<"record" | "enroll" | null>(null);
  const [editing, setEditing] = useState<Row | null>(null);
  const [formError, setFormError] = useState("");
  const [direction, setDirection] = useState<"received" | "made">("received");
  const [allocations, setAllocations] = useState<Allocation[]>([
    { key: 0, document_id: "", amount: "" },
  ]);
  const [detail, setDetail] = useState<Row | null>(null);
  const [voiding, setVoiding] = useState(false);
  const endpoint = `${base}/operations`;

  useEffect(() => {
    if (!canWrite) return;
    const controller = new AbortController();
    const options = { signal: controller.signal };
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [list, balances, suppliers, invoices] = await Promise.all([
          view === "accounts"
            ? Promise.resolve([])
            : api<Row[]>(`${endpoint}/${view}`, options),
          ["accounts", "bills", "payments"].includes(view)
            ? api<Summary>(`${endpoint}/summary`, options)
            : Promise.resolve(null),
          view === "bills"
            ? api<Row[]>(`${endpoint}/vendors`, options)
            : Promise.resolve([]),
          view === "accounts"
            ? api<Candidate[]>(`${endpoint}/invoice-candidates`, options)
            : Promise.resolve([]),
        ]);
        if (!controller.signal.aborted) {
          setRows(list);
          setSummary(balances);
          setVendors(suppliers);
          setCandidates(invoices);
        }
      } catch (e) {
        if (!controller.signal.aborted) setError(message(e));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void load();
    return () => controller.abort();
  }, [canWrite, endpoint, revision, view]);

  const closeEditor = useCallback(() => {
    if (!busy) {
      setEditor(null);
      setFormError("");
    }
  }, [busy]);
  const openEditor = (row: Row | null = null) => {
    setEditing(row);
    setFormError("");
    setDirection("received");
    setAllocations([{ key: 0, document_id: "", amount: "" }]);
    setEditor("record");
  };
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const input: Row = Object.fromEntries(form.entries());
    setBusy(true);
    setFormError("");
    try {
      if (editor === "enroll") {
        const id = String(input.invoice_id);
        await api(`${endpoint}/invoice-terms/${encodeURIComponent(id)}`, {
          method: "PUT",
          body: JSON.stringify({
            due_on: input.due_on || null,
            opening_paid: input.opening_paid,
            payments_complete: form.get("payments_complete") === "on",
          }),
        });
      } else {
        if (view === "bills") {
          input.due_on = input.due_on || null;
          input.payments_complete = form.get("payments_complete") === "on";
        }
        if (view === "payments") {
          input.direction = direction;
          input.allocations = allocations.map(({ document_id, amount }) => ({
            document_id,
            amount,
          }));
          if (
            new Set(allocations.map((a) => a.document_id)).size !==
            allocations.length
          )
            throw new Error("Choose each invoice or bill once per payment.");
        }
        const idKey = view === "vendors" ? "vendor_id" : "item_id";
        const suffix = editing
          ? `/${encodeURIComponent(value(editing, idKey))}`
          : "";
        await api(`${endpoint}/${view}${suffix}`, {
          method: editing ? "PUT" : "POST",
          body: JSON.stringify(input),
        });
      }
      setEditor(null);
      setEditing(null);
      setNotice(
        editor === "enroll"
          ? "Opening payment history reviewed. This invoice is now included in receivables."
          : "Record saved. Balances refreshed from the server.",
      );
      setRevision((r) => r + 1);
    } catch (e) {
      setFormError(message(e));
    } finally {
      setBusy(false);
    }
  };

  if (!canWrite)
    return (
      <section className="panel glass">
        <h2>Finance access required</h2>
        <p>
          Vendor and settlement records are available to workspace
          administrators and finance members.
        </p>
      </section>
    );
  const filtered = rows.filter((row) =>
    Object.values(row).some(
      (v) =>
        typeof v !== "object" &&
        String(v ?? "")
          .toLowerCase()
          .includes(query.toLowerCase()),
    ),
  );
  const eligible =
    (direction === "received"
      ? summary?.receivables.rows
      : summary?.payables.rows
    )?.filter((row) => positive(row.outstanding)) || [];
  const emptyTitle =
    view === "vendors"
      ? "Add your first vendor"
      : view === "items"
        ? "Create your price catalogue"
        : view === "bills"
          ? "No vendor bills recorded"
          : "No payments recorded";
  const untracked = candidates.filter((c) => !c.tracked);

  function balanceTable(balance: Balance, name: string) {
    const visible = balance.rows.filter(
      (row) =>
        (status === "all" || row.status === status) &&
        `${row.document_id} ${row.party_id} ${row.party_name}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
    return (
      <section className="panel glass ops-balance-section" aria-label={name}>
        <div className="ops-section-title">
          <h3>{name}</h3>
          <span>{balance.rows.length} tracked records</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Document</th>
                <th>Party</th>
                <th>Due date</th>
                <th>Total</th>
                <th>Paid</th>
                <th>Outstanding</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.document_id}>
                  <td>
                    <button
                      className="ops-text-button"
                      onClick={() =>
                        setDetail({
                          ...row,
                          record_type: name,
                          currency: summary?.currency,
                        })
                      }
                    >
                      {row.document_id}
                    </button>
                  </td>
                  <td>{row.party_name || row.party_id}</td>
                  <td>{row.due_on || "Not supplied"}</td>
                  <td>{money(row.total, summary?.currency || currency)}</td>
                  <td>{money(row.paid, summary?.currency || currency)}</td>
                  <td>
                    {money(row.outstanding, summary?.currency || currency)}
                  </td>
                  <td>
                    <span
                      className={`ops-status ${row.status === "overdue" ? "ops-overdue" : ""}`}
                    >
                      {row.status.replaceAll("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!visible.length && (
          <p className="ops-empty">
            {balance.rows.length
              ? "No records match these filters."
              : "No tracked records. An empty list does not prove there are no business obligations."}
          </p>
        )}
      </section>
    );
  }

  return (
    <div className="view-stack ops-panel" aria-label={headings[view]}>
      <section className="panel glass ops-intro">
        <div>
          <h2>{headings[view]}</h2>
          <p>{explanations[view]}</p>
        </div>
        <div className="ops-actions">
          <button
            className="secondary"
            onClick={() => setRevision((r) => r + 1)}
            disabled={loading || busy}
          >
            <RefreshCw size={15} />
            Refresh
          </button>
          {view === "accounts" ? (
            <button
              className="primary"
              disabled={loading || !untracked.length}
              onClick={() => {
                setFormError("");
                setEditor("enroll");
              }}
            >
              <Plus size={15} />
              Review invoice balance
            </button>
          ) : (
            <button
              className="primary"
              disabled={loading || (view === "bills" && !vendors.length)}
              onClick={() => openEditor()}
            >
              <Plus size={15} />
              {view === "vendors"
                ? "New vendor"
                : view === "items"
                  ? "New item"
                  : view === "bills"
                    ? "New bill"
                    : "Record payment"}
            </button>
          )}
        </div>
      </section>
      {error && (
        <div className="ops-error" role="alert">
          {error}
          <button
            className="secondary"
            onClick={() => setRevision((r) => r + 1)}
          >
            Try again
          </button>
        </div>
      )}
      {notice && (
        <p className="ops-notice" role="status">
          {notice}
        </p>
      )}
      {loading && <p role="status">Loading workspace records…</p>}
      {!loading && !error && (
        <>
          {view === "accounts" && summary && (
            <>
              <div className="ops-metrics">
                <article className="panel glass">
                  <span>
                    <ArrowDownLeft size={17} />
                    Tracked receivables
                  </span>
                  <strong>
                    {money(summary.receivables.total, summary.currency)}
                  </strong>
                  <p>
                    Overdue:{" "}
                    {money(summary.receivables.overdue, summary.currency)}
                  </p>
                  <small>
                    No due date:{" "}
                    {money(summary.receivables.undated, summary.currency)}
                  </small>
                </article>
                <article className="panel glass">
                  <span>
                    <ArrowUpRight size={17} />
                    Tracked payables
                  </span>
                  <strong>
                    {money(summary.payables.total, summary.currency)}
                  </strong>
                  <p>
                    Overdue: {money(summary.payables.overdue, summary.currency)}
                  </p>
                  <small>
                    No due date:{" "}
                    {money(summary.payables.undated, summary.currency)}
                  </small>
                </article>
              </div>
              <div className="ops-guidance">
                <strong>
                  {summary.receivables.untracked_count ?? untracked.length}{" "}
                  invoice records outside balance tracking
                </strong>
                <p>
                  Existing invoices are not assumed unpaid. Review any payments
                  already made before including an invoice in these balances.
                  Reported-sales records are not eligible for receivables. These
                  are recorded obligations, not a profit or bank-balance report.
                </p>
              </div>
            </>
          )}
          <div className="ops-toolbar">
            <label className="ops-search">
              <Search size={16} />
              <span className="sr-only">
                Search {headings[view].toLowerCase()}
              </span>
              <input
                aria-label={`Search ${headings[view].toLowerCase()}`}
                placeholder="Search names or references…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
            {view === "accounts" && (
              <label>
                Status
                <select
                  aria-label="Status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="all">All statuses</option>
                  <option value="current">Current</option>
                  <option value="overdue">Overdue</option>
                  <option value="undated">No due date</option>
                  <option value="paid">Paid</option>
                </select>
              </label>
            )}
          </div>
          {view === "accounts" && summary ? (
            <>
              {balanceTable(summary.receivables, "Customer receivables")}
              {balanceTable(summary.payables, "Vendor payables")}
              <details className="ops-guidance">
                <summary>How to interpret these balances</summary>
                <ul>
                  {summary.limitations.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </details>
            </>
          ) : (
            <section className="panel glass ops-list">
              {!filtered.length ? (
                <div className="ops-empty">
                  <h3>{rows.length ? "No matching records" : emptyTitle}</h3>
                  <p>
                    {rows.length
                      ? "Try a different name or reference."
                      : view === "bills" && !vendors.length
                        ? "Create a vendor in Vendors first, then record the bill against that exact supplier."
                        : view === "payments"
                          ? "Review invoice opening balances or create a vendor bill before allocating payments."
                          : "Records you add here stay within this workspace."}
                  </p>
                </div>
              ) : (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        {view === "vendors" ? (
                          <>
                            <th>Vendor</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Notes</th>
                            <th>Action</th>
                          </>
                        ) : view === "items" ? (
                          <>
                            <th>Item</th>
                            <th>Name</th>
                            <th>Unit price</th>
                            <th>Description</th>
                            <th>Action</th>
                          </>
                        ) : view === "bills" ? (
                          <>
                            <th>Bill</th>
                            <th>Vendor</th>
                            <th>Issued</th>
                            <th>Due</th>
                            <th>Total</th>
                            <th>Outstanding</th>
                          </>
                        ) : (
                          <>
                            <th>Payment</th>
                            <th>Direction</th>
                            <th>Date</th>
                            <th>Amount</th>
                            <th>Reference</th>
                            <th>Status</th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((row) => {
                        const id = value(
                          row,
                          view === "vendors"
                            ? "vendor_id"
                            : view === "items"
                              ? "item_id"
                              : view === "bills"
                                ? "bill_id"
                                : "payment_id",
                        );
                        return (
                          <tr key={id}>
                            <td>
                              <button
                                className="ops-text-button"
                                onClick={() => {
                                  setVoiding(false);
                                  setFormError("");
                                  setDetail(row);
                                }}
                              >
                                {id}
                              </button>
                            </td>
                            {view === "vendors" ? (
                              <>
                                <td>{value(row, "name")}</td>
                                <td>{value(row, "email") || "Not supplied"}</td>
                                <td className="ops-wrap">
                                  {value(row, "notes") || "—"}
                                </td>
                                <td>
                                  <button
                                    className="secondary"
                                    onClick={() => openEditor(row)}
                                  >
                                    Edit
                                  </button>
                                </td>
                              </>
                            ) : view === "items" ? (
                              <>
                                <td>{value(row, "name")}</td>
                                <td>
                                  {money(
                                    value(row, "unit_price"),
                                    value(row, "currency"),
                                  )}
                                </td>
                                <td className="ops-wrap">
                                  {value(row, "description") || "—"}
                                </td>
                                <td>
                                  <button
                                    className="secondary"
                                    onClick={() => openEditor(row)}
                                  >
                                    Edit
                                  </button>
                                </td>
                              </>
                            ) : view === "bills" ? (
                              <>
                                <td>
                                  {(vendors.find(
                                    (v) =>
                                      value(v, "vendor_id") ===
                                      value(row, "vendor_id"),
                                  )?.name as string) || value(row, "vendor_id")}
                                </td>
                                <td>{value(row, "issued_on")}</td>
                                <td>
                                  {value(row, "due_on") || "Not supplied"}
                                </td>
                                <td>
                                  {money(
                                    value(row, "total"),
                                    value(row, "currency"),
                                  )}
                                </td>
                                <td>
                                  {money(
                                    summary?.payables.rows.find(
                                      (b) => b.document_id === id,
                                    )?.outstanding,
                                    value(row, "currency"),
                                  )}
                                </td>
                              </>
                            ) : (
                              <>
                                <td>
                                  <span className="ops-status">
                                    {value(row, "direction") === "received"
                                      ? "Money received"
                                      : "Money paid"}
                                  </span>
                                </td>
                                <td>{value(row, "paid_on")}</td>
                                <td>
                                  {money(
                                    value(row, "amount") ||
                                      value(row, "total") ||
                                      null,
                                    value(row, "currency"),
                                  )}
                                </td>
                                <td>
                                  {value(row, "reference") || "Not supplied"}
                                </td>
                                <td>
                                  <span className="ops-status">
                                    {value(row, "state") || "Unavailable"}
                                  </span>
                                </td>
                              </>
                            )}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="ops-list-foot">
                {filtered.length} shown · {rows.length} loaded records. Open a
                reference to inspect its recorded details.
              </p>
            </section>
          )}
        </>
      )}
      {editor && (
        <Modal
          heading={
            editor === "enroll"
              ? "Review invoice opening balance"
              : editing
                ? `Edit ${view === "vendors" ? "vendor" : "item"}`
                : view === "vendors"
                  ? "New vendor"
                  : view === "items"
                    ? "New item"
                    : view === "bills"
                      ? "New vendor bill"
                      : "Record payment"
          }
          close={closeEditor}
        >
          <form className="modal-body ops-form" onSubmit={submit}>
            {formError && (
              <p className="ops-error" role="alert">
                {formError}
              </p>
            )}
            <fieldset disabled={busy} className="ops-fieldset">
              {editor === "enroll" ? (
                <>
                  <p className="ops-guidance">
                    Only verified invoices are eligible. Enter the amount
                    already paid before tracking starts; later payments must be
                    recorded separately.
                  </p>
                  <label>
                    Invoice
                    <select
                      aria-label="Invoice"
                      name="invoice_id"
                      required
                      defaultValue=""
                    >
                      <option value="" disabled>
                        Choose a verified invoice
                      </option>
                      {untracked.map((c) => (
                        <option key={c.invoice_id} value={c.invoice_id}>
                          {c.invoice_id} · {c.customer_id} ·{" "}
                          {money(c.total, currency)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Already paid before tracking
                    <input
                      name="opening_paid"
                      type="number"
                      min="0"
                      step="0.01"
                      required
                      placeholder="Enter reviewed paid amount"
                    />
                  </label>
                  <label>
                    Due date (optional)
                    <input name="due_on" type="date" />
                  </label>
                  <label className="ops-checkbox">
                    <input name="payments_complete" type="checkbox" required />I
                    reviewed the payment history. The opening paid amount
                    includes all payments before tracking begins.
                  </label>
                </>
              ) : view === "vendors" ? (
                <>
                  <label>
                    Vendor ID
                    <input
                      name="vendor_id"
                      required
                      maxLength={80}
                      pattern="[A-Za-z0-9][A-Za-z0-9._-]*"
                      defaultValue={editing ? value(editing, "vendor_id") : ""}
                      readOnly={!!editing}
                    />
                  </label>
                  <label>
                    Vendor name
                    <input
                      name="name"
                      required
                      maxLength={200}
                      defaultValue={editing ? value(editing, "name") : ""}
                    />
                  </label>
                  <label>
                    Email (optional)
                    <input
                      name="email"
                      type="email"
                      maxLength={254}
                      defaultValue={editing ? value(editing, "email") : ""}
                    />
                  </label>
                  <label>
                    Notes (optional)
                    <textarea
                      name="notes"
                      maxLength={1000}
                      rows={3}
                      defaultValue={editing ? value(editing, "notes") : ""}
                    />
                  </label>
                </>
              ) : view === "items" ? (
                <>
                  <label>
                    Item ID
                    <input
                      name="item_id"
                      required
                      maxLength={80}
                      pattern="[A-Za-z0-9][A-Za-z0-9._-]*"
                      defaultValue={editing ? value(editing, "item_id") : ""}
                      readOnly={!!editing}
                    />
                  </label>
                  <label>
                    Item or service name
                    <input
                      name="name"
                      required
                      maxLength={200}
                      defaultValue={editing ? value(editing, "name") : ""}
                    />
                  </label>
                  <label>
                    Unit price
                    <input
                      name="unit_price"
                      type="number"
                      min="0"
                      step="0.01"
                      required
                      defaultValue={editing ? value(editing, "unit_price") : ""}
                    />
                  </label>
                  <label>
                    Currency
                    <input name="currency" value={currency} readOnly />
                  </label>
                  <label>
                    Description (optional)
                    <textarea
                      name="description"
                      maxLength={1000}
                      rows={3}
                      defaultValue={
                        editing ? value(editing, "description") : ""
                      }
                    />
                  </label>
                  <p className="ops-guidance">
                    This is a catalogue price reference, not an inventory or tax
                    calculation.
                  </p>
                </>
              ) : view === "bills" ? (
                <>
                  <label>
                    Bill ID
                    <input
                      name="bill_id"
                      required
                      maxLength={80}
                      pattern="[A-Za-z0-9][A-Za-z0-9._-]*"
                    />
                  </label>
                  <label>
                    Vendor
                    <select
                      aria-label="Vendor"
                      name="vendor_id"
                      required
                      defaultValue=""
                    >
                      <option value="" disabled>
                        Choose a vendor
                      </option>
                      {vendors.map((v) => (
                        <option
                          key={value(v, "vendor_id")}
                          value={value(v, "vendor_id")}
                        >
                          {value(v, "name")} · {value(v, "vendor_id")}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-grid">
                    <label>
                      Issue date
                      <input
                        name="issued_on"
                        type="date"
                        required
                        defaultValue={localDate()}
                      />
                    </label>
                    <label>
                      Due date (optional)
                      <input name="due_on" type="date" />
                    </label>
                  </div>
                  <div className="form-grid">
                    <label>
                      Total payable
                      <input
                        name="total"
                        type="number"
                        min="0.01"
                        step="0.01"
                        required
                      />
                    </label>
                    <label>
                      Currency
                      <input name="currency" value={currency} readOnly />
                    </label>
                  </div>
                  <label>
                    Already paid before tracking
                    <input
                      name="opening_paid"
                      type="number"
                      min="0"
                      step="0.01"
                      required
                      placeholder="Enter reviewed paid amount"
                    />
                  </label>
                  <label className="ops-checkbox">
                    <input name="payments_complete" type="checkbox" required />I
                    reviewed the payment history. The opening paid amount
                    includes all payments before tracking begins.
                  </label>
                  <label>
                    Description (optional)
                    <textarea name="description" maxLength={1000} rows={3} />
                  </label>
                  <p className="ops-guidance">
                    Record the payable total and reviewed opening paid amount.
                    Enter zero only if no payment has been made. Later payments
                    must be recorded separately. Bills do not automatically
                    become customer-attributed expenses. Saved bills are
                    immutable; verify the reference and amount before saving.
                  </p>
                </>
              ) : (
                <>
                  <label>
                    Payment ID
                    <input
                      name="payment_id"
                      required
                      maxLength={80}
                      pattern="[A-Za-z0-9][A-Za-z0-9._-]*"
                    />
                  </label>
                  <label>
                    Payment direction
                    <select
                      aria-label="Payment direction"
                      value={direction}
                      onChange={(e) => {
                        setDirection(e.target.value as "received" | "made");
                        setAllocations([
                          { key: 0, document_id: "", amount: "" },
                        ]);
                      }}
                    >
                      <option value="received">
                        Money received · customer invoices
                      </option>
                      <option value="made">Money paid · vendor bills</option>
                    </select>
                  </label>
                  <div className="form-grid">
                    <label>
                      Payment date
                      <input
                        name="paid_on"
                        type="date"
                        required
                        defaultValue={localDate()}
                      />
                    </label>
                    <label>
                      Currency
                      <input name="currency" value={currency} readOnly />
                    </label>
                  </div>
                  <label>
                    Bank or payment reference (optional)
                    <input name="reference" maxLength={200} />
                  </label>
                  <div className="ops-allocation-heading">
                    <h3>Allocate this payment</h3>
                    <button
                      type="button"
                      className="secondary"
                      disabled={
                        allocations.length >= eligible.length ||
                        allocations.length >= 50
                      }
                      onClick={() =>
                        setAllocations((a) => [
                          ...a,
                          {
                            key: Math.max(...a.map((x) => x.key)) + 1,
                            document_id: "",
                            amount: "",
                          },
                        ])
                      }
                    >
                      <Plus size={14} />
                      Add allocation
                    </button>
                  </div>
                  {!eligible.length && (
                    <p className="ops-guidance">
                      No outstanding{" "}
                      {direction === "received"
                        ? "tracked invoices. Review invoice balances in Receivables & payables first"
                        : "bills. Create a vendor bill first"}
                      .
                    </p>
                  )}
                  {allocations.map((allocation, index) => (
                    <div className="ops-allocation" key={allocation.key}>
                      <label>
                        {direction === "received" ? "Invoice" : "Bill"}{" "}
                        {index + 1}
                        <select
                          aria-label={`${direction === "received" ? "Invoice" : "Bill"} ${index + 1}`}
                          required
                          value={allocation.document_id}
                          onChange={(e) =>
                            setAllocations((a) =>
                              a.map((x) =>
                                x.key === allocation.key
                                  ? {
                                      ...x,
                                      document_id: e.target.value,
                                      amount: "",
                                    }
                                  : x,
                              ),
                            )
                          }
                        >
                          <option value="">Choose a document</option>
                          {eligible
                            .filter(
                              (row) =>
                                row.document_id === allocation.document_id ||
                                !allocations.some(
                                  (a) => a.document_id === row.document_id,
                                ),
                            )
                            .map((row) => (
                              <option
                                key={row.document_id}
                                value={row.document_id}
                              >
                                {row.document_id} ·{" "}
                                {row.party_name || row.party_id} · outstanding{" "}
                                {money(row.outstanding, currency)}
                              </option>
                            ))}
                        </select>
                      </label>
                      <label>
                        Allocated amount {index + 1}
                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          required
                          max={
                            eligible.find(
                              (r) => r.document_id === allocation.document_id,
                            )?.outstanding
                          }
                          value={allocation.amount}
                          onChange={(e) =>
                            setAllocations((a) =>
                              a.map((x) =>
                                x.key === allocation.key
                                  ? { ...x, amount: e.target.value }
                                  : x,
                              ),
                            )
                          }
                        />
                      </label>
                      <button
                        type="button"
                        className="icon-btn"
                        aria-label={`Remove allocation ${index + 1}`}
                        disabled={allocations.length === 1}
                        onClick={() =>
                          setAllocations((a) =>
                            a.filter((x) => x.key !== allocation.key),
                          )
                        }
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                  <p className="ops-guidance">
                    Allocate one payment to documents for the same customer or
                    vendor. The server sums the allocations and rejects
                    overpayments. These are manually recorded settlements, not
                    verified bank-feed transactions. Saved amounts cannot be
                    edited; an incorrect recorded payment can be voided with an
                    audit reason.
                  </p>
                </>
              )}
              <div className="ops-form-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={closeEditor}
                >
                  Cancel
                </button>
                <button
                  className="primary"
                  disabled={view === "payments" && !eligible.length}
                >
                  {busy
                    ? "Saving…"
                    : editor === "enroll"
                      ? "Confirm reviewed balance"
                      : "Save record"}
                </button>
              </div>
            </fieldset>
          </form>
        </Modal>
      )}
      {detail && (
        <Modal
          heading="Recorded details"
          close={() => {
            if (!busy) {
              setDetail(null);
              setVoiding(false);
              setFormError("");
            }
          }}
        >
          <div className="modal-body">
            <p className="ops-guidance">
              Workspace record as stored. Payment allocations use exact document
              IDs; no name-based matching is performed.
            </p>
            <dl className="ops-details">
              {Object.entries(detail)
                .filter(([key]) => key !== "organization_id")
                .map(([key, val]) => (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>
                      {val == null || val === "" ? (
                        "Not supplied"
                      ) : typeof val === "object" ? (
                        <pre>{JSON.stringify(val, null, 2)}</pre>
                      ) : (
                        String(val)
                      )}
                    </dd>
                  </div>
                ))}
            </dl>
            {view === "payments" &&
              value(detail, "state") === "active" &&
              (voiding ? (
                <form
                  className="ops-form"
                  onSubmit={async (event) => {
                    event.preventDefault();
                    const reason = String(
                      new FormData(event.currentTarget).get("reason") || "",
                    ).trim();
                    setBusy(true);
                    setFormError("");
                    try {
                      await api(
                        `${endpoint}/payments/${encodeURIComponent(value(detail, "payment_id"))}/void`,
                        { method: "POST", body: JSON.stringify({ reason }) },
                      );
                      setDetail(null);
                      setVoiding(false);
                      setNotice(
                        "Recorded payment voided. Its history is retained and outstanding balances have been restored. No money was moved.",
                      );
                      setRevision((r) => r + 1);
                    } catch (e) {
                      setFormError(message(e));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  <fieldset className="ops-fieldset" disabled={busy}>
                    <p className="ops-guidance">
                      This corrects the recorded settlement and restores its
                      outstanding allocations. The original payment remains in
                      audit history. It does not cancel a bank transfer or issue
                      a refund.
                    </p>
                    {formError && (
                      <p className="ops-error" role="alert">
                        {formError}
                      </p>
                    )}
                    <label>
                      Reason for voiding
                      <textarea
                        name="reason"
                        required
                        minLength={1}
                        maxLength={1000}
                        rows={3}
                      />
                    </label>
                    <label className="ops-checkbox">
                      <input type="checkbox" required />I confirm this recorded
                      payment should no longer reduce outstanding balances.
                    </label>
                    <div className="ops-form-actions">
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => setVoiding(false)}
                      >
                        Keep payment
                      </button>
                      <button className="primary">
                        {busy ? "Voiding…" : "Confirm void"}
                      </button>
                    </div>
                  </fieldset>
                </form>
              ) : (
                <button
                  className="secondary"
                  onClick={() => {
                    setFormError("");
                    setVoiding(true);
                  }}
                >
                  Void recorded payment
                </button>
              ))}
          </div>
        </Modal>
      )}
    </div>
  );
}
