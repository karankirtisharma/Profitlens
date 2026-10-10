"use client";
import { useRef, useState, FormEvent } from "react";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Check,
  Database,
  Eye,
  EyeOff,
  FileCheck2,
  LockKeyhole,
  Mail,
  ShieldCheck,
  LoaderCircle,
} from "lucide-react";
import { Logo } from "./ui";
import { ReplayIntro, useExperience } from "./experience";

gsap.registerPlugin(useGSAP);

function GlassSculpture() {
  const scope = useRef<HTMLDivElement>(null);
  const { ready } = useExperience();
  const reduce = useReducedMotion();
  useGSAP(
    () => {
      if (!ready || reduce) return;
      gsap.fromTo(
        ".glass-tile",
        { y: 18, opacity: 0.3 },
        { y: 0, opacity: 1, stagger: 0.09, duration: 0.9, ease: "power3.out" },
      );
    },
    { scope, dependencies: [ready, reduce], revertOnUpdate: true },
  );
  return (
    <div className="glass-sculpture" ref={scope} aria-hidden="true">
      <div className="sculpture-orbit" />
      <div className="glass-tile tile-back">
        <svg viewBox="0 0 100 60">
          <path d="M8 49L29 28L49 36L71 12L90 18M76 13L90 18L85 31" />
        </svg>
      </div>
      <div className="glass-tile tile-left">
        <ArrowRight size={36} strokeWidth={1.2} />
      </div>
      <div className="glass-tile tile-main">
        <span className="sculpture-bars">
          <i />
          <i />
          <i />
        </span>
        <span className="tile-caption">CLARITY, CONNECTED.</span>
      </div>
      <div className="glass-tile tile-right">
        <span className="lens-ring">
          <span />
          <i />
        </span>
      </div>
      <span className="sculpture-glint" />
    </div>
  );
}

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
  const { animate } = useExperience();
  return (
    <main className="login-page">
      <div className="glass-ribbon ribbon-one" aria-hidden="true" />
      <div className="glass-ribbon ribbon-two" aria-hidden="true" />
      <header className="login-header flex items-center justify-between gap-4">
        <Logo />
        <div className="flex items-center gap-5">
          <ReplayIntro />
          <span className="release-label">WORKSPACE / 03</span>
        </div>
      </header>
      <div className="login-layout">
        <section className="login-story">
          <GlassSculpture />
          <div className="story-copy">
            <span className="eyebrow">
              The foundation of a clearer business
            </span>
            <h1>
              Every record.
              <br />
              One perspective.
              <br />
              <span>More clarity.</span>
            </h1>
            <p>
              Bring your customers, business records and contract evidence into
              focus.
            </p>
          </div>
          <div className="login-capabilities">
            <div>
              <span>
                <Database size={20} strokeWidth={1.5} />
              </span>
              <p>
                Connected
                <br />
                records
              </p>
            </div>
            <div>
              <span>
                <FileCheck2 size={20} strokeWidth={1.5} />
              </span>
              <p>
                Verified
                <br />
                imports
              </p>
            </div>
            <div>
              <span>
                <ShieldCheck size={20} strokeWidth={1.5} />
              </span>
              <p>
                Scoped
                <br />
                access
              </p>
            </div>
          </div>
        </section>
        <section className="login-form" aria-labelledby="login-title">
          <div className="login-card glass-panel">
            <div className="login-card-top flex items-center justify-between">
              <span className="login-lock">
                <LockKeyhole size={20} strokeWidth={1.5} />
              </span>
              <span className="micro-label">
                <i /> PRIVATE WORKSPACE
              </span>
            </div>
            <span className="eyebrow">Welcome back</span>
            <h2 id="login-title">Sign in to your workspace</h2>
            <p className="muted">Your business records. All in one place.</p>
            <form onSubmit={login}>
              <label htmlFor="login-email">Email address</label>
              <div className="input-icon">
                <Mail size={19} />
                <input
                  id="login-email"
                  name="email"
                  type="email"
                  autoComplete="username"
                  placeholder="you@company.com"
                  required
                />
              </div>
              <div className="password-label">
                <label htmlFor="login-password">Password</label>
                <span>Provisioned account</span>
              </div>
              <div className="input-icon">
                <LockKeyhole size={18} />
                <input
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
                  {visible ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
              {error && (
                <div role="alert" className="alert error">
                  {error}
                </div>
              )}
              <motion.button
                className="primary login-submit"
                disabled={busy}
                whileTap={animate ? { transform: "scale(0.98)" } : undefined}
              >
                <span>{busy ? "Signing in…" : "Sign in"}</span>
                {busy ? (
                  <LoaderCircle className="spinner" size={18} />
                ) : (
                  <ArrowRight size={19} />
                )}
              </motion.button>
            </form>
            <div className="login-assurance">
              <Check size={14} />
              <span>Access is limited to your organization.</span>
            </div>
            <div className="login-help">
              <span>Need workspace access?</span>
              <p>
                Contact your project administrator to get a provisioned account.
              </p>
            </div>
          </div>
          <p className="login-edition">
            <span /> WEEK 3 DEMO <i /> Business data foundation
          </p>
        </section>
      </div>
      <footer className="login-footer">
        <span>
          PROFIT LENS <i> / </i> A CLEARER VIEW STARTS HERE
        </span>
        <span>Customers · Invoices · Expenses · Contracts</span>
      </footer>
    </main>
  );
}
