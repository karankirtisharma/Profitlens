"use client";
import { useEffect, useRef, useSyncExternalStore } from "react";
import { motion } from "framer-motion";
import { useExperience } from "./experience";
import { FileSpreadsheet, Moon, Sun, Volume2, VolumeX, X } from "lucide-react";
import {
  SOUND_EVENT,
  playToggle,
  setSoundEnabled,
  sfx,
  soundEnabled,
} from "../lib/sound";
export function Logo() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span>
        Profit Lens<span className="brand-dot">.</span>
      </span>
    </span>
  );
}

const THEME_KEY = "profitlens.theme";
const darkQuery = "(prefers-color-scheme: dark)";
function subscribeTheme(callback: () => void) {
  const media = matchMedia(darkQuery);
  media.addEventListener("change", callback);
  window.addEventListener(THEME_KEY, callback);
  return () => {
    media.removeEventListener("change", callback);
    window.removeEventListener(THEME_KEY, callback);
  };
}
const currentTheme = () =>
  document.documentElement.dataset.theme ||
  (matchMedia(darkQuery).matches ? "dark" : "light");

export function ThemeToggle() {
  const theme = useSyncExternalStore(
    subscribeTheme,
    currentTheme,
    () => "light",
  );
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      className="chip-btn square"
      onClick={() => {
        document.documentElement.dataset.theme = next;
        sfx.tap();
        try {
          localStorage.setItem(THEME_KEY, next);
        } catch {
          /* The choice still applies for this page view. */
        }
        window.dispatchEvent(new Event(THEME_KEY));
      }}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
    >
      {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
    </button>
  );
}

function subscribeSound(callback: () => void) {
  window.addEventListener(SOUND_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(SOUND_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

export function SoundToggle() {
  const on = useSyncExternalStore(subscribeSound, soundEnabled, () => false);
  return (
    <button
      className="chip-btn square"
      onClick={() => {
        setSoundEnabled(!on);
        playToggle(!on);
      }}
      aria-label="Sound effects"
      aria-pressed={on}
      title={on ? "Sound effects on" : "Sound effects off"}
    >
      {on ? <Volume2 size={15} /> : <VolumeX size={15} />}
    </button>
  );
}

export function Modal({
  heading,
  close,
  source,
  children,
}: {
  heading: string;
  close: () => void;
  /** Where the record came from, shown on a pane behind the dialog. */
  source?: { label: string; detail?: string };
  children: React.ReactNode;
}) {
  const { animate } = useExperience();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    const opener =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    dialog?.showModal();
    sfx.open();
    return () => {
      dialog?.close();
      queueMicrotask(() => {
        if (opener?.isConnected) opener.focus({ preventScroll: true });
      });
    };
  }, []);
  return (
    <motion.dialog
      ref={ref}
      className="modal glass"
      onCancel={close}
      aria-label={heading}
      initial={
        animate
          ? { opacity: 0, transform: "translateY(10px) scale(0.97)" }
          : false
      }
      animate={{ opacity: 1, transform: "translateY(0px) scale(1)" }}
      transition={{ duration: animate ? 0.24 : 0 }}
    >
      {source && (
        <p className="modal-source">
          <FileSpreadsheet size={13} aria-hidden="true" />
          <span>{source.label}</span>
          {source.detail && <span className="detail">{source.detail}</span>}
        </p>
      )}
      <div className="modal-scroll">
        <div className="modal-head">
          <h2>{heading}</h2>
          <button className="icon-btn" onClick={close} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </motion.dialog>
  );
}
