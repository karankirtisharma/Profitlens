"use client";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { View } from "../lib/workspace";
import { useExperience } from "./experience";

/*
  Navigation adapted from the 21st.dev "Animated Sidebar" by unlumen:
  a spring hover highlight and a shared active indicator, here a glass pill
  with an iridescent rim. Resizing, groups and the tick accents were left
  out; items stay buttons because views are client state, not routes.
*/
export type NavItem = { id: View; label: string; icon: LucideIcon };

export function SideNav({
  items,
  view,
  onSelect,
}: {
  items: NavItem[];
  view: View;
  onSelect: (view: View) => void;
}) {
  const { animate } = useExperience();
  const [hovered, setHovered] = useState<number | null>(null);
  return (
    <nav
      className="nav"
      aria-label="Workspace sections"
      onMouseLeave={() => setHovered(null)}
    >
      <AnimatePresence>
        {animate && hovered !== null && (
          <motion.span
            key="nav-hover"
            className="nav-hover"
            aria-hidden="true"
            initial={{ opacity: 0, transform: `translateY(${hovered}px)` }}
            animate={{ opacity: 1, transform: `translateY(${hovered}px)` }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 420, damping: 36 }}
          />
        )}
      </AnimatePresence>
      {items.map((item) => {
        const active = view === item.id;
        return (
          <div
            key={item.id}
            className={`nav-item ${active ? "is-active" : ""}`}
            onMouseEnter={(e) => setHovered(e.currentTarget.offsetTop)}
          >
            {active && (
              <motion.span
                layoutId="nav-active"
                className="nav-active"
                aria-hidden="true"
                transition={
                  animate
                    ? { type: "spring", stiffness: 700, damping: 42 }
                    : { duration: 0 }
                }
              />
            )}
            <button
              className="nav-btn"
              onClick={() => {
                if (!active) onSelect(item.id);
              }}
              aria-current={active ? "page" : undefined}
            >
              <item.icon size={17} strokeWidth={1.7} />
              {item.label}
            </button>
          </div>
        );
      })}
    </nav>
  );
}
