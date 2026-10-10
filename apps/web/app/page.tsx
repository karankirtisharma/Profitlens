"use client";
import { useCallback, useEffect, useRef, useState, FormEvent } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  LayoutDashboard,
  LogOut,
  Plus,
  RefreshCw,
  ShieldCheck,
  Upload,
  Users,
  Search,
} from "lucide-react";

import {
  Account,
  RecordData,
  Contract,
  Batch,
  Member,
  Kind,
  View,
  fields,
  labels,
  title,
  message,
  details,
  api,
} from "../lib/workspace";
import { Logo, Modal } from "../components/ui";
import { Login } from "../components/login";
import { Overview, OverviewData } from "../components/overview";
import { PageTransition, ReplayIntro } from "../components/experience";

export default function Home() {
  const [account, setAccount] = useState<Account | null>(null),
    [org, setOrg] = useState(""),
    [boot, setBoot] = useState(true),
    [view, setView] = useState<View>("overview");
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState<RecordData[]>([]),
    [rows, setRows] = useState<RecordData[]>([]),
    [contracts, setContracts] = useState<Contract[]>([]),
    [batches, setBatches] = useState<Batch[]>([]),
    [members, setMembers] = useState<Member[]>([]);
  const [selected, setSelected] = useState<RecordData | null>(null),
    [editing, setEditing] = useState(false),
    [contract, setContract] = useState<Contract | null>(null),
    [preview, setPreview] = useState<Batch | null>(null);
  const [kind, setKind] = useState<Kind>("customers"),
    [query, setQuery] = useState(""),
    [offset, setOffset] = useState(0),
    [customerFilter, setCustomerFilter] = useState("");
  const workspace = account?.workspaces.find((w) => w.id === org),
    canWrite = ["admin", "finance"].includes(workspace?.role || ""),
    isAdmin = workspace?.role === "admin";
  const [overviewData, setOverviewData] = useState<OverviewData>({
    invoices: [],
    expenses: [],
    contracts: [],
  });
  const base = `/workspaces/${encodeURIComponent(org)}`;
  const currentRequest = useRef<AbortController | null>(null);
  const refresh = useCallback(async () => {
    if (!org) return;
    currentRequest.current?.abort();
    const controller = new AbortController();
    currentRequest.current = controller;
    const options = { signal: controller.signal };
    setLoading(true);
    setError("");
    try {
      const list = await api<RecordData[]>(
        `${base}/records/customers`,
        options,
      );
      setCustomers(list);
      if (view === "overview") {
        const [invoices, expenses, contractList] = await Promise.all([
          api<RecordData[]>(`${base}/records/invoices?limit=200`, options),
          api<RecordData[]>(`${base}/records/expenses?limit=200`, options),
          api<Contract[]>(`${base}/contracts`, options),
        ]);
        setOverviewData({ invoices, expenses, contracts: contractList });
      }
      if (["customers", "invoices", "expenses"].includes(view))
        setRows(
          await api<RecordData[]>(
            `${base}/records/${view}?limit=200&offset=${offset}${customerFilter ? `&customer_id=${encodeURIComponent(customerFilter)}` : ""}`,
            options,
          ),
        );
      if (view === "contracts")
        setContracts(
          await api<Contract[]>(
            `${base}/contracts${customerFilter ? `?customer_id=${encodeURIComponent(customerFilter)}` : ""}`,
            options,
          ),
        );
      if (view === "imports" && canWrite)
        setBatches(await api<Batch[]>(`${base}/imports`, options));
      if (view === "team" && isAdmin)
        setMembers(await api<Member[]>(`${base}/members`, options));
    } catch (e) {
      if (!controller.signal.aborted) setError(message(e));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [org, base, view, offset, customerFilter, canWrite, isAdmin]);
  useEffect(() => {
    api<Account>("/auth/me")
      .then((a) => {
        setAccount(a);
        setOrg(a.workspaces[0]?.id || "");
      })
      .catch(() => {})
      .finally(() => setBoot(false));
  }, []);
  useEffect(() => {
    if (account) {
      document
        .getElementById("workspace-title")
        ?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }, [account]);
  useEffect(() => {
    // Refresh synchronizes the view with an external API; loading mirrors that request.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
    return () => currentRequest.current?.abort();
  }, [refresh]);
  const changeView = (v: View) => {
    setView(v);
    setRows([]);
    setOverviewData({ invoices: [], expenses: [], contracts: [] });
    setQuery("");
    setCustomerFilter("");
    setOffset(0);
    setNotice("");
    setError("");
    setPreview(null);
  };
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await action(async () => {
      await api("/auth/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(data)),
      });
      const a = await api<Account>("/auth/me");
      setAccount(a);
      setOrg(a.workspaces[0]?.id || "");
    });
  }
  async function logout() {
    await action(async () => {
      await api("/auth/logout", { method: "POST" });
      setAccount(null);
      setOrg("");
      setCustomers([]);
      setRows([]);
      setContracts([]);
      setBatches([]);
      setMembers([]);
      setSelected(null);
      setContract(null);
      setEditing(false);
      changeView("overview");
    });
  }
  const money = (value: unknown) =>
    `${workspace?.currency || "INR"} ${Number(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const customerName = (id: string) =>
    customers.find((c) => c.customer_id === id)?.name || id;
  const recordKind = (
    ["customers", "invoices", "expenses"].includes(view) ? view : "customers"
  ) as Kind;
  const displayed = rows.filter((r) =>
    Object.values(r).some(
      (v) =>
        typeof v !== "object" &&
        String(v).toLowerCase().includes(query.toLowerCase()),
    ),
  );
  if (boot)
    return (
      <main className="boot">
        <Logo />
        <p>Opening your workspace…</p>
      </main>
    );
  if (!account) return <Login login={login} busy={busy} error={error} />;
  const nav: { id: View; label: string; icon: typeof Users }[] = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "customers", label: "Customers", icon: Users },
    { id: "invoices", label: "Invoices", icon: FileSpreadsheet },
    { id: "expenses", label: "Expenses", icon: FileText },
    { id: "contracts", label: "Contracts", icon: FileCheck2 },
    ...(canWrite
      ? [{ id: "imports" as View, label: "Imports", icon: Upload }]
      : []),
    ...(isAdmin
      ? [{ id: "team" as View, label: "Team access", icon: ShieldCheck }]
      : []),
  ];
  return (
    <div className="shell">
      <a href="#main-content" className="skip-link">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <Logo />
        <div className="workspace-picker">
          <label htmlFor="workspace">Workspace</label>
          <select
            id="workspace"
            value={org}
            onChange={(e) => {
              setOrg(e.target.value);
              setCustomers([]);
              setContracts([]);
              setBatches([]);
              setMembers([]);
              changeView("overview");
            }}
          >
            {account.workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>
        <span className="nav-label">Business workspace</span>
        <nav>
          {nav.map((n) => (
            <button
              key={n.id}
              className={view === n.id ? "active" : ""}
              onClick={() => {
                if (view !== n.id) changeView(n.id);
              }}
              aria-current={view === n.id ? "page" : undefined}
            >
              <n.icon size={19} />
              {n.label}
              {view === n.id && <span className="active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <ShieldCheck size={20} />
          <strong>Access stays scoped</strong>
          <p>
            {canWrite
              ? "Manage records in your organization."
              : "Only your assigned customers are visible."}
          </p>
        </div>
        <div className="account">
          <span className="avatar">{account.name.slice(0, 1)}</span>
          <div>
            <strong>{account.name}</strong>
            <span>{title(workspace?.role || "member")}</span>
          </div>
          <button
            className="icon-btn"
            onClick={logout}
            aria-label="Sign out"
            disabled={busy}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="main-wrap">
        <header className="topbar">
          <span>
            Workspace <ChevronRight size={14} /> <strong>{title(view)}</strong>
          </span>
          <div className="topbar-actions">
            <ReplayIntro />
            <span className="status-dot">
              {["demo-org", "other-org"].includes(org)
                ? "Synthetic demo data"
                : "Organization data"}
            </span>
          </div>
        </header>
        <main className="content" id="main-content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                {workspace?.name || "Your workspace"}
              </span>
              <h1 id="workspace-title" tabIndex={-1}>
                {view === "overview"
                  ? "Business data, connected."
                  : view === "team"
                    ? "Team access"
                    : title(view)}
              </h1>
              <p className="muted">
                {
                  {
                    overview:
                      "A trusted starting point for your customer profitability investigations.",
                    customers:
                      "Keep customer identities consistent across every source.",
                    invoices:
                      "Review billed amounts and their original source records.",
                    expenses:
                      "Organize attributed costs by customer and billing month.",
                    contracts:
                      "Store private documents and verify their pricing terms.",
                    imports:
                      "Validate first. Review the preview. Then commit your records.",
                    team: "Manage which customers your analysts can access.",
                  }[view]
                }
              </p>
            </div>
            <button
              className="secondary"
              onClick={refresh}
              disabled={loading || busy}
              aria-label="Refresh data"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="alert success" role="status">
              <Check size={17} />
              {notice}
            </div>
          )}
          {!org && (
            <div className="empty">
              No workspace membership. Ask your administrator to provision
              access.
            </div>
          )}
          {loading ? (
            <div className="loading" role="status">
              <div className="skeleton" />
              <div className="skeleton" />
              <p>Loading workspace records…</p>
            </div>
          ) : (
            <PageTransition identity={`${org}:${view}`}>
              {view === "overview" && org && !error && (
                <Overview
                  customers={customers}
                  data={overviewData}
                  canWrite={canWrite}
                  changeView={changeView}
                />
              )}
              {["customers", "invoices", "expenses"].includes(view) && (
                <section className="panel">
                  <div className="table-toolbar">
                    <div className="search">
                      <Search size={17} />
                      <input
                        aria-label="Search loaded records"
                        placeholder={`Search ${view} on this page…`}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </div>
                    {view !== "customers" && (
                      <select
                        aria-label="Filter by customer"
                        value={customerFilter}
                        onChange={(e) => {
                          setCustomerFilter(e.target.value);
                          setOffset(0);
                        }}
                      >
                        <option value="">All customers</option>
                        {customers.map((c) => (
                          <option value={c.customer_id} key={c.customer_id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    )}
                    {canWrite && (
                      <button
                        className="primary"
                        onClick={() => {
                          setSelected(null);
                          setEditing(true);
                        }}
                      >
                        <Plus size={17} />
                        Add{" "}
                        {view === "customers"
                          ? "customer"
                          : view === "invoices"
                            ? "invoice"
                            : "expense"}
                      </button>
                    )}
                  </div>
                  {displayed.length === 0 ? (
                    <div className="empty">
                      <FileSpreadsheet size={32} />
                      <h3>No {view} to show</h3>
                      <p>
                        {query || customerFilter
                          ? "Try another filter."
                          : canWrite
                            ? "Create a record or confirm a CSV import to get started."
                            : "No records are available for your assigned customers."}
                      </p>
                    </div>
                  ) : (
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>
                              {view === "customers" ? "Customer" : "Record"}
                            </th>
                            <th>
                              {view === "customers" ? "Industry" : "Customer"}
                            </th>
                            <th>
                              {view === "customers"
                                ? "Source"
                                : "Billing month"}
                            </th>
                            <th>{view === "customers" ? "Open" : "Amount"}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {displayed.map((r) => {
                            const id = String(r[fields[recordKind][0]]);
                            return (
                              <tr key={id}>
                                <td>
                                  <button
                                    className="record-link"
                                    onClick={() => {
                                      setSelected(r);
                                      setEditing(true);
                                    }}
                                  >
                                    {view === "customers" ? r.name : id}
                                  </button>
                                  <small>
                                    {view === "customers"
                                      ? id
                                      : r.source?.type === "csv"
                                        ? `${r.source.filename} · row ${r.source.row}`
                                        : "Manual record"}
                                  </small>
                                </td>
                                <td>
                                  {view === "customers"
                                    ? String(r.industry || "—")
                                    : customerName(r.customer_id)}
                                </td>
                                <td>
                                  {view === "customers" ? (
                                    <span className="tag">
                                      {r.source?.type || "manual"}
                                    </span>
                                  ) : (
                                    String(r.billing_period)
                                  )}
                                </td>
                                <td>
                                  {view === "customers" ? (
                                    <button
                                      className="icon-btn"
                                      aria-label={`View ${r.name}`}
                                      onClick={() => {
                                        setSelected(r);
                                        setEditing(true);
                                      }}
                                    >
                                      <ArrowRight size={17} />
                                    </button>
                                  ) : (
                                    money(r.total ?? r.amount)
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <div className="table-footer">
                    <span>
                      {rows.length} records loaded · Page{" "}
                      {Math.floor(offset / 200) + 1}
                    </span>
                    <div>
                      <button
                        className="icon-btn"
                        aria-label="Previous page"
                        disabled={offset === 0}
                        onClick={() => setOffset(Math.max(0, offset - 200))}
                      >
                        <ChevronLeft size={17} />
                      </button>
                      <button
                        className="icon-btn"
                        aria-label="Next page"
                        disabled={rows.length < 200}
                        onClick={() => setOffset(offset + 200)}
                      >
                        <ChevronRight size={17} />
                      </button>
                    </div>
                  </div>
                </section>
              )}
              {view === "imports" && canWrite && (
                <>
                  <section className="panel import-panel">
                    <div className="section-heading">
                      <div>
                        <h2>New CSV import</h2>
                        <p className="muted">
                          Import customers first, then invoices and expenses.
                          Maximum 5 MiB / 10,000 rows.
                        </p>
                      </div>
                      <Upload size={26} />
                    </div>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const form = new FormData(e.currentTarget);
                        void action(async () => {
                          const p = await api<Batch>(
                            `${base}/imports/${kind}/preview`,
                            { method: "POST", body: form },
                          );
                          setPreview(p);
                          await refresh();
                        });
                      }}
                    >
                      <div className="form-grid">
                        <label>
                          Record type
                          <select
                            value={kind}
                            onChange={(e) => {
                              setKind(e.target.value as Kind);
                              setPreview(null);
                            }}
                          >
                            {["customers", "invoices", "expenses"].map((k) => (
                              <option key={k}>{k}</option>
                            ))}
                          </select>
                        </label>
                        <label>
                          CSV file
                          <input
                            name="file"
                            type="file"
                            accept=".csv,text/csv"
                            required
                          />
                        </label>
                      </div>
                      <p className="format-hint">
                        Required columns: <code>{fields[kind].join(", ")}</code>
                      </p>
                      <button className="primary" disabled={busy}>
                        <Search size={16} />
                        {busy ? "Validating…" : "Preview import"}
                      </button>
                    </form>
                  </section>
                  {preview && (
                    <section className="panel import-panel">
                      <div className="section-heading">
                        <h2>Preview: {preview.filename}</h2>
                        <span className={`tag ${preview.state}`}>
                          {preview.state}
                        </span>
                      </div>
                      <p>
                        {preview.row_count} valid parsed rows ·{" "}
                        {preview.issues.length} issues
                      </p>
                      {preview.issues.length > 0 && (
                        <div className="alert error">
                          {preview.issues.map((i, n) => (
                            <p key={n}>
                              {i.source_row ? `Row ${i.source_row}: ` : ""}
                              {details(i.message)}
                            </p>
                          ))}
                        </div>
                      )}
                      {preview.preview_rows.length > 0 && (
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>Source row</th>
                                {fields[preview.kind as Kind].map((f) => (
                                  <th key={f}>{labels[f]}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {preview.preview_rows.map((r) => (
                                <tr key={r.source_row}>
                                  <td>{r.source_row}</td>
                                  {fields[preview.kind as Kind].map((f) => (
                                    <td key={f}>{r.data[f]}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <p className="footnote">
                            Showing the first 10 parsed rows. Confirmation
                            checks every row again.
                          </p>
                        </div>
                      )}
                      {preview.state === "ready" && (
                        <button
                          className="primary"
                          disabled={busy}
                          onClick={() =>
                            void action(async () => {
                              const p = await api<Batch>(
                                `${base}/imports/${preview.id}/confirm`,
                                { method: "POST" },
                              );
                              setPreview(p);
                              await refresh();
                              setNotice(
                                `Import confirmed: ${p.result.inserted} inserted, ${p.result.skipped} identical records skipped.`,
                              );
                            })
                          }
                        >
                          <Check size={16} />
                          Confirm import
                        </button>
                      )}
                      {preview.state === "confirmed" && (
                        <p className="alert success">
                          Saved: {preview.result.inserted} inserted ·{" "}
                          {preview.result.skipped} skipped. Repeating this
                          import will not duplicate records.
                        </p>
                      )}
                    </section>
                  )}
                  <section className="panel">
                    <div className="panel-title">
                      <h2>Import history</h2>
                      <span className="muted">Latest 100 imports</span>
                    </div>
                    {batches.length === 0 ? (
                      <div className="empty">No imports yet.</div>
                    ) : (
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Source file</th>
                              <th>Records</th>
                              <th>Status</th>
                              <th>Result</th>
                            </tr>
                          </thead>
                          <tbody>
                            {batches.map((b) => (
                              <tr key={b.id}>
                                <td>
                                  <button
                                    className="record-link"
                                    onClick={() => setPreview(b)}
                                  >
                                    {b.filename}
                                  </button>
                                  <small>{b.kind}</small>
                                </td>
                                <td>{b.row_count}</td>
                                <td>
                                  <span className={`tag ${b.state}`}>
                                    {b.state}
                                  </span>
                                </td>
                                <td>
                                  {b.state === "confirmed"
                                    ? `${b.result.inserted} saved / ${b.result.skipped} skipped`
                                    : `${b.issues.length} issues`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </>
              )}
              {view === "contracts" && (
                <>
                  {canWrite && (
                    <section className="panel import-panel">
                      <h2>Upload a contract</h2>
                      <p className="muted">
                        Text-based PDF · Maximum 10 MiB / 100 pages · Terms
                        require human review.
                      </p>
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          const element = e.currentTarget;
                          const form = new FormData(element);
                          void action(async () => {
                            const c = await api<Contract>(`${base}/contracts`, {
                              method: "POST",
                              body: form,
                            });
                            setContract(c);
                            element.reset();
                            await refresh();
                            setNotice(
                              "Contract stored privately. Review its monthly terms.",
                            );
                          });
                        }}
                      >
                        <div className="form-grid">
                          <label>
                            Customer
                            <select name="customer_id" required defaultValue="">
                              <option value="" disabled>
                                Select a customer
                              </option>
                              {customers.map((c) => (
                                <option
                                  key={c.customer_id}
                                  value={c.customer_id}
                                >
                                  {c.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            Contract PDF
                            <input
                              name="file"
                              type="file"
                              accept=".pdf,application/pdf"
                              required
                            />
                          </label>
                        </div>
                        <button
                          className="primary"
                          disabled={busy || !customers.length}
                        >
                          <Upload size={16} />
                          Upload contract
                        </button>
                      </form>
                    </section>
                  )}
                  <section className="panel">
                    <div className="panel-title">
                      <h2>Contract library</h2>
                      <span className="muted">Latest 200 documents</span>
                    </div>
                    {contracts.length === 0 ? (
                      <div className="empty">
                        <FileCheck2 size={32} />
                        <h3>No contracts yet</h3>
                        <p>
                          Uploaded contracts will appear here with their review
                          status.
                        </p>
                      </div>
                    ) : (
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Document</th>
                              <th>Customer</th>
                              <th>Review status</th>
                              <th>Monthly rate</th>
                            </tr>
                          </thead>
                          <tbody>
                            {contracts.map((c) => (
                              <tr key={c.id}>
                                <td>
                                  <button
                                    className="record-link"
                                    onClick={() => setContract(c)}
                                  >
                                    {c.filename}
                                  </button>
                                  <small>
                                    {c.pages.length} pages with text
                                  </small>
                                </td>
                                <td>{customerName(c.customer_id)}</td>
                                <td>
                                  <span className={`tag ${c.state}`}>
                                    {c.state}
                                  </span>
                                </td>
                                <td>
                                  {c.state === "reviewed"
                                    ? money(c.monthly_rate)
                                    : "Awaiting review"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </section>
                </>
              )}
              {view === "team" && isAdmin && (
                <section className="panel">
                  <div className="panel-title">
                    <h2>Workspace members</h2>
                    <span className="muted">Preset roles</span>
                  </div>
                  <p className="access-note">
                    Admins manage access. Finance members manage all workspace
                    records. Analysts can read only assigned customers. Account
                    provisioning is handled by the administrator CLI.
                  </p>
                  {members.map((m) => (
                    <div className="member" key={m.id}>
                      <div>
                        <strong>{m.name}</strong>
                        <p className="muted">{m.email}</p>
                        <span className="tag">{m.role}</span>
                      </div>
                      {m.role === "analyst" ? (
                        <form
                          onSubmit={(e) => {
                            e.preventDefault();
                            const data = new FormData(e.currentTarget);
                            void action(async () => {
                              await api(`${base}/members/${m.id}/customers`, {
                                method: "PUT",
                                body: JSON.stringify({
                                  customer_ids: data.getAll("customers"),
                                }),
                              });
                              await refresh();
                              setNotice(
                                "Customer assignments saved. Access changes apply immediately.",
                              );
                            });
                          }}
                        >
                          <fieldset>
                            <legend>Assigned customers</legend>
                            {customers.map((c) => (
                              <label
                                className="check-label"
                                key={c.customer_id}
                              >
                                <input
                                  type="checkbox"
                                  name="customers"
                                  value={c.customer_id}
                                  defaultChecked={m.customer_ids.includes(
                                    c.customer_id,
                                  )}
                                />
                                {c.name}
                              </label>
                            ))}
                          </fieldset>
                          <button className="secondary" disabled={busy}>
                            Save assignments
                          </button>
                        </form>
                      ) : (
                        <p className="muted">All organization customers</p>
                      )}
                    </div>
                  ))}
                </section>
              )}
            </PageTransition>
          )}
          <footer className="page-footer">
            <Logo />
            <span>
              Week 3 · Business data foundation · {workspace?.currency || "INR"}
            </span>
          </footer>
        </main>
      </div>
      {editing && (
        <Modal
          heading={`${selected ? (canWrite ? "Edit" : "View") : "Add"} ${recordKind.slice(0, -1)}`}
          close={() => {
            setEditing(false);
            setError("");
          }}
        >
          <form
            className="modal-body"
            onSubmit={(e) => {
              e.preventDefault();
              const values = Object.fromEntries(new FormData(e.currentTarget));
              const id = selected?.[fields[recordKind][0]];
              void action(async () => {
                await api(
                  `${base}/records/${recordKind}${id ? `/${encodeURIComponent(String(id))}` : ""}`,
                  { method: id ? "PUT" : "POST", body: JSON.stringify(values) },
                );
                setEditing(false);
                await refresh();
                setNotice("Record saved.");
              });
            }}
          >
            <div className="form-grid">
              {fields[recordKind].map((f) => (
                <label key={f}>
                  {labels[f]}
                  {f === "customer_id" && recordKind !== "customers" ? (
                    <select
                      name={f}
                      defaultValue={String(selected?.[f] || "")}
                      required
                      disabled={!canWrite}
                    >
                      <option value="" disabled>
                        Select a customer
                      </option>
                      {customers.map((c) => (
                        <option key={c.customer_id} value={c.customer_id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      name={f}
                      defaultValue={String(
                        selected?.[f] ??
                          (f === "currency"
                            ? workspace?.currency
                            : ["discount", "tax", "refund"].includes(f)
                              ? "0"
                              : ""),
                      )}
                      type={
                        f === "billing_period"
                          ? "month"
                          : [
                                "subtotal",
                                "discount",
                                "tax",
                                "refund",
                                "total",
                                "amount",
                              ].includes(f)
                            ? "number"
                            : "text"
                      }
                      min={0}
                      step="0.01"
                      required={f !== "industry"}
                      readOnly={
                        !canWrite ||
                        (!!selected && f === fields[recordKind][0]) ||
                        f === "currency"
                      }
                      maxLength={200}
                    />
                  )}
                </label>
              ))}
            </div>
            {recordKind === "invoices" && (
              <p className="footnote">
                Total = subtotal − discount + tax − refund. Use same-period,
                pre-tax refunds.
              </p>
            )}
            {selected?.source && (
              <div className="source-box">
                <strong>Original source</strong>
                <p>
                  {selected.source.type === "csv"
                    ? `${selected.source.filename} · Row ${selected.source.row}`
                    : "Manually created record"}
                </p>
                {selected.source.batch_id && (
                  <small>Import {selected.source.batch_id}</small>
                )}
                <p className="footnote">
                  Edits retain the original source and create an audit event.
                </p>
              </div>
            )}
            {selected && recordKind === "customers" && (
              <div className="button-row">
                {(["invoices", "expenses", "contracts"] as View[]).map((v) => (
                  <button
                    type="button"
                    className="secondary"
                    key={v}
                    onClick={() => {
                      setEditing(false);
                      changeView(v);
                      setCustomerFilter(selected.customer_id);
                    }}
                  >
                    View {v}
                  </button>
                ))}
              </div>
            )}
            {error && (
              <p role="alert" className="alert error">
                {error}
              </p>
            )}
            {canWrite && (
              <button className="primary" disabled={busy}>
                {busy ? "Saving…" : "Save record"}
              </button>
            )}
          </form>
        </Modal>
      )}
      {contract && (
        <Modal
          heading="Review contract"
          close={() => {
            setContract(null);
            setError("");
          }}
        >
          <div className="modal-body">
            <div className="contract-summary">
              <div>
                <strong>{contract.filename}</strong>
                <p className="muted">
                  {customerName(contract.customer_id)} ·{" "}
                  <span className={`tag ${contract.state}`}>
                    {contract.state}
                  </span>
                </p>
              </div>
              <a
                className="secondary"
                href={`/api${base}/contracts/${contract.id}/file`}
              >
                <ArrowDownToLine size={16} />
                Download PDF
              </a>
            </div>
            <details className="source-box" open>
              <summary>Extracted evidence · verify against the PDF</summary>
              {contract.pages.map((p) => (
                <div className="pdf-page" key={p.page}>
                  <strong>Page {p.page}</strong>
                  <pre>{p.text}</pre>
                </div>
              ))}
            </details>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const values = Object.fromEntries(
                  new FormData(e.currentTarget),
                );
                void action(async () => {
                  const c = await api<Contract>(
                    `${base}/contracts/${contract.id}/terms`,
                    { method: "PUT", body: JSON.stringify(values) },
                  );
                  setContract(c);
                  await refresh();
                  setNotice("Contract terms reviewed and saved.");
                });
              }}
            >
              <h3>Fixed monthly terms</h3>
              <p className="footnote">
                Amounts are before tax. Confirm these values against the source
                document. Only one reviewed contract may cover a customer on a
                given date.
              </p>
              <div className="form-grid">
                {[
                  {
                    key: "effective_from",
                    label: "Effective from",
                    type: "date",
                  },
                  { key: "effective_to", label: "Effective to", type: "date" },
                  {
                    key: "monthly_rate",
                    label: "Monthly rate",
                    type: "number",
                  },
                  {
                    key: "monthly_discount",
                    label: "Monthly discount",
                    type: "number",
                  },
                  { key: "source_page", label: "Source page", type: "number" },
                  { key: "currency", label: "Currency", type: "text" },
                ].map((f) => (
                  <label
                    key={`${contract.id}-${contract.reviewed_at}-${f.key}`}
                  >
                    {f.label}
                    <input
                      name={f.key}
                      type={f.type}
                      required
                      min={f.key === "source_page" ? 1 : 0}
                      step={f.key === "source_page" ? 1 : "0.01"}
                      readOnly={!canWrite || f.key === "currency"}
                      defaultValue={String(
                        contract[f.key as keyof Contract] ??
                          (f.key === "currency"
                            ? workspace?.currency
                            : f.key === "monthly_discount"
                              ? "0"
                              : f.key === "source_page"
                                ? "1"
                                : ""),
                      )}
                    />
                  </label>
                ))}
              </div>
              {error && (
                <p role="alert" className="alert error">
                  {error}
                </p>
              )}
              {canWrite && (
                <button className="primary" disabled={busy}>
                  <Check size={16} />
                  Confirm reviewed terms
                </button>
              )}
            </form>
          </div>
        </Modal>
      )}
    </div>
  );
}
