"use client";
import { useEffect, useState, type FormEvent } from "react";
import { api, message, type RecordData, type View } from "../lib/workspace";
import { Modal } from "./ui";
import "./operations.css";

type Row = Record<string, unknown>;
type Draft = Row & {
  snapshot: Record<string, string>;
  id: string;
  state: string;
  issued_on: string;
};
type Line = {
  item_id: string;
  description: string;
  quantity: string;
  unit_price: string;
  tax: string;
};
const emptyLine = (): Line => ({
  item_id: "",
  description: "",
  quantity: "1",
  unit_price: "",
  tax: "0",
});
const today = () => new Date().toLocaleDateString("en-CA");
const val = (r: Row, k: string) => String(r[k] ?? "");

export function PlanningPanel({
  base,
  view,
  currency,
  customers,
  changeView,
}: {
  base: string;
  view: "recurring" | "orders";
  currency: string;
  customers: RecordData[];
  changeView: (v: View) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]),
    [drafts, setDrafts] = useState<Draft[]>([]);
  const [vendors, setVendors] = useState<Row[]>([]),
    [items, setItems] = useState<Row[]>([]);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const [form, setForm] = useState<"create" | "bill" | null>(null),
    [selected, setSelected] = useState<Row | null>(null),
    [lines, setLines] = useState<Line[]>([emptyLine()]),
    [query, setQuery] = useState("");
  const [revision, setRevision] = useState(0);
  const load = () => setRevision((x) => x + 1);
  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      try {
        if (view === "recurring") {
          const r = await api<{ schedules: Row[]; drafts: Draft[] }>(
            `${base}/planning/recurring`,
            { signal: controller.signal },
          );
          if (controller.signal.aborted) return;
          setRows(r.schedules);
          setDrafts(r.drafts);
        } else {
          const [r, v, i] = await Promise.all([
            api<Row[]>(`${base}/planning/orders`),
            api<Row[]>(`${base}/operations/vendors`),
            api<Row[]>(`${base}/operations/items`),
          ]);
          if (controller.signal.aborted) return;
          setRows(r);
          setVendors(v);
          setItems(i);
        }
      } catch (e) {
        if (!controller.signal.aborted) setError(message(e));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void fetchData();
    return () => controller.abort();
  }, [base, view, revision]);
  async function action(path: string, body?: unknown, method = "POST") {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await api<Row>(`${base}/planning/${path}`, {
        method,
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      setNotice(
        r.message
          ? String(r.message)
          : "Saved. Financial records and review history are up to date.",
      );
      setForm(null);
      setSelected(null);
      await load();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  }
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget));
    if (form === "bill") {
      void action(
        `orders/${val(selected!, "id")}/bill`,
        {
          ...f,
          due_on: f.due_on || null,
          payments_complete: true,
          invoice_matches_order: true,
        },
        "PUT",
      );
      return;
    }
    if (view === "recurring")
      void action("recurring", {
        ...f,
        currency,
        interval_months: Number(f.interval_months),
        due_days: Number(f.due_days),
        end_on: f.end_on || null,
      });
    else
      void action("orders", {
        ...f,
        currency,
        expected_on: f.expected_on || null,
        lines: lines.map((l) => ({ ...l, item_id: l.item_id || null })),
      });
  }
  const visible = rows.filter((r) =>
    JSON.stringify(r).toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <section className="operations-panel">
      <div className="table-toolbar">
        <div>
          <h2>
            {view === "recurring"
              ? "Recurring billing"
              : "Purchase commitments"}
          </h2>
          <p>
            {view === "recurring"
              ? "Prepare scheduled drafts, review the charges, then issue into your invoice ledger."
              : "Plan purchases, approve an order, then record the matching supplier bill."}
          </p>
        </div>
        <button disabled={busy || loading} onClick={() => void load()}>
          Refresh
        </button>
        <button
          className="primary"
          onClick={() => {
            setLines([emptyLine()]);
            setForm("create");
          }}
        >
          New {view === "recurring" ? "schedule" : "purchase order"}
        </button>
      </div>
      {error && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="alert">
          {notice}
        </p>
      )}
      <div className="panel glass">
        <p>
          {view === "recurring"
            ? "Monthly, quarterly or yearly schedules. Generate due drafts when you review billing; nothing is emailed or charged automatically. Pausing stops future generation; existing drafts remain reviewable."
            : "Orders are commitments, not expenses or payments. Conversion requires a received supplier invoice matching the full order. Partial billing and stock receipts are not supported."}
        </p>
        {view === "recurring" ? (
          <button
            disabled={busy}
            onClick={() => void action("recurring/generate")}
          >
            Generate due drafts
          </button>
        ) : (
          <button onClick={() => changeView("vendors")}>Manage vendors</button>
        )}
      </div>
      <label>
        Search {view === "recurring" ? "schedules" : "orders"}
        <input value={query} onChange={(e) => setQuery(e.target.value)} />
      </label>
      {loading ? (
        <p role="status">Loading…</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>
                  {view === "recurring"
                    ? "Customer / next date"
                    : "Vendor / order date"}
                </th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((r) => (
                <tr key={val(r, "id")}>
                  <td>
                    <button onClick={() => setSelected(r)}>
                      {val(r, "name") || val(r, "id")}
                    </button>
                    <small>{val(r, "id")}</small>
                  </td>
                  <td>
                    {val(r, view === "recurring" ? "customer_id" : "vendor_id")}
                    <br />
                    {val(r, view === "recurring" ? "next_on" : "ordered_on")}
                    {view === "orders" && (
                      <div>
                        {currency} {val(r, "total")}
                      </div>
                    )}
                  </td>
                  <td>{val(r, "state")}</td>
                  <td>
                    {view === "recurring" && r.state !== "completed" ? (
                      <button
                        disabled={busy}
                        onClick={() =>
                          void action(
                            `recurring/${val(r, "id")}/state`,
                            {
                              state: r.state === "active" ? "paused" : "active",
                            },
                            "PUT",
                          )
                        }
                      >
                        {r.state === "active" ? "Pause" : "Resume"}
                      </button>
                    ) : null}
                    {view === "orders" && r.state === "draft" && (
                      <button
                        disabled={busy}
                        onClick={() =>
                          void action(`orders/${val(r, "id")}/approve`)
                        }
                      >
                        Approve
                      </button>
                    )}
                    {view === "orders" && r.state === "approved" && (
                      <button
                        onClick={() => {
                          setSelected(r);
                          setForm("bill");
                        }}
                      >
                        Record matching bill
                      </button>
                    )}
                    {view === "orders" &&
                      ["draft", "approved"].includes(val(r, "state")) && (
                        <button
                          disabled={busy}
                          onClick={() => {
                            setSelected(r);
                          }}
                        >
                          Review / cancel
                        </button>
                      )}
                    {Boolean(r.bill_id) && (
                      <button onClick={() => changeView("bills")}>
                        View bills
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!visible.length && (
            <p>
              No {view === "recurring" ? "schedules" : "purchase orders"} yet.
              Create one to begin.
            </p>
          )}
        </div>
      )}
      {view === "recurring" && (
        <section className="panel glass">
          <h2>Generated drafts & history</h2>
          <p>
            Issuing confirms these are new, unpaid charges. It adds verified
            revenue and a tracked receivable. Do not issue a charge already
            imported elsewhere.
          </p>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Schedule / date</th>
                  <th>Amounts</th>
                  <th>State</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {drafts.map((d) => (
                  <tr key={d.id}>
                    <td>
                      {d.snapshot.name}
                      <br />
                      {d.issued_on}
                    </td>
                    <td>
                      {currency} {d.snapshot.subtotal} subtotal
                      <br />
                      {d.snapshot.discount} discount · {d.snapshot.tax} tax
                    </td>
                    <td>{d.state}</td>
                    <td>
                      {d.state === "draft" ? (
                        <>
                          <button
                            disabled={busy}
                            onClick={() => setSelected(d)}
                          >
                            Review draft
                          </button>
                        </>
                      ) : d.state === "issued" ? (
                        <button onClick={() => changeView("invoices")}>
                          View invoices
                        </button>
                      ) : (
                        "Skipped with history retained"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!drafts.length && (
            <p>No drafts generated. Future schedules appear here when due.</p>
          )}
        </section>
      )}
      {form && (
        <Modal
          heading={
            form === "bill"
              ? "Record matching supplier bill"
              : view === "recurring"
                ? "New recurring schedule"
                : "New purchase order"
          }
          close={() => {
            if (!busy) {
              setForm(null);
              setSelected(null);
            }
          }}
        >
          <form onSubmit={submit} className="operation-form">
            {form === "bill" ? (
              <>
                <label>
                  Supplier bill reference
                  <input name="bill_id" required maxLength={80} />
                </label>
                <label>
                  Bill date
                  <input
                    name="issued_on"
                    type="date"
                    required
                    defaultValue={today()}
                  />
                </label>
                <label>
                  Due date
                  <input name="due_on" type="date" />
                </label>
                <label>
                  Already paid
                  <input
                    name="opening_paid"
                    required
                    type="number"
                    min="0"
                    step="0.01"
                  />
                </label>
                <p>
                  {currency} {val(selected!, "total")} will become a payable; it
                  does not become an expense automatically.
                </p>
                <label>
                  <input type="checkbox" required />I reviewed payment history
                  and the received invoice matches this entire order.
                </label>
              </>
            ) : (
              <>
                <label>
                  Reference
                  <input
                    name="id"
                    required
                    maxLength={80}
                    pattern="[A-Za-z0-9][A-Za-z0-9._-]*"
                  />
                </label>
                {view === "recurring" ? (
                  <>
                    <label>
                      Schedule name
                      <input name="name" required maxLength={200} />
                    </label>
                    <label>
                      Customer
                      <select name="customer_id" aria-label="Customer" required>
                        <option value="">Choose customer</option>
                        {customers.map((c) => (
                          <option key={c.customer_id} value={c.customer_id}>
                            {String(c.name || c.customer_id)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Start date
                      <input
                        name="start_on"
                        type="date"
                        required
                        defaultValue={today()}
                      />
                    </label>
                    <label>
                      End date (optional)
                      <input name="end_on" type="date" />
                    </label>
                    <label>
                      Frequency
                      <select name="interval_months" aria-label="Frequency">
                        <option value="1">Monthly</option>
                        <option value="3">Quarterly</option>
                        <option value="12">Yearly</option>
                      </select>
                    </label>
                    <label>
                      Payment due in days
                      <input
                        name="due_days"
                        type="number"
                        min="0"
                        max="365"
                        defaultValue="30"
                        required
                      />
                    </label>
                    {["subtotal", "discount", "tax"].map((k) => (
                      <label key={k}>
                        {k}
                        <input
                          name={k}
                          aria-label={k}
                          type="number"
                          min={k === "subtotal" ? "0.01" : "0"}
                          step="0.01"
                          required
                          defaultValue={k === "subtotal" ? undefined : "0"}
                        />
                      </label>
                    ))}
                    <p>
                      Fixed charges in {currency}. Dates keep the original day,
                      clamped to month end. Change terms by pausing this
                      schedule and creating a new one.
                    </p>
                  </>
                ) : (
                  <>
                    <label>
                      Vendor
                      <select name="vendor_id" aria-label="Vendor" required>
                        <option value="">Choose vendor</option>
                        {vendors.map((v) => (
                          <option
                            key={val(v, "vendor_id")}
                            value={val(v, "vendor_id")}
                          >
                            {val(v, "name")}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Order date
                      <input
                        name="ordered_on"
                        type="date"
                        required
                        defaultValue={today()}
                      />
                    </label>
                    <label>
                      Expected date
                      <input name="expected_on" type="date" />
                    </label>
                    <label>
                      Notes
                      <textarea name="notes" maxLength={1000} />
                    </label>
                    {lines.map((l, index) => (
                      <fieldset key={index}>
                        <legend>Line {index + 1}</legend>
                        <label>
                          Catalogue item (optional)
                          <select
                            aria-label={`Item ${index + 1}`}
                            value={l.item_id}
                            onChange={(e) => {
                              const item = items.find(
                                (i) => i.item_id === e.target.value,
                              );
                              setLines(
                                lines.map((x, j) =>
                                  j === index
                                    ? {
                                        ...x,
                                        item_id: e.target.value,
                                        ...(item
                                          ? {
                                              description: val(item, "name"),
                                              unit_price: val(
                                                item,
                                                "unit_price",
                                              ),
                                            }
                                          : {}),
                                      }
                                    : x,
                                ),
                              );
                            }}
                          >
                            <option value="">Custom service / goods</option>
                            {items.map((i) => (
                              <option
                                key={val(i, "item_id")}
                                value={val(i, "item_id")}
                              >
                                {val(i, "name")}
                              </option>
                            ))}
                          </select>
                        </label>
                        {["description", "quantity", "unit_price", "tax"].map(
                          (k) => (
                            <label key={k}>
                              {k.replace("_", " ")}
                              <input
                                aria-label={`${k} ${index + 1}`}
                                required
                                value={l[k as keyof Line]}
                                type={k === "description" ? "text" : "number"}
                                min={k === "quantity" ? "0.001" : "0"}
                                step={k === "quantity" ? "0.001" : "0.01"}
                                maxLength={300}
                                onChange={(e) =>
                                  setLines(
                                    lines.map((x, j) =>
                                      j === index
                                        ? { ...x, [k]: e.target.value }
                                        : x,
                                    ),
                                  )
                                }
                              />
                            </label>
                          ),
                        )}
                        {lines.length > 1 && (
                          <button
                            type="button"
                            onClick={() =>
                              setLines(lines.filter((_, j) => j !== index))
                            }
                          >
                            Remove line {index + 1}
                          </button>
                        )}
                      </fieldset>
                    ))}
                    <button
                      type="button"
                      disabled={lines.length >= 50}
                      onClick={() => setLines([...lines, emptyLine()])}
                    >
                      Add line
                    </button>
                    <p>
                      Tax is an explicit amount per line. Totals are rounded and
                      calculated on the server in {currency}.
                    </p>
                  </>
                )}
              </>
            )}
            <button type="submit" className="primary" disabled={busy}>
              {busy ? "Saving…" : "Save"}
            </button>
            {error && <p role="alert">{error}</p>}
          </form>
        </Modal>
      )}
      {selected && !form && (
        <Modal
          heading={
            "snapshot" in selected ? "Review recurring draft" : "Record details"
          }
          close={() => setSelected(null)}
        >
          <dl>
            {Object.entries(selected)
              .filter(
                ([k]) => !["organization_id", "snapshot", "lines"].includes(k),
              )
              .map(([k, v]) => (
                <div key={k}>
                  <dt>{k.replaceAll("_", " ")}</dt>
                  <dd>{String(v ?? "Not provided")}</dd>
                </div>
              ))}
          </dl>
          {"snapshot" in selected && (
            <>
              <dl>
                {Object.entries(
                  selected.snapshot as Record<string, unknown>,
                ).map(([key, value]) => (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>{String(value)}</dd>
                  </div>
                ))}
              </dl>
              <p>
                Confirm this charge is new, unpaid and correct before issuing.
                It will affect revenue and receivables.
              </p>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  void action(`drafts/${val(selected, "id")}/issue`)
                }
              >
                Confirm & issue invoice
              </button>
              <button
                disabled={busy}
                onClick={() =>
                  void action(`drafts/${val(selected, "id")}/skip`)
                }
              >
                Skip this occurrence
              </button>
            </>
          )}
          {Array.isArray(selected.lines) && (
            <>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th>Quantity</th>
                      <th>Unit price</th>
                      <th>Tax</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selected.lines as Row[]).map((l) => (
                      <tr key={val(l, "line")}>
                        {[
                          "description",
                          "quantity",
                          "unit_price",
                          "tax",
                          "amount",
                        ].map((k) => (
                          <td key={k}>{val(l, k)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {["draft", "approved"].includes(val(selected, "state")) && (
                <button
                  disabled={busy}
                  onClick={() =>
                    void action(`orders/${val(selected, "id")}/cancel`)
                  }
                >
                  Confirm cancellation
                </button>
              )}
            </>
          )}
          {error && <p role="alert">{error}</p>}
        </Modal>
      )}
    </section>
  );
}
