import { Contract, RecordData, View } from "../lib/workspace";
export type OverviewData = {
  invoices: RecordData[];
  expenses: RecordData[];
  contracts: Contract[];
  summary?: {
    currency: string;
    source_series?: {
      period: string | null;
      kind: string;
      amount: string;
      records: number;
    }[];
    cost_series?: { period: string; amount: string }[];
    counts: Record<string, number>;
    record_months?: {
      billing_period: string;
      invoice_count: number;
      expense_count: number;
    }[];
    reported_count: number | null;
    reported_sales: string | null;
    verified_net_revenue: string | null;
    months: {
      billing_period: string;
      invoice_count: number;
      reported_count: number;
      reported_sales: string | null;
      verified_net_revenue: string | null;
    }[];
    top_reported_customers: {
      customer_id: string;
      reported_sales: string;
      invoice_count: number;
    }[];
  };
};
export type Props = {
  base: string;
  customers: RecordData[];
  data: OverviewData;
  canWrite: boolean;
  changeView: (view: View) => void;
};
