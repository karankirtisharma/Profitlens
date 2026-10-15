"use client";

import Image from "next/image";
import { useEffect, useId, useRef, useState } from "react";
import { ArrowUp, RotateCcw, X } from "lucide-react";
import { api, type RecordData } from "../lib/workspace";
import { useExperience } from "./experience";

export type ChatAction = {
  view:
    "finance" | "analysis" | "invoices" | "expenses" | "contracts" | "imports";
  label: string;
  customer_id?: string | null;
  billing_period?: string | null;
  record_id?: string | null;
};
function FormattedReply({ text }: { text: string }) {
  return (
    <div className="chat-formatted">
      {text
        .split("\n")
        .filter(Boolean)
        .map((line, i) => {
          const bullet = /^[-•]\s/.test(line);
          const content = line
            .replace(/^[-•]\s/, "")
            .split(/(\*\*[^*]+\*\*)/g)
            .map((part, j) =>
              part.startsWith("**") && part.endsWith("**") ? (
                <strong key={j}>{part.slice(2, -2)}</strong>
              ) : (
                part
              ),
            );
          return (
            <p key={i} className={bullet ? "chat-bullet" : undefined}>
              {bullet && <span aria-hidden="true">• </span>}
              {content}
            </p>
          );
        })}
    </div>
  );
}
type Reply = {
  scope_label?: string;
  actions?: ChatAction[];
  cards?: {
    label: string;
    value: string;
    tone: "positive" | "negative" | "warning" | "neutral";
  }[];
  reply: string;
  insufficient_evidence: boolean;
  billing_period: string | null;
  profitability_status: string;
  notice: string;
  sources: {
    source_id: string;
    filename: string;
    page: number;
    source_url: string;
    quote: string;
    evidence_status?: string;
  }[];
  findings: {
    id: string;
    rule: string;
    actual: string;
    expected: string;
    unit: string;
    limitation: string;
  }[];
  record_ids: { invoices: string[]; expenses: string[] };
};
type Message = { role: "user" | "assistant"; content: string; result?: Reply };

