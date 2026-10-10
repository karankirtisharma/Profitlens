"use client";
import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useExperience } from "./experience";
import { X } from "lucide-react";
export function Logo() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      Profit Lens<span className="brand-dot">.</span>
    </span>
  );
}
export function Modal({
  heading,
  close,
  children,
}: {
  heading: string;
  close: () => void;
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
      onCancel={close}
      aria-label={heading}
      initial={
        animate
          ? { opacity: 0, transform: "translateY(8px) scale(0.98)" }
          : false
      }
      animate={{ opacity: 1, transform: "translateY(0px) scale(1)" }}
      transition={{ duration: animate ? 0.2 : 0 }}
    >
      <div className="modal-head">
        <h2>{heading}</h2>
        <button className="icon-btn" onClick={close} aria-label="Close">
          <X size={20} />
        </button>
      </div>
      {children}
    </motion.dialog>
  );
}
