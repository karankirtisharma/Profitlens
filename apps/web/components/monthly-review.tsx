"use client";

import { useEffect, useRef, useState } from "react";
import { api, message } from "../lib/workspace";

export type ReviewFilters = {
  start?: string;
  end?: string;
  kind?: string;
  customer_id?: string;
  counterparty?: string;
  currency?: string;
};

type PeriodTotal = { amount: string | null; count: number; source_url: string };
type Review = {
  period: string;
  previous_period: string;
  kind: string;
  currency: string;
  current: PeriodTotal;
  previous: PeriodTotal;
  comparable: boolean;
  change: string | null;
  drivers: {
    counterparty: string;
    label: string;
    status: "comparable" | "current_only" | "previous_only";
    current: string | null;
    previous: string | null;
    change: string | null;
    current_count: number;
    previous_count: number;
    current_source_url: string;
    previous_source_url: string;
  }[];
  driver_group_count: number;
  missing_dates: number;
  unknown_counterparty_records: number;
  current_month_incomplete: boolean;
  notice: string;
  review_prompts: string[];
};

const meanings = {
  expenditure: "Spending recorded",
  reported_sales: "Sales reported",
  cash_inflow: "Money received",
  cash_outflow: "Money paid",
};
type Meaning = keyof typeof meanings;
const money = (amount: string | null, currency: string) =>
  amount === null ? "No records — unavailable" : `${currency} ${amount}`;