export function ChatbotLauncher({
  base,
  customers,
  onNavigate,
}: {
  base: string;
  customers: RecordData[];
  onNavigate?: (action: ChatAction) => void;
}) {
  const [open, setOpen] = useState(false);
  const [manual, setManual] = useState(false);
  const [customer, setCustomer] = useState("");
  const [month, setMonth] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Checking AI connection…");
  const trigger = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const transcript = useRef<HTMLDivElement>(null);
  const request = useRef<AbortController | null>(null);
  const messageId = useId();
  const { ready } = useExperience();

  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => {
    if (open && !pending) input.current?.focus();
  }, [open, pending]);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    input.current?.focus();
    void api<{ configured: boolean; model: string }>(`${base}/ai/status`, {
      signal: controller.signal,
    })
      .then((r) => {
        if (!controller.signal.aborted)
          setStatus(
            r.configured
              ? "AI configured · workspace evidence"
              : "AI setup required · no generated replies yet",
          );
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("AI connection unavailable");
      });
    const escape = (event: KeyboardEvent) => {
      if (
        event.key === "Escape" &&
        container.current?.contains(event.target as Node)
      ) {
        setOpen(false);
        trigger.current?.focus();
      }
    };
    document.addEventListener("keydown", escape);
    return () => {
      controller.abort();
      document.removeEventListener("keydown", escape);
    };
  }, [open, base]);
  useEffect(() => {
    const el = transcript.current;
    if (!el) return;
    const replies = el.querySelectorAll(".chat-assistant");
    const last = replies[replies.length - 1];
    if (!pending && messages.at(-1)?.role === "assistant" && last) {
      el.scrollTop +=
        last.getBoundingClientRect().top - el.getBoundingClientRect().top - 8;
    } else el.scrollTop = el.scrollHeight;
  }, [messages, pending, error, open]);

  function reset() {
    request.current?.abort();
    request.current = null;
    setMessages([]);
    setDraft("");
    setError("");
    setPending(false);
  }
  async function send() {
    const text = draft.trim();
    if (!text || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const previous = messages;
    setMessages([...previous, { role: "user", content: text }]);
    setDraft("");
    setPending(true);
    setError("");
    try {
      const result = await api<Reply>(`${base}/chat`, {
        method: "POST",
        signal: controller.signal,
        body: JSON.stringify({
          message: text,
          automatic: !manual,
          customer_id: manual ? customer || null : null,
          billing_period: manual ? month || null : null,
          history: previous.slice(-4).map(({ role, content, result }) => ({
            role,
            content:
              `${result ? `[Scope: ${result.scope_label || "selected customer"}; month: ${result.billing_period || "unspecified"}] ` : ""}${content}`.slice(
                0,
                3000,
              ),
          })),
        }),
      });
      if (!controller.signal.aborted)
        setMessages((items) => [
          ...items,
          { role: "assistant", content: result.reply, result },
        ]);
    } catch (e) {
      if (!controller.signal.aborted) {
        setMessages(previous);
        setDraft(text);
        setError(
          e instanceof Error ? e.message : "Could not send. Please retry.",
        );
      }
    } finally {
      if (request.current === controller) {
        request.current = null;
        setPending(false);
        input.current?.focus();
      }
    }
  }
  if (!ready) return null;
  return (
    <div className="chatbot-launcher" ref={container}>
      {open && (
        <section
          id={messageId}
          className="chatbot-bubble"
          aria-label="ProfitLens assistant"
        >
          <header className="chat-header">
            <div>
              <strong>Ask ProfitLens</strong>
              <small>{status}</small>
            </div>
            <button
              type="button"
              aria-label="New conversation"
              title="New conversation"
              onClick={reset}
            >
              <RotateCcw size={16} />
            </button>
            <button
              type="button"
              aria-label="Close chat"
              onClick={() => {
                setOpen(false);
                trigger.current?.focus();
              }}
            >
              <X size={18} />
            </button>
          </header>
          <div className="chat-scope-toggle">
            <span>
              {manual
                ? "Manual filters"
                : "Automatic · accessible workspace data"}
            </span>
            <button
              type="button"
              aria-pressed={manual}
              onClick={() => {
                reset();
                setManual(!manual);
              }}
            >
              {manual ? "Use automatic scope" : "Use manual filters"}
            </button>
          </div>
          {manual && (
            <div className="chat-context">
              <label>
                Customer
                <select
                  aria-label="Chat customer"
                  value={customer}
                  onChange={(e) => {
                    reset();
                    setCustomer(e.target.value);
                  }}
                >
                  <option value="">All accessible customers</option>
                  {customers.map((c) => (
                    <option key={c.customer_id} value={c.customer_id}>
                      {c.name || c.customer_id} · {c.customer_id}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Month
                <input
                  aria-label="Chat month"
                  type="month"
                  value={month}
                  onChange={(e) => {
                    reset();
                    setMonth(e.target.value);
                  }}
                />
              </label>
              <small>
                Blank month uses latest records. Changing context starts a new
                chat.
              </small>
            </div>
          )}
          <div
            className="chat-transcript"
            ref={transcript}
            role="log"
            aria-label="Chat messages"
            aria-live="polite"
            aria-relevant="additions"
          >
            {messages.length === 0 && (
              <div className="chat-welcome">
                <strong>Your data, in conversation.</strong>
                <p>
                  Ask about profitability, missing costs, invoices or contracts
                  across your accessible workspace. Mention a customer or month
                  naturally.
                </p>
                <p>
                  Try: “What should I review this month?” Then ask a follow-up.
                </p>
              </div>
            )}
            {messages.map((m, index) => (
              <article
                className={`chat-message chat-${m.role}`}
                key={index}
                aria-label={m.role === "user" ? "Your message" : "AI reply"}
              >
                <small>{m.role === "user" ? "You" : "ProfitLens AI"}</small>
                {m.role === "assistant" ? (
                  <FormattedReply text={m.content} />
                ) : (
                  <p>{m.content}</p>
                )}
                {m.result?.scope_label && (
                  <small className="chat-evidence-note">
                    {m.result.scope_label}
                  </small>
                )}
                {!!m.result?.cards?.length && (
                  <div className="chat-metric-grid">
                    {m.result.cards.map((card) => (
                      <div
                        key={card.label}
                        className={`chat-metric chat-tone-${card.tone}`}
                      >
                        <small>{card.label}</small>
                        <strong>{card.value}</strong>
                      </div>
                    ))}
                  </div>
                )}
                {!!m.result?.actions?.length && onNavigate && (
                  <div className="chat-actions" aria-label="Related records">
                    {m.result.actions.map((link, i) => (
                      <button
                        type="button"
                        key={i}
                        onClick={() => {
                          setOpen(false);
                          onNavigate(link);
                        }}
                      >
                        {link.label} <span aria-hidden="true">↗</span>
                      </button>
                    ))}
                  </div>
                )}
                {m.result && (
                  <>
                    {m.result.billing_period && (
                      <small className="chat-evidence-note">
                        {m.result.billing_period} · Financial data:{" "}
                        {m.result.profitability_status}
                      </small>
                    )}
                    {m.result.insufficient_evidence && (
                      <small className="chat-evidence-note">
                        Evidence is incomplete for this question.
                      </small>
                    )}
                    {(m.result.sources.length > 0 ||
                      m.result.record_ids.invoices.length > 0 ||
                      m.result.record_ids.expenses.length > 0 ||
                      m.result.findings.length > 0) && (
                      <details className="chat-sources">
                        <summary>View supporting records</summary>
                        {m.result.sources.map((s) => (
                          <div key={s.source_id}>
                            <a
                              href={s.source_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {s.filename} · page {s.page}
                            </a>
                            <blockquote>{s.quote}</blockquote>
                            {s.evidence_status && (
                              <small>
                                {s.evidence_status === "reviewed_period_match"
                                  ? "Reviewed · covers the selected month"
                                  : s.evidence_status === "unreviewed"
                                    ? "Unreviewed document · pricing not validated"
                                    : s.evidence_status ===
                                        "outside_selected_period"
                                      ? "Outside the selected month · reference only"
                                      : s.evidence_status ===
                                          "currency_mismatch"
                                        ? "Different currency · reference only"
                                        : "No reporting month selected · reference only"}
                              </small>
                            )}
                          </div>
                        ))}
                        {m.result.record_ids.invoices.length > 0 && (
                          <p>
                            Invoices: {m.result.record_ids.invoices.join(", ")}
                          </p>
                        )}
                        {m.result.record_ids.expenses.length > 0 && (
                          <p>
                            Expenses: {m.result.record_ids.expenses.join(", ")}
                          </p>
                        )}
                        {m.result.findings.map((f) => (
                          <p key={f.id}>
                            {f.rule.replaceAll("_", " ")}: actual {f.actual},
                            expected {f.expected} {f.unit}. {f.limitation}
                          </p>
                        ))}
                        <small>{m.result.notice}</small>
                      </details>
                    )}
                  </>
                )}
              </article>
            ))}
            {pending && (
              <p role="status" className="chat-thinking">
                Reading evidence and composing a reply…
              </p>
            )}
          </div>
          <form
            className="chat-compose"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            {error && (
              <p role="alert" className="chat-error">
                {error}
              </p>
            )}
            <div>
              <textarea
                ref={input}
                aria-label="Message ProfitLens"
                placeholder="Ask about your business data…"
                value={draft}
                rows={2}
                maxLength={1000}
                disabled={pending}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey &&
                    !e.nativeEvent.isComposing
                  ) {
                    e.preventDefault();
                    void send();
                  }
                }}
              />
              <button
                type="submit"
                className="primary"
                aria-label="Send message"
                disabled={pending || !draft.trim()}
              >
                <ArrowUp size={19} />
              </button>
            </div>
            <small>
              AI can make mistakes. Review sources. Chat stays in this session.
            </small>
          </form>
        </section>
      )}
      <button
        type="button"
        ref={trigger}
        className="chatbot-button"
        aria-label="ProfitLens chatbot"
        aria-expanded={open}
        aria-controls={open ? messageId : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        <Image
          src="/images/profitlens-bot.png"
          alt=""
          width={104}
          height={104}
          sizes="(max-width: 960px) 76px, 104px"
          draggable={false}
        />
      </button>
    </div>
  );
}
