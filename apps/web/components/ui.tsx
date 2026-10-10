"use client";
import { useEffect, useRef } from "react";
import { X } from "lucide-react";
export function Logo() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <span />
        <span />
        <span />
      </span>
      ProfitLens<span className="brand-dot">.</span>
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
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog ref={ref} onCancel={close} aria-label={heading}>
      <div className="modal-head">
        <h2>{heading}</h2>
        <button className="icon-btn" onClick={close} aria-label="Close">
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
