"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { MotionConfig, motion, useReducedMotion } from "framer-motion";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
import { ArrowRight } from "lucide-react";
import { sfx } from "../lib/sound";

gsap.registerPlugin(useGSAP);
const Experience = createContext({
  animate: false,
  ready: false,
  /** Plays the intro again, e.g. right after signing in. */
  play: () => {},
});
export const useExperience = () => useContext(Experience);
export const ease = [0.23, 1, 0.32, 1] as const;

// The intro plays on every page load and after signing in.
function Introduction({ done }: { done: () => void }) {
  const scope = useRef<HTMLDialogElement>(null);
  useGSAP(
    () => {
      const dialog = scope.current;
      if (!dialog) return;
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
        const frame = requestAnimationFrame(done);
        return () => cancelAnimationFrame(frame);
      }
      dialog.showModal();
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      // Three panes arrive out of depth with overlapping follow-through, the
      // bars rise with a small overshoot, and light sweeps across the glass.
      const timeline = gsap.timeline({ onComplete: done });
      sfx.intro();
      timeline
        .fromTo(
          ".intro-pane",
          { z: -520, y: 70, rotateX: 22, opacity: 0 },
          {
            z: (i: number) => [-90, -45, 0][i],
            x: (i: number) => [34, 17, 0][i],
            y: (i: number) => [-26, -13, 0][i],
            rotateX: 0,
            opacity: (i: number) => [0.45, 0.7, 1][i],
            duration: 1,
            stagger: 0.09,
            ease: "expo.out",
          },
          0,
        )
        .fromTo(
          ".intro-bar",
          { scaleY: 0 },
          {
            scaleY: 1,
            duration: 0.55,
            stagger: 0.08,
            ease: "back.out(1.7)",
            transformOrigin: "50% 100%",
          },
          0.55,
        )
        .fromTo(
          ".intro-sweep",
          { xPercent: -55 },
          { xPercent: 55, duration: 0.8, ease: "power2.inOut" },
          0.85,
        )
        .fromTo(
          ".intro-word",
          { y: 16, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.55, ease: "power3.out" },
          0.7,
        )
        .fromTo(
          ".intro-tagline",
          { opacity: 0 },
          { opacity: 1, duration: 0.4, ease: "power1.out" },
          0.95,
        )
        .to(
          ".intro-composition",
          { y: -10, opacity: 0, duration: 0.3, ease: "power2.in" },
          1.85,
        )
        .to(dialog, { opacity: 0, duration: 0.22 }, 2.0);
      const fallback = window.setTimeout(done, 3200);
      const preference = matchMedia("(prefers-reduced-motion: reduce)");
      const onPreference = () => {
        if (preference.matches) done();
      };
      preference.addEventListener("change", onPreference);
      return () => {
        window.clearTimeout(fallback);
        preference.removeEventListener("change", onPreference);
        document.body.style.overflow = previousOverflow;
        dialog.close();
      };
    },
    { scope, dependencies: [done] },
  );
  return (
    <dialog
      ref={scope}
      className="intro"
      aria-label="ProfitLens introduction"
      onCancel={done}
    >
      <div className="intro-spot" aria-hidden="true" />
      <div className="intro-composition">
        <div className="intro-stack" aria-hidden="true">
          <div className="intro-pane back glass" />
          <div className="intro-pane mid glass" />
          <div className="intro-pane front glass iris">
            <div className="intro-bars">
              <i className="intro-bar" />
              <i className="intro-bar" />
              <i className="intro-bar" />
            </div>
            <i className="intro-sweep" />
          </div>
        </div>
        <div className="intro-wordmark">
          <strong className="intro-word">
            Profit Lens<span className="intro-dot">.</span>
          </strong>
          <p className="intro-tagline">A clearer view starts here.</p>
        </div>
      </div>
      <button className="intro-skip" onClick={done} autoFocus>
        Skip intro <ArrowRight size={15} />
      </button>
    </dialog>
  );
}

export function ExperienceProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [intro, setIntro] = useState(true);
  const [keyboard, setKeyboard] = useState(false);
  const reduce = useReducedMotion();
  const done = useCallback(() => setIntro(false), []);
  const play = useCallback(() => {
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches) setIntro(true);
  }, []);
  useEffect(() => {
    // The specular rim follows the pointer across whichever pane it is over,
    // then glides back to the top corner when the pointer leaves.
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    let current: HTMLElement | null = null;
    let frame = 0;
    let event: PointerEvent | null = null;
    const apply = () => {
      frame = 0;
      if (!event) return;
      const target = event.target instanceof Element ? event.target : null;
      const pane = target?.closest<HTMLElement>(".glass") ?? null;
      if (current && current !== pane) {
        current.style.removeProperty("--mx");
        current.style.removeProperty("--my");
      }
      current = pane;
      if (!pane) return;
      const rect = pane.getBoundingClientRect();
      pane.style.setProperty(
        "--mx",
        `${(((event.clientX - rect.left) / rect.width) * 100).toFixed(1)}%`,
      );
      pane.style.setProperty(
        "--my",
        `${(((event.clientY - rect.top) / rect.height) * 100).toFixed(1)}%`,
      );
    };
    const move = (e: PointerEvent) => {
      event = e;
      if (!frame) frame = requestAnimationFrame(apply);
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => {
      window.removeEventListener("pointermove", move);
      cancelAnimationFrame(frame);
    };
  }, []);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (["Tab", "Enter", " ", "Escape"].includes(event.key)) {
        setKeyboard(true);
        document.documentElement.dataset.input = "keyboard";
      }
    };
    const pointer = () => {
      setKeyboard(false);
      document.documentElement.dataset.input = "pointer";
    };
    window.addEventListener("keydown", key, true);
    window.addEventListener("pointerdown", pointer, true);
    return () => {
      window.removeEventListener("keydown", key, true);
      window.removeEventListener("pointerdown", pointer, true);
    };
  }, []);
  return (
    <Experience.Provider
      value={{ animate: !reduce && !keyboard && !intro, ready: !intro, play }}
    >
      <MotionConfig reducedMotion="user" transition={{ duration: 0.22, ease }}>
        <div data-intro-ready={!intro} inert={intro}>
          {children}
        </div>
        {intro && <Introduction done={done} />}
      </MotionConfig>
    </Experience.Provider>
  );
}

export function PageTransition({
  children,
  identity,
}: {
  children: React.ReactNode;
  identity: string;
}) {
  const { animate } = useExperience();
  return (
    <motion.div
      key={identity}
      className="view-stack"
      initial={animate ? { opacity: 0, transform: "translateY(8px)" } : false}
      animate={{ opacity: 1, transform: "translateY(0px)" }}
      transition={{ duration: animate ? 0.22 : 0, ease }}
    >
      {children}
    </motion.div>
  );
}
