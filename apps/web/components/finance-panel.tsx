"use client";

import type { Kind, RecordData } from "../lib/workspace";

type Source = { type?: string; filename?: string; row?: number };
type InvoiceLine = {
  id: string;
  subtotal: string | null;
  discount: string | null;
  refund: string | null;
  tax_excluded: string | null;
  payable_total: string | null;
  net_billed_revenue: string | null;
  reported_sales: string | null;
  source: Source;
};
type ExpenseLine = {
  id: string;
  category: string;
  amount: string;
  source: Source;
};
type FinancialItem = {
  customer_id: string;
  customer_name: string;
  reported_sales: string | null;
  billing_period: string;
  net_billed_revenue: string | null;
  attributed_cost: string | null;
  calculation_status: string;
  cost_completeness: string;
  invoice_lines: InvoiceLine[];
  expense_lines: ExpenseLine[];
  warnings: { code: string; message: string; record_id: string | null }[];
  contracts: {
    id: string;
    filename: string;
    state: string;
    source_page: number | null;
    effective_from: string | null;
    effective_to: string | null;
    full_month_match: boolean;
  }[];
};
export type FinancialReport = {
  billing_period: string | null;
  currency: string;
  total_customers: number;
  offset: number;
  limit: number;
  calculation_version: string;
  items: FinancialItem[];
};
// Format exact server strings without passing aggregate amounts through floating point.
const amount = (value: string | null, currency: string) =>
  value === null
    ? "Unavailable"
    : `${currency} ${value.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`;
const sourceLabel = (source: Source) =>
  source.type === "csv"
    ? `${source.filename} · row ${source.row}`
    : "Manually entered record";

