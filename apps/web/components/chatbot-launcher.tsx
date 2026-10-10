"use client";

import Image from "next/image";
import { useEffect, useId, useRef, useState } from "react";
import { useExperience } from "./experience";

export function ChatbotLauncher() {
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  const messageId = useId();
  const { ready } = useExperience();

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", dismiss);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  if (!ready) return null;
  return (
    <div className="chatbot-launcher" ref={container}>
      <div id={messageId} className="chatbot-bubble" role="status">
        {open ? "Under development" : ""}
      </div>
      <button
        type="button"
        className="chatbot-button"
        aria-label="ProfitLens chatbot"
        aria-expanded={open}
        aria-controls={messageId}
        onClick={() => setOpen((value) => !value)}
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
