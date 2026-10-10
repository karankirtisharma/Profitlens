"use client";
import { useRef, useState, FormEvent } from "react";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  FileSpreadsheet,
  FileText,
  LockKeyhole,
  LoaderCircle,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { Logo, SoundToggle, ThemeToggle } from "./ui";
import { useExperience } from "./experience";
import { AnimatedInput } from "./animated-input";

gsap.registerPlugin(useGSAP);

// Synthetic records shaped like the demo fixtures in data/demo.
const ROWS: [string, string, string, string, string, string][] = [
  ["2", "I001", "Northstar Studio", "11,210", ".00", "2026-09"],
  ["3", "I002", "Harbor Retail", "9,440", ".00", "2026-09"],
  ["4", "BAD-1", "Northstar Studio", "99", ".00", "2026-09"],
  ["5", "I004", "Harbor Retail", "9,440", ".00", "2026-10"],
  ["6", "I005", "Northstar Studio", "11,210", ".00", "2026-10"],
];
// How far each pane drifts with the pointer: the farther back, the more it moves.
const DEPTH = { contract: 22, ledger: 12, signin: -3 };

export function Login({
  login,
  busy,
  error,
}: {
  login: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  busy: boolean;
  error: string;
}) {
  const [visible, setVisible] = useState(false);
  const { ready, animate } = useExperience();
  const stage = useRef<HTMLDivElement>(null);
  useGSAP(
    () => {
      if (!ready || !animate) return;
      // Panes arrive from depth, back to front, each overlapping the last.
      gsap.from(".depth-pane", {
        scale: 0.94,
        y: 36,
        opacity: 0,
        duration: 1.1,
        stagger: 0.12,
        ease: "expo.out",
        clearProps: "scale",
      });
      const panes = (["contract", "ledger", "signin"] as const).map((name) => ({
        x: gsap.quickTo(`.depth-pane.${name}`, "x", {
          duration: 0.9,
          ease: "power3",
        }),
        y: gsap.quickTo(`.depth-pane.${name}`, "y", {
          duration: 0.9,
          ease: "power3",
        }),
        depth: DEPTH[name],
      }));
      const move = (e: PointerEvent) => {
        const nx = e.clientX / window.innerWidth - 0.5;
        const ny = e.clientY / window.innerHeight - 0.5;
        for (const pane of panes) {
          pane.x(nx * pane.depth);
          pane.y(ny * pane.depth * 0.7);
        }
      };
      if (matchMedia("(hover: hover) and (pointer: fine)").matches)
        window.addEventListener("pointermove", move, { passive: true });
      return () => window.removeEventListener("pointermove", move);
    },
    { scope: stage, dependencies: [ready, animate], revertOnUpdate: true },
  );
  return (
    <main className="login">
      <header className="login-top">
        <Logo />
        <div className="login-top-actions">
          <SoundToggle />
          <ThemeToggle />
        </div>
      </header>
      <div className="login-copy">
        <h1>
          See the source
          <br />
          <span>behind every figure.</span>
        </h1>
        <p>
          Customers, invoices, expenses and contracts in one scoped workspace.
          Every number traces back to its CSV row or PDF page.
        </p>
      </div>
      <div className="pane-stage" ref={stage}>
        <div className="pane-stack">
          <div className="depth-pane contract glass" aria-hidden="true">
            <div className="pane-label">
              <span>
                <FileText size={14} />
                contract_C001.pdf
              </span>
              Page 1
            </div>
            <div className="doc-term">
              Monthly rate
              <b>
                INR 10,000<span className="cents">.00</span>
              </b>
            </div>
            <div className="doc-lines">
              <i style={{ width: "72%" }} />
              <i style={{ width: "90%" }} />
              <i style={{ width: "64%" }} />
              <i style={{ width: "84%" }} />
            </div>
          </div>
          <div className="depth-pane ledger glass" aria-hidden="true">
            <div className="pane-label">
              <span>
                <FileSpreadsheet size={14} />
                invoices.csv
              </span>
              INR
            </div>
            <div className="ledger-grid">
              <div className="ledger-row th">
                <span>Row</span>
                <span>Invoice</span>
                <span className="num">Total</span>
                <span>Customer</span>
                <span className="hide-sm">Month</span>
              </div>
              {ROWS.map(([row, id, customer, whole, cents, month]) => (
                <div
                  className={`ledger-row ${id === "BAD-1" ? "flag" : ""}`}
                  key={id}
                >
                  <span className="mono src">{row}</span>
                  <span className="mono">{id}</span>
                  <span className="num">
                    {whole}
                    <span className="cents">{cents}</span>
                  </span>
                  <span>{customer}</span>
                  <span className="mono hide-sm">{month}</span>
                </div>
              ))}
            </div>
          </div>
          <section
            className="depth-pane signin glass iris"
            aria-labelledby="login-title"
          >
            <h2 id="login-title">Sign in to your workspace</h2>
            <p>Your business records, all in one place.</p>
            <form className="login-form" onSubmit={login}>
              <div className="field">
                <label htmlFor="login-email">Email address</label>
                <div className="input-icon">
                  <Mail size={16} />
                  <AnimatedInput
                    id="login-email"
                    name="email"
                    type="email"
                    autoComplete="username"
                    placeholder="you@company.com"
                    required
                  />
                </div>
              </div>
              <div className="field">
                <div className="field-head">
                  <label htmlFor="login-password">Password</label>
                  <span>Provisioned account</span>
                </div>
                <div className="input-icon">
                  <LockKeyhole size={16} />
                  <AnimatedInput
                    id="login-password"
                    name="password"
                    type={visible ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    required
                    minLength={1}
                  />
                  <button
                    className="password-toggle"
                    type="button"
                    onClick={() => setVisible(!visible)}
                    aria-label={visible ? "Hide password" : "Show password"}
                    aria-pressed={visible}
                  >
                    {visible ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>
              {error && (
                <div role="alert" className="alert error">
                  {error}
                </div>
              )}
              <button className="primary login-submit" disabled={busy}>
                <span>{busy ? "Signing in…" : "Sign in"}</span>
                <span className="cta-nub" aria-hidden="true">
                  {busy ? (
                    <LoaderCircle className="spinner" size={15} />
                  ) : (
                    <ArrowRight size={15} />
                  )}
                </span>
              </button>
            </form>
            <div className="login-note">
              <ShieldCheck size={16} />
              <p>
                <strong>Access is limited to your organization.</strong>
                Need an account? Your project administrator provisions access.
              </p>
            </div>
          </section>
        </div>
      </div>
      <footer className="login-foot">
        <span>Week 3 · Business data foundation</span>
        <span>Background panes show synthetic sample records.</span>
      </footer>
    </main>
  );
}