export function MonthlyReview({
  base,
  initialPeriod,
  customerId,
  onInspect,
}: {
  base: string;
  initialPeriod?: string;
  customerId?: string;
  onInspect: (filters: ReviewFilters) => void;
}) {
  const [chosenPeriod, setChosenPeriod] = useState<string | null>(null);
  const [kind, setKind] = useState<Meaning>("expenditure");
  const [result, setResult] = useState<{
    key: string;
    data?: Review;
    error?: string;
  } | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const period = chosenPeriod ?? initialPeriod ?? "";
  const params = new URLSearchParams({ period, kind });
  if (customerId) params.set("customer_id", customerId);
  const requestKey = `${base}/source-review?${params}`;
  const current = result?.key === requestKey ? result : null;
  const review = current?.data;
  const busy = pending === requestKey;
  useEffect(() => () => controller.current?.abort(), []);

  async function run() {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setPending(requestKey);
    setResult(null);
    try {
      const data = await api<Review>(requestKey, { signal: request.signal });
      if (!request.signal.aborted) setResult({ key: requestKey, data });
    } catch (error) {
      if (!request.signal.aborted)
        setResult({ key: requestKey, error: message(error) });
    } finally {
      if (!request.signal.aborted) setPending(null);
    }
  }

  function inspect(sourceUrl: string) {
    const url = new URL(sourceUrl, "https://profitlens.invalid");
    if (
      url.origin !== "https://profitlens.invalid" ||
      url.pathname !== `/api${base}/facts`
    )
      return;
    const filters: ReviewFilters = {};
    for (const key of [
      "start",
      "end",
      "kind",
      "customer_id",
      "counterparty",
      "currency",
    ] as const) {
      if (url.searchParams.has(key)) filters[key] = url.searchParams.get(key)!;
    }
    onInspect(filters);
  }

  return (
    <section className="panel glass" aria-labelledby="monthly-review-heading">
      <p className="eyebrow">Understand the change. Inspect the evidence.</p>
      <h2 id="monthly-review-heading">Monthly business review</h2>
      <p>
        Compare a recorded month with the previous month and see which named
        counterparties changed. This reviews your imported records; it does not
        assume they cover the whole business.
      </p>
      <p className="footnote">
        This review uses all source records your role can access in this
        workspace{customerId ? ` for customer ${customerId}` : ""}. The table’s
        active date, type and counterparty filters do not change it; choose the
        month and data type here.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void run();
        }}
      >
        <div className="form-grid">
          <label>
            Review month
            <input
              aria-label="Review month"
              type="month"
              required
              value={period}
              onChange={(event) => setChosenPeriod(event.target.value)}
            />
          </label>
          <label>
            Review data
            <select
              aria-label="Review data"
              value={kind}
              onChange={(event) => setKind(event.target.value as Meaning)}
            >
              {Object.entries(meanings).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {customerId && (
          <p className="footnote">
            Scoped to customer {customerId} and your access permissions.
          </p>
        )}
        <button className="primary" disabled={!period || busy}>
          {busy ? "Reviewing records…" : "Run review"}
        </button>
      </form>
      {busy && <p role="status">Comparing authorized source records…</p>}
      {current?.error && (
        <p className="alert error" role="alert">
          {current.error}
        </p>
      )}
      {review && (
        <div className="view-stack" style={{ marginTop: 24 }}>
          <div className="form-grid">
            <article>
              <h3>{review.previous_period} · previous</h3>
              <p>
                <strong>
                  {money(review.previous.amount, review.currency)}
                </strong>
              </p>
              <p>{review.previous.count} records</p>
              {review.previous.count > 0 && (
                <button
                  className="text-button"
                  onClick={() => inspect(review.previous.source_url)}
                >
                  Inspect previous month
                </button>
              )}
            </article>
            <article>
              <h3>{review.period} · selected</h3>
              <p>
                <strong>{money(review.current.amount, review.currency)}</strong>
              </p>
              <p>{review.current.count} records</p>
              {review.current.count > 0 && (
                <button
                  className="text-button"
                  onClick={() => inspect(review.current.source_url)}
                >
                  Inspect selected month
                </button>
              )}
            </article>
            <article>
              <h3>Change in recorded amounts</h3>
              <p>
                <strong>
                  {review.comparable && review.change !== null
                    ? `${review.currency} ${review.change}`
                    : "Comparison unavailable"}
                </strong>
              </p>
              <p className="footnote">
                A change is not automatically a saving, loss or anomaly.
              </p>
            </article>
          </div>
          <p className="alert">{review.notice}</p>
          {review.current_month_incomplete && (
            <p className="alert">
              The selected calendar month has not ended. It may be a future or
              partial period; do not treat its records as a completed month.
            </p>
          )}
          {review.missing_dates > 0 && (
            <p className="footnote">
              {review.missing_dates} accessible records of this type have no
              date and cannot be placed in either month.
            </p>
          )}
          {review.unknown_counterparty_records > 0 && (
            <p className="footnote">
              {review.unknown_counterparty_records} records in this comparison
              have no counterparty. They remain an unnamed group, not an
              invented business relationship.
            </p>
          )}
          <section>
            <h3>Where the recorded change comes from</h3>
            <p className="footnote">
              Exact source names only; similar names are not merged. Showing{" "}
              {review.drivers.length} of {review.driver_group_count} groups.
              These are review prompts, not proof of a business cause.
            </p>
            {review.drivers.length === 0 ? (
              <p>
                No dated records to compare for these months and this data type.
                Try another month or import the relevant records.
              </p>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Counterparty</th>
                      <th>Previous month</th>
                      <th>Selected month</th>
                      <th>Change / review</th>
                      <th>Evidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {review.drivers.map((driver) => (
                      <tr key={driver.counterparty}>
                        <td
                          style={{
                            whiteSpace: "normal",
                            overflowWrap: "anywhere",
                            maxWidth: 240,
                          }}
                        >
                          {driver.label}
                        </td>
                        <td>{money(driver.previous, review.currency)}</td>
                        <td>{money(driver.current, review.currency)}</td>
                        <td style={{ whiteSpace: "normal", maxWidth: 260 }}>
                          {driver.change === null
                            ? "Not comparable"
                            : `${review.currency} ${driver.change}`}
                          <small>
                            {driver.status === "current_only"
                              ? "Only in selected-month records. Check earlier coverage before calling this new spending or sales."
                              : driver.status === "previous_only"
                                ? "Only in previous-month records. Missing records do not prove activity stopped."
                                : "Inspect the supporting records and check price, quantity, timing or category changes."}
                          </small>
                        </td>
                        <td>
                          {driver.current_count > 0 && (
                            <button
                              className="text-button"
                              aria-label={`Inspect selected records for ${driver.label}`}
                              onClick={() => inspect(driver.current_source_url)}
                            >
                              Selected records ↗
                            </button>
                          )}
                          {driver.previous_count > 0 && (
                            <button
                              className="text-button"
                              aria-label={`Inspect previous records for ${driver.label}`}
                              onClick={() =>
                                inspect(driver.previous_source_url)
                              }
                            >
                              Previous records ↗
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
          {review.review_prompts.length > 0 && (
            <section>
              <h3>Questions worth checking</h3>
              <ul>
                {review.review_prompts.map((prompt) => (
                  <li key={prompt}>{prompt}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </section>
  );
}
