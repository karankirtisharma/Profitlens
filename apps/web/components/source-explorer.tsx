"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, message } from "../lib/workspace";
import { Modal } from "./ui";
import { MonthlyReview } from "./monthly-review";
import {
  SourceEvidenceBody,
  type SourceEvidenceDetail,
} from "./source-evidence";

type Doc = {
  id: string;
  filename: string;
  state: string;
  headers: string[];
  sha256: string;
  pages: { page: number; text: string }[];
};
type Fact = {
  id: string;
  document_id: string;
  row_number: number;
  kind: string;
  amount: string;
  currency: string;
  occurred_on: string | null;
  description: string;
  counterparty: string;
  customer_id: string | null;
};
type Report = {
  months: {
    month: string;
    kind: string;
    currency: string;
    amount: string;
    count: number;
  }[];
  rows: Fact[];
  groups: {
    kind: string;
    currency: string;
    amount: string | null;
    count: number;
  }[];
  total: number;
  unmatched: number;
  notice: string;
};
type MapConfig = {
  kind: string;
  columns: Record<string, string>;
  currency: string;
  date_format: string;
  decimal_format: string;
  amount_mode: string;
  namespace: string;
  profile_name: string;
};
type Preview = {
  rows: Record<string, unknown>[];
  issues: { row?: number; message: string }[];
  row_count: number;
  preview_token: string;
  unmapped_columns: string[];
  notice: string;
};
const kinds = [
  "reported_sales",
  "expenditure",
  "cash_inflow",
  "cash_outflow",
  "commitment",
  "asset_balance",
  "liability_balance",
];
const label = (s: string) => s.replaceAll("_", " ");
const kindHelp: Record<string, string> = {
  reported_sales:
    "Amounts reported as sales. Tax basis and delivery costs are not assumed.",
  expenditure:
    "Spending recorded by this source, including signed credits. It is not automatically a customer cost.",
  cash_inflow:
    "Money received into an account. It may include loans or transfers, not only revenue.",
  cash_outflow:
    "Money paid from an account. It may include asset purchases or transfers, not only expenses.",
  commitment: "A promised or approved amount, not proof of payment or expense.",
  asset_balance:
    "An asset value at a point in time. Snapshots are not added together.",
  liability_balance:
    "An amount owed at a point in time. Snapshots are not added together.",
};
const columnLabel = (target: string) =>
  target === "credit"
    ? "Money received (bank credit)"
    : target === "debit"
      ? "Money paid (bank debit)"
      : label(target);
