export type Workspace = {
  id: string;
  name: string;
  currency: string;
  role: string;
};
export type Account = {
  id: string;
  name: string;
  email: string;
  workspaces: Workspace[];
};
export type RecordData = {
  [key: string]: unknown;
  customer_id: string;
  name?: string;
  source?: { type: string; filename?: string; row?: number; batch_id?: string };
};
export type Contract = {
  id: string;
  customer_id: string;
  filename: string;
  state: string;
  pages: { page: number; text: string }[];
  effective_from: string | null;
  effective_to: string | null;
  monthly_rate: string | null;
  monthly_discount: string | null;
  source_page: number | null;
  currency: string | null;
  reviewed_at: string | null;
};
export type Batch = {
  id: string;
  kind: string;
  filename: string;
  state: string;
  row_count: number;
  issues: { source_row?: number; message: unknown }[];
  result: { inserted?: number; skipped?: number };
  preview_rows: { data: Record<string, string>; source_row: number }[];
};
export type Member = {
  id: string;
  name: string;
  email: string;
  role: string;
  customer_ids: string[];
};
export type Kind = "customers" | "invoices" | "expenses";
export type View = "overview" | Kind | "imports" | "contracts" | "team";
export const fields: Record<Kind, string[]> = {
  customers: ["customer_id", "name", "industry"],
  invoices: [
    "invoice_id",
    "customer_id",
    "billing_period",
    "currency",
    "subtotal",
    "discount",
    "tax",
    "refund",
    "total",
  ],
  expenses: [
    "expense_id",
    "customer_id",
    "billing_period",
    "category",
    "amount",
    "currency",
  ],
};
export const labels: Record<string, string> = {
  customer_id: "Customer ID",
  invoice_id: "Invoice ID",
  expense_id: "Expense ID",
  billing_period: "Billing month",
  subtotal: "Subtotal (before tax/discount)",
  total: "Invoice total",
  discount: "Discount",
  tax: "Tax",
  refund: "Refund",
  amount: "Expense amount",
  industry: "Industry",
  name: "Customer name",
  category: "Category",
  currency: "Currency",
};
export const title = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
export const message = (e: unknown) =>
  e instanceof Error ? e.message : String(e);
export function details(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(details).join(" · ");
  if (value && typeof value === "object") {
    const v = value as Record<string, unknown>;
    return `${v.field || (v.source_row && `Row ${v.source_row}`) || ""} ${details(v.message || v.msg || JSON.stringify(v))}`.trim();
  }
  return String(value);
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!res.ok) {
    let text = `Request failed (${res.status})`;
    try {
      text = details((await res.json()).detail);
    } catch {}
    throw new Error(text);
  }
  return res.json();
}