export function FinancePanel({
  report,
  customers,
  period,
  customer,
  offset,
  onPeriod,
  onCustomer,
  onPage,
  openRecord,
  base,
}: {
  report: FinancialReport | null;
  customers: RecordData[];
  period: string;
  customer: string;
  offset: number;
  onPeriod: (value: string) => void;
  onCustomer: (value: string) => void;
  onPage: (value: number) => void;
  openRecord: (kind: Kind, customer: string, id: string) => void;
  base: string;
}) {
  return (
    <div className="view-stack finance-view">
      <section className="panel glass">
        <div className="form-grid">
          <label>
            Billing month
            <input
              type="month"
              value={period || report?.billing_period || ""}
              onChange={(e) => onPeriod(e.target.value)}
            />
          </label>
          <label>
            Customer
            <select
              aria-label="Customer"
              value={customer}
              onChange={(e) => onCustomer(e.target.value)}
            >
              <option value="">All accessible customers</option>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.name} · {c.customer_id}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="finance-note">
          Revenue = subtotal − discount − refund. Tax is excluded. Costs are the
          supplied customer-attributed amounts, on a tax-excluded basis. Missing
          records are not treated as zero.
        </p>
        <p className="finance-note">
          Recorded amounts only: review contribution, margin and discrepancies
          in Profitability & evidence. Reported sales with an unknown breakdown
          are excluded from net revenue and profit calculations. Contracts are
          optional.
        </p>
        {customers.length === 200 && (
          <p className="finance-note">
            The customer picker shows the first 200 customers. All accessible
            customers remain available through the report pages.
          </p>
        )}
      </section>
      {report && !report.billing_period && (
        <div className="empty">
          No billing records yet. Choose a month to inspect missing-data
          warnings, or import invoices and expenses.
        </div>
      )}
      {report?.billing_period && (
        <>
          <p className="muted">
            {report.billing_period} ·{" "}
            {report.items.length
              ? `${offset + 1}–${offset + report.items.length}`
              : "0"}{" "}
            of {report.total_customers} accessible customers ·{" "}
            {report.calculation_version}
          </p>
          {!report.items.length && (
            <div className="empty">
              No accessible customers match this selection.
            </div>
          )}
          {report.items.map((item) => (
            <article
              className="panel glass finance-customer"
              key={item.customer_id}
            >
              <div className="section-heading">
                <div>
                  <h2>{item.customer_name}</h2>
                  <p className="mono">
                    {item.customer_id} · {item.billing_period}
                  </p>
                </div>
                <span className="tag">
                  {item.calculation_status === "blocked"
                    ? "Needs correction"
                    : "Recorded amounts"}
                </span>
              </div>
              <dl className="finance-metrics">
                <div>
                  <dt>Net billed revenue</dt>
                  <dd>{amount(item.net_billed_revenue, report.currency)}</dd>
                </div>
                <div>
                  <dt>Recorded attributed costs</dt>
                  <dd>{amount(item.attributed_cost, report.currency)}</dd>
                </div>
              </dl>
              <p className="finance-note">
                {item.invoice_lines.length} validated invoice records ·{" "}
                {item.expense_lines.length} validated expense records · cost
                completeness unverified
              </p>
              <ul
                className="finance-warnings"
                aria-label={`Data quality for ${item.customer_id}`}
              >
                {item.warnings.map((w, i) => (
                  <li key={`${w.code}-${i}`}>
                    <strong>{w.code.replaceAll("_", " ")}</strong>
                    <span>
                      {w.record_id ? `${w.record_id}: ` : ""}
                      {w.message}
                    </span>
                  </li>
                ))}
              </ul>
              <details className="finance-sources">
                <summary>
                  Calculation and sources for {item.customer_id}
                </summary>
                <h3>Invoice calculation</h3>
                {item.reported_sales !== null && (
                  <p className="alert">
                    Reported sales:{" "}
                    {amount(item.reported_sales, report.currency)}. The
                    financial breakdown is unknown; this is not net revenue or
                    profit.
                  </p>
                )}
                <p className="finance-note">
                  Each line: subtotal − discount − refund = net billed revenue.
                  Tax is shown separately and is never subtracted again.
                </p>
                {item.invoice_lines.length ? (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Invoice / source</th>
                          <th>Subtotal</th>
                          <th>Discount</th>
                          <th>Refund</th>
                          <th>Excluded tax</th>
                          <th>Net revenue</th>
                          <th>Reported sales</th>
                        </tr>
                      </thead>
                      <tbody>
                        {item.invoice_lines.map((line) => (
                          <tr key={line.id}>
                            <td>
                              <button
                                className="text-button"
                                onClick={() =>
                                  openRecord(
                                    "invoices",
                                    item.customer_id,
                                    line.id,
                                  )
                                }
                              >
                                {line.id}
                              </button>
                              <div className="finance-note">
                                {sourceLabel(line.source)}
                              </div>
                            </td>
                            <td>{amount(line.subtotal, report.currency)}</td>
                            <td>{amount(line.discount, report.currency)}</td>
                            <td>{amount(line.refund, report.currency)}</td>
                            <td>
                              {amount(line.tax_excluded, report.currency)}
                            </td>
                            <td>
                              {amount(line.net_billed_revenue, report.currency)}
                            </td>
                            <td>
                              {amount(line.reported_sales, report.currency)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="finance-note">
                    No validated invoices for this month.
                  </p>
                )}
                <h3>Attributed expense inputs</h3>
                {item.expense_lines.length ? (
                  <ul className="finance-records">
                    {item.expense_lines.map((line) => (
                      <li key={line.id}>
                        <button
                          className="text-button"
                          onClick={() =>
                            openRecord("expenses", item.customer_id, line.id)
                          }
                        >
                          {line.id}
                        </button>
                        <span>
                          {line.category} ·{" "}
                          {amount(line.amount, report.currency)}
                        </span>
                        <span className="muted">
                          {sourceLabel(line.source)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="finance-note">
                    No validated costs for this month. Unavailable does not mean
                    zero.
                  </p>
                )}
                <h3>Contract evidence</h3>
                {item.contracts.length ? (
                  <ul className="finance-records">
                    {item.contracts.map((c) => (
                      <li key={c.id}>
                        <a
                          className="text-button"
                          href={`/api${base}/contracts/${encodeURIComponent(c.id)}/file`}
                        >
                          {c.filename}
                        </a>
                        <span>
                          {c.state === "reviewed"
                            ? `Reviewed · ${c.effective_from} to ${c.effective_to} · source page ${c.source_page}`
                            : "Awaiting manual review"}
                        </span>
                        <span className="muted">
                          {c.full_month_match
                            ? "Covers this complete month"
                            : "Not a full-month reviewed match"}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="finance-note">
                    No contract documents for this customer.
                  </p>
                )}
                <p className="finance-note">
                  Quality warnings identify missing or inconsistent evidence;
                  they do not prove a pricing anomaly. Partial months are not
                  prorated.
                </p>
              </details>
            </article>
          ))}
          <div className="table-footer">
            <button
              className="secondary"
              disabled={offset === 0}
              onClick={() => onPage(Math.max(0, offset - report.limit))}
            >
              Previous customers
            </button>
            <button
              className="secondary"
              disabled={offset + report.items.length >= report.total_customers}
              onClick={() => onPage(offset + report.limit)}
            >
              Next customers
            </button>
          </div>
        </>
      )}
    </div>
  );
}