type Suggestion = {
  column: string;
  confidence?: string;
  candidates?: string[];
};
function SampleTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{label(column)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((column) => (
                <td
                  key={column}
                  style={{
                    maxWidth: 280,
                    overflowWrap: "anywhere",
                    whiteSpace: "normal",
                  }}
                >
                  {row[column] === null ||
                  row[column] === undefined ||
                  row[column] === ""
                    ? "Unavailable"
                    : typeof row[column] === "object"
                      ? JSON.stringify(row[column])
                      : String(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
const initial = (currency: string): MapConfig => ({
  kind: "",
  columns: {},
  currency,
  date_format: "ISO",
  decimal_format: "dot",
  amount_mode: "direct",
  namespace: "",
  profile_name: "",
});

export function SourceExplorer({
  base,
  currency,
  canWrite,
  initialFilters = {},
}: {
  base: string;
  currency: string;
  canWrite: boolean;
  initialFilters?: {
    start?: string;
    end?: string;
    kind?: string;
    customer_id?: string;
    counterparty?: string;
    currency?: string;
  };
}) {
  const [docs, setDocs] = useState<Doc[]>([]),
    [report, setReport] = useState<Report | null>(null),
    [doc, setDoc] = useState<Doc | null>(null);
  const [mapping, setMapping] = useState<MapConfig>(initial(currency)),
    [preview, setPreview] = useState<Preview | null>(null),
    [raw, setRaw] = useState<Record<string, unknown>[]>([]);
  const [suggested, setSuggested] = useState<Record<string, Suggestion>>({});
  const [profiles, setProfiles] = useState<
    { name: string; mapping: MapConfig; version: number }[]
  >([]);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [start, setStart] = useState(initialFilters.start || ""),
    [end, setEnd] = useState(initialFilters.end || ""),
    [kind, setKind] = useState(initialFilters.kind || ""),
    [offset, setOffset] = useState(0);
  const [customerFilter, setCustomerFilter] = useState(
    initialFilters.customer_id || "",
  );
  const [counterpartyFilter, setCounterpartyFilter] = useState<
    string | undefined
  >(initialFilters.counterparty);
  const [currencyFilter, setCurrencyFilter] = useState<string | undefined>(
    initialFilters.currency,
  );
  const [detail, setDetail] = useState<SourceEvidenceDetail | null>(null);
  const generation = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++generation.current;
    const params = new URLSearchParams({ offset: String(offset) });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    if (kind) params.set("kind", kind);
    if (customerFilter) params.set("customer_id", customerFilter);
    if (counterpartyFilter !== undefined)
      params.set("counterparty", counterpartyFilter);
    if (currencyFilter) params.set("currency", currencyFilter);
    const [result, documents, savedProfiles] = await Promise.all([
      api<Report>(`${base}/facts?${params}`),
      canWrite ? api<Doc[]>(`${base}/sources`) : Promise.resolve([]),
      canWrite
        ? api<{ name: string; mapping: MapConfig; version: number }[]>(
            `${base}/mapping-profiles`,
          )
        : Promise.resolve([]),
    ]);
    if (request !== generation.current) return;
    setReport(result);
    setDocs(documents);
    setProfiles(savedProfiles);
  }, [
    base,
    canWrite,
    start,
    end,
    kind,
    offset,
    customerFilter,
    counterpartyFilter,
    currencyFilter,
  ]);
  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled)
        void refresh().catch((e) => {
          if (!cancelled) setError(message(e));
        });
    });
    return () => {
      cancelled = true;
      // This ref is a request sequence, not a DOM node; invalidate pending reads.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      generation.current++;
    };
  }, [refresh]);
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
  async function open(d: Doc) {
    setDoc(d);
    setPreview(null);
    setRaw([]);
    setSuggested({});
    setMapping(initial(currency));
    const data = await api<{
      rows: { values: Record<string, unknown> }[];
      suggestions: Record<string, Suggestion>;
    }>(`${base}/sources/${d.id}/raw`);
    setRaw(data.rows.slice(0, 5).map((r) => r.values));
    setSuggested(data.suggestions);
    setMapping({
      ...initial(currency),
      columns: Object.fromEntries(
        Object.entries(data.suggestions).map(([k, v]) => [
          k,
          k === "customer_id" ? "" : v.column,
        ]),
      ),
    });
  }
  return (
    <div className="view-stack source-explorer">
      <MonthlyReview
        base={base}
        initialPeriod={report?.months
          .map((m) => m.month)
          .sort()
          .at(-1)}
        onInspect={(filters) => {
          setStart(filters.start || "");
          setEnd(filters.end || "");
          setKind(filters.kind || "");
          setCustomerFilter(filters.customer_id || "");
          setCounterpartyFilter(filters.counterparty);
          setCurrencyFilter(filters.currency);
          setOffset(0);
          requestAnimationFrame(() =>
            document
              .getElementById("supporting-source-records")
              ?.scrollIntoView({ behavior: "instant" }),
          );
        }}
      />
      <section className="panel glass">
        <h2>Source records &amp; financial observations</h2>
        {currencyFilter && <p>Currency filter: {currencyFilter}</p>}
        {counterpartyFilter !== undefined && (
          <p className="alert">
            Exact source name: {counterpartyFilter || "Not supplied"}.{" "}
            <button
              className="text-button"
              onClick={() => {
                setCounterpartyFilter(undefined);
                setOffset(0);
              }}
            >
              Clear name filter
            </button>
          </p>
        )}
        <p>
          Import documents without inventing customers, contracts or profit.
          Review mappings before confirmation. Observations stay separate from
          the verified invoice/cost ledger.
        </p>
        {customerFilter && (
          <p className="alert">
            Filtered to customer: <strong>{customerFilter}</strong>.{" "}
            <button
              className="text-button"
              onClick={() => {
                setCustomerFilter("");
                setOffset(0);
              }}
            >
              Show all accessible customers
            </button>
          </p>
        )}
        <div className="form-grid">
          <label>
            From date
            <input
              type="date"
              value={start}
              onChange={(e) => {
                setStart(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            To date
            <input
              type="date"
              value={end}
              onChange={(e) => {
                setEnd(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            Financial meaning
            <select
              aria-label="Financial meaning"
              value={kind}
              onChange={(e) => {
                setKind(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">All types (kept separate)</option>
              {kinds.map((k) => (
                <option key={k} value={k}>
                  {label(k)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {report && (
          <>
            <p>
              {canWrite ? `${docs.length} listed source documents · ` : ""}
              {report.total} matching observations · {report.unmatched}{" "}
              unmatched to customers. Unknown dates are excluded only when a
              date filter is applied.
            </p>
            <div className="form-grid">
              {report.groups.map((g) => (
                <button
                  className="secondary"
                  key={g.kind + g.currency}
                  onClick={() => {
                    setKind(g.kind);
                    setOffset(0);
                  }}
                >
                  <span>
                    {label(g.kind)}
                    <br />
                    <strong>
                      {g.amount === null
                        ? "Balance snapshots — inspect individually"
                        : `${g.currency} ${g.amount}`}
                    </strong>
                    <br />
                    {g.count} records · inspect sources ↗
                  </span>
                </button>
              ))}
            </div>
            <p className="footnote">{report.notice}</p>
            {report.months.length > 0 && (
              <>
                <h3>Recorded amounts by month</h3>
                <p className="footnote">
                  Separate meanings; negative bars are source credits/reversals.
                  Click a month to inspect its records. Unknown dates and
                  balance snapshots are excluded.
                </p>
                <div className="sales-bars">
                  {report.months.map((m) => (
                    <button
                      className="secondary"
                      key={m.month + m.kind + m.currency}
                      onClick={() => {
                        setKind(m.kind);
                        setStart(m.month + "-01");
                        const [y, n] = m.month.split("-").map(Number);
                        setEnd(
                          `${m.month}-${new Date(Date.UTC(y, n, 0)).getUTCDate()}`,
                        );
                        setOffset(0);
                      }}
                    >
                      <span>
                        {m.month} · {label(m.kind)} · {m.currency} {m.amount} ·{" "}
                        {m.count} records
                      </span>
                      <span className="sales-track" style={{ width: "100%" }}>
                        <span
                          style={{
                            width: `${(Math.abs(Number(m.amount)) / Math.max(1, ...report.months.filter((x) => x.kind === m.kind).map((x) => Math.abs(Number(x.amount))))) * 100}%`,
                            background:
                              Number(m.amount) < 0 ? "#d59691" : undefined,
                          }}
                        />
                      </span>
                    </button>
                  ))}
                </div>
                <button
                  className="text-button"
                  onClick={() => {
                    setStart("");
                    setEnd("");
                    setKind("");
                    setCustomerFilter("");
                    setOffset(0);
                  }}
                >
                  Clear filters
                </button>
              </>
            )}
          </>
        )}
      </section>
      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="alert" role="status">
          {notice}
        </p>
      )}
      {canWrite && (
        <section className="panel glass">
          <h2>1. Upload your source file</h2>
          <p>
            Keep your original file. Review its meaning and fields before
            anything is added to your reports.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = new FormData(e.currentTarget);
              void action(async () => {
                const d = await api<Doc>(`${base}/sources`, {
                  method: "POST",
                  body: form,
                });
                await refresh();
                await open(d);
              });
            }}
          >
            <div className="form-grid">
              <label>
                Original CSV, TSV, XLSX, JSON or text PDF
                <input
                  name="file"
                  type="file"
                  required
                  accept=".csv,.tsv,.xlsx,.json,.pdf"
                />
              </label>
              <label>
                Source adapter
                <select name="adapter">
                  <option value="generic">Generic table / PDF text</option>
                  <option value="fhdc_card">
                    FHDC procurement-card PDF (reviewed layout)
                  </option>
                </select>
              </label>
            </div>
            <button className="primary" disabled={busy}>
              Extract and retain original
            </button>
          </form>
          <p className="footnote">
            At most 2,000 rows; hosted upload limit 4 MB. One worksheet; no
            formula execution or OCR. All unknown columns are retained. Header
            suggestions are candidates, not semantic proof.
          </p>
          <ul className="doc-stack">
            {docs.map((d) => (
              <li key={d.id}>
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={() => void action(() => open(d))}
                >
                  {d.filename}
                </button>
                <span className="tag">{d.state}</span>
                <a href={`/api${base}/sources/${d.id}/file`}>Original ↗</a>
              </li>
            ))}
          </ul>
        </section>
      )}
      {doc && (
        <section className="panel glass">
          <h2>2. Review mapping: {doc.filename}</h2>
          <p className="footnote">SHA-256: {doc.sha256}</p>
          {raw.length > 0 ? (
            <details>
              <summary>Original sample rows (all columns preserved)</summary>
              <SampleTable rows={raw} />
            </details>
          ) : (
            <details>
              <summary>Extracted PDF pages — no inferred finances</summary>
              {doc.pages.map((p) => (
                <pre key={p.page} style={{ whiteSpace: "pre-wrap" }}>
                  Page {p.page}: {p.text}
                </pre>
              ))}
            </details>
          )}
          {doc.state !== "confirmed" && doc.headers.length > 0 && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void action(async () =>
                  setPreview(
                    await api<Preview>(`${base}/sources/${doc.id}/preview`, {
                      method: "POST",
                      body: JSON.stringify(mapping),
                    }),
                  ),
                );
              }}
              onChange={() => setPreview(null)}
            >
              <div className="form-grid">
                <label>
                  Saved mapping profile
                  <select
                    onChange={(e) => {
                      const p = profiles.find((p) => p.name === e.target.value);
                      if (p) setMapping(p.mapping);
                    }}
                    defaultValue=""
                  >
                    <option value="">Choose a reviewed profile</option>
                    {profiles.map((p) => (
                      <option key={p.name}>{p.name}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Record meaning
                  <select
                    aria-label="Record meaning"
                    value={mapping.kind}
                    required
                    onChange={(e) =>
                      setMapping({
                        ...mapping,
                        kind: e.target.value,
                        amount_mode: "direct",
                      })
                    }
                  >
                    <option value="">Choose what these records mean</option>
                    {kinds.map((k) => (
                      <option key={k} value={k}>
                        {label(k)}
                      </option>
                    ))}
                  </select>
                  <small>
                    {kindHelp[mapping.kind] ||
                      "A column named Amount does not tell us whether it is sales, spending, cash or a balance. Please choose."}
                  </small>
                </label>
                <label>
                  Amount derivation
                  <select
                    value={mapping.amount_mode}
                    onChange={(e) =>
                      setMapping({ ...mapping, amount_mode: e.target.value })
                    }
                  >
                    <option value="direct">Direct source amount</option>
                    {mapping.kind === "reported_sales" && (
                      <option value="quantity_price">
                        Quantity × price (reported sales only)
                      </option>
                    )}
                    {["cash_inflow", "cash_outflow"].includes(mapping.kind) && (
                      <option value="bank_columns">
                        Bank statement: separate money received / paid
                      </option>
                    )}
                  </select>
                </label>
                {[
                  ...(mapping.amount_mode === "quantity_price"
                    ? ["quantity", "unit_price"]
                    : mapping.amount_mode === "bank_columns"
                      ? ["credit", "debit"]
                      : ["amount"]),
                  "date",
                  "description",
                  "counterparty",
                  "external_id",
                  "customer_id",
                  "currency",
                ].map((target) => (
                  <label key={target}>
                    {columnLabel(target)} source column
                    <select
                      aria-label={`${columnLabel(target)} source column`}
                      value={mapping.columns[target] || ""}
                      onChange={(e) =>
                        setMapping({
                          ...mapping,
                          columns: {
                            ...mapping.columns,
                            [target]: e.target.value,
                          },
                        })
                      }
                    >
                      <option value="">Unmapped / unavailable</option>
                      {doc.headers.map((h) => (
                        <option key={h}>{h}</option>
                      ))}
                    </select>
                    <small>
                      {suggested[target]?.confidence === "ambiguous"
                        ? `Needs review: ${suggested[target].candidates?.join(", ")}`
                        : suggested[target]?.column &&
                            mapping.columns[target] === suggested[target].column
                          ? "Suggested by header — verify against the sample"
                          : mapping.columns[target]
                            ? "Selected for your review"
                            : "Unmapped; kept in the original record"}
                    </small>
                  </label>
                ))}
                <label>
                  Declared currency
                  <input
                    required
                    value={mapping.currency}
                    onChange={(e) =>
                      setMapping({ ...mapping, currency: e.target.value })
                    }
                  />
                </label>
                <label>
                  Date convention
                  <select
                    value={mapping.date_format}
                    onChange={(e) =>
                      setMapping({ ...mapping, date_format: e.target.value })
                    }
                  >
                    {["ISO", "DMY", "MDY"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Decimal convention
                  <select
                    value={mapping.decimal_format}
                    onChange={(e) =>
                      setMapping({ ...mapping, decimal_format: e.target.value })
                    }
                  >
                    <option value="dot">1,234.56</option>
                    <option value="comma">1.234,56</option>
                  </select>
                </label>
                <label>
                  Identifier namespace
                  <input
                    value={mapping.namespace}
                    onChange={(e) =>
                      setMapping({ ...mapping, namespace: e.target.value })
                    }
                  />
                </label>
                <label>
                  Save as mapping profile (optional)
                  <input
                    value={mapping.profile_name}
                    onChange={(e) =>
                      setMapping({ ...mapping, profile_name: e.target.value })
                    }
                  />
                </label>
              </div>
              {mapping.amount_mode === "bank_columns" && (
                <p className="alert">
                  Review the bank account perspective: credits mean money
                  received; debits mean money paid. Both directions are imported
                  separately. Blank opposite cells mean no movement in that
                  direction; both nonzero or negative values are rejected. Cash
                  movements are not automatically sales or expenses.
                </p>
              )}
              <button className="primary" disabled={busy || !mapping.kind}>
                Preview normalized records
              </button>
            </form>
          )}
          {preview && (
            <div>
              <h3>3. Check and confirm</h3>
              <p>
                {preview.row_count} records · {preview.issues.length} issues
              </p>
              <p>
                Unmapped columns retained:{" "}
                {preview.unmapped_columns.join(", ") || "None"}
              </p>
              {preview.issues.map((i, n) => (
                <p key={n} className="alert error">
                  Row {i.row}: {i.message}
                </p>
              ))}
              <details open>
                <summary>Normalized preview</summary>
                <SampleTable rows={preview.rows} />
              </details>
              <p>{preview.notice}</p>
              <button
                className="primary"
                disabled={busy || preview.issues.length > 0}
                onClick={() =>
                  void action(async () => {
                    await api(`${base}/sources/${doc.id}/confirm`, {
                      method: "POST",
                      body: JSON.stringify({
                        preview_token: preview.preview_token,
                      }),
                    });
                    setDoc(null);
                    setPreview(null);
                    setNotice(
                      "Source import confirmed. Original data retained.",
                    );
                    await refresh();
                  })
                }
              >
                Confirm reviewed mapping
              </button>
            </div>
          )}
        </section>
      )}
      {report && (
        <section className="panel glass">
          <h2 id="supporting-source-records">Supporting records</h2>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Meaning</th>
                  <th>Counterparty / description</th>
                  <th>Amount</th>
                  <th>Relationship</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {report.rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.occurred_on || "Unknown"}</td>
                    <td>{label(r.kind)}</td>
                    <td>
                      {r.counterparty || "Unspecified"}
                      <small>{r.description}</small>
                    </td>
                    <td>
                      {r.currency} {r.amount}
                    </td>
                    <td>{r.customer_id || "Unmatched"}</td>
                    <td>
                      <button
                        className="text-button"
                        onClick={() =>
                          void action(async () =>
                            setDetail(await api(`${base}/facts/${r.id}`)),
                          )
                        }
                      >
                        Source row {r.row_number} ↗
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="button-row">
            <button
              className="secondary"
              disabled={!offset}
              onClick={() => setOffset(Math.max(0, offset - 100))}
            >
              Previous
            </button>
            <button
              className="secondary"
              disabled={offset + 100 >= report.total}
              onClick={() => setOffset(offset + 100)}
            >
              Next
            </button>
          </div>
        </section>
      )}
      {detail && (
        <Modal
          heading={`Evidence: ${detail.filename}`}
          close={() => setDetail(null)}
        >
          <SourceEvidenceBody detail={detail} base={base} />
          {error && (
            <p className="alert error" role="alert">
              {error}
            </p>
          )}
          {notice && (
            <p className="alert" role="status">
              {notice}
            </p>
          )}
          {canWrite && (
            <form
              className="form-grid"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                void action(async () => {
                  await api(`${base}/facts/${detail.fact.id}/link`, {
                    method: "PUT",
                    body: JSON.stringify({
                      customer_id: f.get("customer"),
                      reason: f.get("reason"),
                    }),
                  });
                  if (f.get("alias") && detail.fact.counterparty)
                    await api(`${base}/entity-aliases`, {
                      method: "POST",
                      body: JSON.stringify({
                        alias: detail.fact.counterparty,
                        customer_id: f.get("customer"),
                      }),
                    });
                  setNotice(
                    "Relationship reviewed. No financial amounts were changed.",
                  );
                  await refresh();
                  setDetail(await api(`${base}/facts/${detail.fact.id}`));
                });
              }}
            >
              <label>
                Verified customer ID
                <input
                  name="customer"
                  required
                  defaultValue={detail.fact.customer_id || ""}
                />
              </label>
              <label>
                Evidence for this relationship
                <input name="reason" required minLength={5} />
              </label>
              <label>
                <input name="alias" type="checkbox" />
                Also verify this exact counterparty alias for future imports
              </label>
              <button className="secondary" disabled={busy}>
                Confirm customer relationship
              </button>
            </form>
          )}
          <button className="secondary" onClick={() => setDetail(null)}>
            Close source
          </button>
        </Modal>
      )}
    </div>
  );
}
