"use client";
import { useEffect, useState } from "react";
import { api, message } from "../lib/workspace";
import { Modal } from "./ui";

export type SourceEvidenceDetail = {
  fact: {
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
  raw: Record<string, unknown>;
  filename: string;
  sha256: string;
  mapping: {
    kind: string;
    columns: Record<string, string>;
    currency: string;
    date_format: string;
    decimal_format: string;
    amount_mode: string;
  };
  allocations: unknown[];
  can_download: boolean;
};

const display = (value: unknown): string =>
  value === null || value === undefined || value === ""
    ? "Unavailable"
    : typeof value === "object"
      ? JSON.stringify(value)
      : String(value);

export function SourceEvidenceBody({
  detail,
  base,
}: {
  detail: SourceEvidenceDetail;
  base: string;
}) {
  const { fact, raw, mapping } = detail;
  const original = (field: string) => display(raw[mapping.columns[field]]);
  const normalized: Record<string, unknown> = {
    amount: `${fact.currency} ${fact.amount}`,
    date: fact.occurred_on,
    description: fact.description,
    counterparty: fact.counterparty,
    customer_id: fact.customer_id,
    currency: fact.currency,
  };
  return (
    <div className="view-stack source-evidence-body">
      <p className="eyebrow">
        {fact.kind.replaceAll("_", " ")} · source record {fact.row_number}
      </p>
      <p>
        <strong>
          {fact.currency} {fact.amount}
        </strong>{" "}
        · {fact.occurred_on || "Date unavailable"}
      </p>
      <p>
        {fact.counterparty || "Counterparty not provided"}
        {fact.description ? ` · ${fact.description}` : ""}
      </p>
      <section>
        <h3>How this figure was obtained</h3>
        <p>
          {mapping.amount_mode === "quantity_price"
            ? `Original quantity ${original("quantity")} × original unit price ${original("unit_price")} → ${fact.currency} ${fact.amount}. Decimal arithmetic runs on the server; tax and cost are not inferred.`
            : mapping.amount_mode === "bank_columns"
              ? `Money received: ${original("credit")}; money paid: ${original("debit")}. The reviewed bank mapping classified this row as ${fact.kind.replaceAll("_", " ")}. This is a cash movement, not proof of revenue or expense.`
              : `Source amount ${original("amount")} → ${fact.currency} ${fact.amount}, using the reviewed ${mapping.decimal_format === "comma" ? "comma-decimal" : "dot-decimal"} convention. No missing costs or taxes are added.`}
        </p>
        <p className="footnote">
          Customer link:{" "}
          {fact.customer_id || "Unmatched — no customer relationship assumed"}.
          This source observation does not establish net profit.
        </p>
      </section>
      <section>
        <h3>Original values and reviewed interpretation</h3>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Original field</th>
                <th>Original value</th>
                <th>Used as</th>
                <th>Stored interpretation</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(raw).map(([column, value]) => {
                const targets = Object.entries(mapping.columns)
                  .filter(([, source]) => source === column)
                  .map(([target]) => target);
                return (
                  <tr key={column}>
                    <td
                      style={{ overflowWrap: "anywhere", whiteSpace: "normal" }}
                    >
                      {column}
                    </td>
                    <td
                      style={{
                        maxWidth: 260,
                        overflowWrap: "anywhere",
                        whiteSpace: "normal",
                      }}
                    >
                      {display(value)}
                    </td>
                    <td>
                      {targets.length
                        ? targets.map((t) => t.replaceAll("_", " ")).join(", ")
                        : "Preserved only"}
                    </td>
                    <td
                      style={{
                        maxWidth: 260,
                        overflowWrap: "anywhere",
                        whiteSpace: "normal",
                      }}
                    >
                      {targets.length
                        ? targets
                            .map((t) =>
                              t in normalized
                                ? display(normalized[t])
                                : "Calculation input / reference",
                            )
                            .join("; ")
                        : "Not used in calculations"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      {detail.can_download && (
        <a
          className="secondary"
          href={`/api${base}/sources/${fact.document_id}/file`}
        >
          Download unchanged original
        </a>
      )}
      {!detail.can_download && (
        <p className="footnote">
          Your role can inspect this authorized record; downloading the whole
          source file requires finance or administrator access.
        </p>
      )}
      <details>
        <summary>Technical provenance and allocation records</summary>
        <p style={{ overflowWrap: "anywhere" }}>SHA-256: {detail.sha256}</p>
        <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
          {JSON.stringify(
            { mapping, allocations: detail.allocations },
            null,
            2,
          )}
        </pre>
      </details>
    </div>
  );
}

export function SourceEvidence({
  base,
  factId,
  onClose,
}: {
  base: string;
  factId: string;
  onClose: () => void;
}) {
  const [result, setResult] = useState<{
    key: string;
    detail?: SourceEvidenceDetail;
    error?: string;
  } | null>(null);
  const key = `${base}/${factId}`;
  useEffect(() => {
    const controller = new AbortController();
    void api<SourceEvidenceDetail>(
      `${base}/facts/${encodeURIComponent(factId)}`,
      { signal: controller.signal },
    )
      .then((detail) => {
        if (!controller.signal.aborted) setResult({ key, detail });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setResult({ key, error: message(error) });
      });
    return () => controller.abort();
  }, [base, factId, key]);
  const current = result?.key === key ? result : null;
  return (
    <Modal
      heading={
        current?.detail
          ? `Evidence: ${current.detail.filename}`
          : "Source evidence"
      }
      close={onClose}
    >
      {!current && <p role="status">Loading authorized source evidence…</p>}
      {current?.error && (
        <p className="alert error" role="alert">
          {current.error}
        </p>
      )}
      {current?.detail && (
        <SourceEvidenceBody detail={current.detail} base={base} />
      )}
    </Modal>
  );
}
