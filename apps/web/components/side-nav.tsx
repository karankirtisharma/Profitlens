"use client";

import { useId, useRef, useState } from "react";
import { Search, X, type LucideIcon } from "lucide-react";
import type { View } from "../lib/workspace";
import styles from "./side-nav.module.css";

export type NavItem = {
  id: View;
  label: string;
  icon: LucideIcon;
  group?: string;
  keywords?: string;
};

const sections: Partial<Record<View, { group: string; keywords: string }>> = {
  overview: { group: "Workspace", keywords: "home dashboard activity summary" },
  data: {
    group: "Workspace",
    keywords:
      "sources sales spending banking monthly review reports files upload",
  },
  customers: { group: "Business records", keywords: "sales contacts clients" },
  invoices: { group: "Business records", keywords: "sales billing revenue" },
  expenses: { group: "Business records", keywords: "purchases costs spending" },
  finance: {
    group: "Review & evidence",
    keywords: "reports revenue expenses costs calculations",
  },
  analysis: {
    group: "Review & evidence",
    keywords: "reports profit margin contribution investigation ai",
  },
  contracts: {
    group: "Review & evidence",
    keywords: "documents pdf agreements terms",
  },
  imports: {
    group: "Review & evidence",
    keywords: "upload csv records history preview",
  },
  team: {
    group: "Administration",
    keywords: "settings users roles permissions access",
  },
};

export function SideNav({
  items,
  view,
  onSelect,
}: {
  items: NavItem[];
  view: View;
  onSelect: (view: View) => void;
}) {
  const searchId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const matches = items.filter((item) => {
    const source =
      `${item.label} ${item.group ?? sections[item.id]?.group ?? "Workspace"} ${item.keywords ?? ""} ${sections[item.id]?.keywords ?? ""}`.toLocaleLowerCase();
    return words.every((word) => source.includes(word));
  });
  const groups = new Map<string, NavItem[]>();
  for (const item of matches) {
    const group = item.group ?? sections[item.id]?.group ?? "Workspace";
    groups.set(group, [...(groups.get(group) ?? []), item]);
  }
  const select = (next: View) => {
    setQuery("");
    if (view !== next) onSelect(next);
  };
  return (
    <nav className={`nav ${styles.navigation}`} aria-label="Workspace sections">
      <div className={styles.search}>
        <Search size={15} aria-hidden="true" />
        <label className={styles.srOnly} htmlFor={searchId}>
          Find a section
        </label>
        <input
          ref={input}
          id={searchId}
          type="search"
          placeholder="Find a section…"
          value={query}
          autoComplete="off"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape") setQuery("");
            if (event.key === "Enter" && matches.length === 1) {
              event.preventDefault();
              select(matches[0].id);
            }
          }}
        />
        {query && (
          <button
            type="button"
            aria-label="Clear section search"
            onClick={() => {
              setQuery("");
              input.current?.focus();
            }}
          >
            <X size={14} aria-hidden="true" />
          </button>
        )}
      </div>
      <div className={styles.groups}>
        {[...groups].map(([group, entries]) => (
          <div
            key={group}
            className={styles.group}
            role="group"
            aria-label={`${group} navigation`}
          >
            <div className={styles.heading} aria-hidden="true">
              {group}
            </div>
            {entries.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`${styles.item} ${view === item.id ? styles.active : ""}`}
                aria-current={view === item.id ? "page" : undefined}
                onClick={() => select(item.id)}
              >
                <item.icon size={17} strokeWidth={1.7} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        ))}
      </div>
      {query && (
        <p className={styles.result} role="status">
          {matches.length
            ? `${matches.length} section${matches.length === 1 ? "" : "s"} found`
            : "No matching sections. Try invoices, documents or reports."}
        </p>
      )}
    </nav>
  );
}
