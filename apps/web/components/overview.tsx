"use client";
import { useEffect, useState } from "react";
import { api, type View } from "../lib/workspace";
import type { Props } from "./overview-types";
export type { OverviewData } from "./overview-types";
import "./focus-dashboard.css";
type Balance = { total: string; overdue: string; untracked_count?: number };
type Series = {
  label: string;
  note: string;
  view: View;
  points: { period: string; amount: string }[];
};
const money = (v: string, c: string) =>
  `${c} ${Number(v).toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export function Overview({ base, data, canWrite, changeView }: Props) {
  const [range, setRange] = useState("6"),
    [balance, setBalance] = useState<{
      receivables: Balance;
      payables: Balance;
    } | null>(null),
    [failed, setFailed] = useState(false);
  const [tasks, setTasks] = useState<{ drafts: number; orders: number } | null>(
    null,
  );
  const s = data.summary,
    c = s?.currency || "INR",
    counts = s?.counts || {};
  useEffect(() => {
    if (!canWrite) return;
    let live = true;
    Promise.all([
      api<{ receivables: Balance; payables: Balance }>(
        `${base}/operations/summary`,
      ),
      api<{ drafts: { state: string }[] }>(`${base}/planning/recurring`),
      api<{ state: string }[]>(`${base}/planning/orders`),
    ])
      .then(([b, r, o]) => {
        if (live) {
          setBalance(b);
          setTasks({
            drafts: r.drafts.filter((x) => x.state === "draft").length,
            orders: o.filter((x) => ["draft", "approved"].includes(x.state))
              .length,
          });
        }
      })
      .catch(() => {
        if (live) setFailed(true);
      });
    return () => {
      live = false;
    };
  }, [base, canWrite]);
  const series: Series[] = [];
  if (s?.months.some((m) => m.verified_net_revenue !== null))
    series.push({
      label: "Net billed revenue",
      note: "Verified invoice ledger · excludes tax",
      view: "finance",
      points: s.months
        .filter((m) => m.verified_net_revenue !== null)
        .map((m) => ({
          period: m.billing_period,
          amount: m.verified_net_revenue!,
        })),
    });
  if (s?.cost_series?.length)
    series.push({
      label: "Attributed customer costs",
      note: "Recorded costs · completeness requires review",
      view: "finance",
      points: s.cost_series,
    });
  const names: Record<string, string> = {
    reported_sales: "Reported sales",
    expenditure: "Recorded expenditure",
    cash_inflow: "Bank inflows",
    cash_outflow: "Bank outflows",
    commitment: "Source commitments",
  };
  for (const kind of Object.keys(names)) {
    const rows = (s?.source_series || []).filter(
      (x) => x.kind === kind && x.period,
    );
    if (rows.length)
      series.push({
        label: names[kind],
        note: "Source observations · original dates preserved",
        view: "data",
        points: rows.map((x) => ({ period: x.period!, amount: x.amount })),
      });
  }
  if (
    !series.some((x) => x.label === "Reported sales") &&
    s?.months.some((m) => m.reported_sales !== null)
  )
    series.push({
      label: "Reported sales",
      note: "Reported amounts · costs and tax breakdown unknown",
      view: "invoices",
      points: s.months
        .filter((m) => m.reported_sales !== null)
        .map((m) => ({ period: m.billing_period, amount: m.reported_sales! })),
    });
  const undated = (s?.source_series || [])
    .filter((x) => !x.period)
    .reduce((n, x) => n + x.records, 0);
  return (
    <div className="focus-dashboard">
      <section className="focus-intro">
        <div>
          <span className="focus-kicker">Evidence before conclusions</span>
          <h2>See the signal. Take the next step.</h2>
          <p>
            Revenue, spending and commitments keep their own meaning. Profit
            needs verified revenue and sufficient cost evidence.
          </p>
        </div>
        <button
          className="primary"
          onClick={() =>
            changeView(s?.verified_net_revenue != null ? "analysis" : "data")
          }
        >
          {s?.verified_net_revenue != null
            ? "Investigate profitability"
            : "Explore source evidence"}{" "}
          ↗
        </button>
      </section>
      <section className="focus-kpis" aria-label="Workspace coverage">
        {[
          {
            label: "Evidence documents",
            n: (counts.source_documents || 0) + (counts.contracts || 0),
            v: "documents",
          },
          {
            label: counts.financial_facts
              ? "Source observations"
              : "Invoice records",
            n: counts.financial_facts || counts.invoices || 0,
            v: counts.financial_facts ? "data" : "invoices",
          },
          {
            label: counts.customers
              ? "Customer relationships"
              : "Named counterparties",
            n: counts.customers || counts.source_counterparties || 0,
            v: counts.customers ? "customers" : "data",
          },
          {
            label: "Pending source reviews",
            n: counts.review_tasks || 0,
            v: "data",
          },
        ].map((x) => (
          <button
            key={x.label}
            className="glass focus-kpi"
            onClick={() => changeView(x.v as View)}
          >
            <span>{x.label} ↗</span>
            <strong>{x.n.toLocaleString()}</strong>
            <small>Open supporting records</small>
          </button>
        ))}
      </section>
      <div className="focus-section-heading">
        <div>
          <h2>Financial activity</h2>
          <p>
            Actual recorded periods. Missing months are not filled with zero.
          </p>
        </div>
        <label>
          Chart range
          <select
            aria-label="Chart range"
            value={range}
            onChange={(e) => setRange(e.target.value)}
          >
            <option value="6">Latest 6 recorded months</option>
            <option value="12">Latest 12 recorded months</option>
            <option value="all">All recorded months</option>
          </select>
        </label>
      </div>
      <section className="focus-charts" aria-label="Financial trends">
        {series.map((x) => {
          const points =
            range === "all" ? x.points : x.points.slice(-Number(range));
          const max = Math.max(
            1,
            ...points.map((p) => Math.abs(Number(p.amount))),
          );
          return (
            <article className="glass focus-chart" key={x.label}>
              <h3>{x.label}</h3>
              <p>{x.note}</p>
              <strong className="focus-latest">
                {money(points.at(-1)!.amount, c)}
              </strong>
              <small>Latest recorded month · {points.at(-1)!.period}</small>
              <div
                className="focus-bars"
                role="img"
                aria-label={`${x.label}: ${points.map((p) => `${p.period} ${p.amount} ${c}`).join(", ")}`}
              >
                {points.map((p) => (
                  <div
                    key={p.period}
                    title={`${p.period}: ${money(p.amount, c)}`}
                  >
                    <div className="focus-bar-track">
                      <span
                        className={Number(p.amount) < 0 ? "negative" : ""}
                        style={{
                          height: `${Math.max(2, (Math.abs(Number(p.amount)) / max) * 100)}%`,
                        }}
                      />
                    </div>
                    <small>{p.period.slice(2)}</small>
                  </div>
                ))}
              </div>
              <details>
                <summary>View exact monthly figures</summary>
                <table>
                  <thead>
                    <tr>
                      <th>Period</th>
                      <th>{c}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {points.map((p) => (
                      <tr key={p.period}>
                        <td>{p.period}</td>
                        <td>{money(p.amount, c)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
              <button onClick={() => changeView(x.view)}>
                Inspect {x.label.toLowerCase()} records →
              </button>
            </article>
          );
        })}
        {!series.length && (
          <article className="panel glass">
            <h3>No dated financial activity yet</h3>
            <p>
              Import and review records to see meaningful trends. Missing values
              stay unavailable.
            </p>
            <button onClick={() => changeView("data")}>
              Explore available records
            </button>
          </article>
        )}
      </section>
      {undated > 0 && (
        <p className="alert">
          {undated} observations have no verified date and are excluded from
          monthly charts.
        </p>
      )}
      {canWrite &&
        (!(counts.financial_facts > 0 && !counts.invoices) ||
          (tasks?.orders || 0) > 0 ||
          Number(balance?.payables.total || 0) > 0) && (
          <section className="focus-bottom">
            <article className="panel glass">
              <h2>Money still due</h2>
              <p>
                Tracked balances only. Imported invoices are not assumed unpaid.
              </p>
              {balance ? (
                <>
                  <div className="focus-balances">
                    {(["receivables", "payables"] as const).map((k) => (
                      <button key={k} onClick={() => changeView("accounts")}>
                        <span>{k}</span>
                        <strong>{money(balance[k].total, c)}</strong>
                        <small>{money(balance[k].overdue, c)} overdue</small>
                      </button>
                    ))}
                  </div>
                  <p>
                    {balance.receivables.untracked_count || 0} invoice records
                    outside balance tracking.
                  </p>
                </>
              ) : (
                <p>
                  {failed
                    ? "Summary unavailable. Open Money tracking to retry."
                    : "Loading balances…"}
                </p>
              )}
              <button onClick={() => changeView("accounts")}>
                Review balances →
              </button>
            </article>
            <article className="panel glass">
              <h2>Your review queue</h2>
              <button
                className="focus-task"
                onClick={() => changeView("recurring")}
              >
                Recurring invoices{" "}
                <small>
                  {tasks
                    ? `${tasks.drafts} generated drafts to review`
                    : "Open billing schedule"}
                </small>{" "}
                ↗
              </button>
              <button
                className="focus-task"
                onClick={() => changeView("orders")}
              >
                Purchase orders{" "}
                <small>
                  {tasks
                    ? `${tasks.orders} draft or approved commitments`
                    : "Review planned purchases"}
                </small>{" "}
                ↗
              </button>
              <button
                className="focus-task"
                onClick={() => changeView("contracts")}
              >
                Contract evidence{" "}
                <small>
                  {counts.reviewed_contracts || 0} reviewed of{" "}
                  {counts.contracts || 0} optional documents
                </small>{" "}
                ↗
              </button>
            </article>
          </section>
        )}
      <details className="panel glass">
        <summary>Record inventory & coverage</summary>
        <div className="focus-kpis">
          {[
            {
              label: "Invoice records",
              n: counts.invoices || 0,
              v: "invoices",
            },
            {
              label: "Expense records",
              n: counts.expenses || 0,
              v: "expenses",
            },
            {
              label: "Contract documents",
              n: counts.contracts || 0,
              v: "contracts",
            },
          ].map((x) => (
            <button key={x.v} onClick={() => changeView(x.v as View)}>
              {x.label}: {x.n}
            </button>
          ))}
        </div>
        <p>
          Amounts describe imported records, not complete company accounts.
          Bills, purchase orders and payments are separate from attributed
          expenses. No profit is inferred from incomplete records.
        </p>
      </details>
    </div>
  );
}
