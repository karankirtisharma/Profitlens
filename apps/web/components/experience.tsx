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
import { Play, ArrowRight } from "lucide-react";

gsap.registerPlugin(useGSAP);
const INTRO_KEY = "profitlens.intro.v1";
const Experience = createContext({
  animate: false,
  ready: false,
  replay: () => {},
});
export const useExperience = () => useContext(Experience);
export const ease = [0.23, 1, 0.32, 1] as const;

function Introduction({ done, replay }: { done: () => void; replay: boolean }) {
  const scope = useRef<HTMLDialogElement>(null);
  useGSAP(
    () => {
      const dialog = scope.current;
      if (!dialog) return;
      let seen = false;
      try {
        seen = sessionStorage.getItem(INTRO_KEY) === "seen";
      } catch {
        /* Storage is optional. */
      }
      if (
        matchMedia("(prefers-reduced-motion: reduce)").matches ||
        (seen && !replay)
      ) {
        const frame = requestAnimationFrame(done);
        return () => cancelAnimationFrame(frame);
      }
      dialog.showModal();
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      const timeline = gsap.timeline({ onComplete: done });
      timeline
        .fromTo(
          ".intro-bar",
          { scaleY: 0, opacity: 0 },
          {
            scaleY: 1,
            opacity: 1,
            duration: 0.65,
            stagger: 0.13,
            ease: "power3.out",
            transformOrigin: "50% 100%",
          },
          0.1,
        )
        .fromTo(
          ".intro-orbit",
          { strokeDashoffset: 700, opacity: 0 },
          {
            strokeDashoffset: 0,
            opacity: 0.7,
            duration: 1.1,
            ease: "power2.out",
          },
          0,
        )
        .fromTo(
          ".intro-wordmark",
          { y: 12, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.45, ease: "power3.out" },
          0.45,
        )
        .to(
          ".intro-composition",
          { y: -16, opacity: 0, duration: 0.3, ease: "power2.inOut" },
          1.65,
        )
        .to(dialog, { opacity: 0, duration: 0.25 }, 1.8);
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
    { scope, dependencies: [done, replay] },
  );
  return (
    <dialog
      ref={scope}
      className="intro"
      aria-label="ProfitLens introduction"
      onCancel={done}
    >
      <div className="intro-composition">
        <div className="intro-emblem" aria-hidden="true">
          <svg className="intro-orbit" viewBox="0 0 220 220">
            <rect x="24" y="24" width="172" height="172" rx="48" />
          </svg>
          <div className="intro-bars">
            <i className="intro-bar" />
            <i className="intro-bar" />
            <i className="intro-bar" />
          </div>
        </div>
        <div className="intro-wordmark">
          <strong>
            Profit Lens<span>.</span>
          </strong>
          <p>A clearer view starts here.</p>
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
  const returnFocus = useRef<HTMLElement | null>(null);
  const [replaying, setReplaying] = useState(false);
  const [keyboard, setKeyboard] = useState(false);
  const reduce = useReducedMotion();
  const done = useCallback(() => {
    try {
      sessionStorage.setItem(INTRO_KEY, "seen");
    } catch {
      /* The app also works without storage. */
    }
    setIntro(false);
  }, []);
  const replay = useCallback(() => {
    returnFocus.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    setReplaying(true);
    setIntro(true);
  }, []);
  useEffect(() => {
    if (!intro && returnFocus.current?.isConnected) {
      returnFocus.current.focus({ preventScroll: true });
      returnFocus.current = null;
    }
  }, [intro]);
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
      value={{ animate: !reduce && !keyboard && !intro, ready: !intro, replay }}
    >
      <MotionConfig reducedMotion="user" transition={{ duration: 0.22, ease }}>
        <div data-intro-ready={!intro} inert={intro}>
          {children}
        </div>
        {intro && <Introduction done={done} replay={replaying} />}
      </MotionConfig>
    </Experience.Provider>
  );
}

export function ReplayIntro() {
  const { replay } = useExperience();
  const reduced = useReducedMotion();
  if (reduced) return null;
  return (
    <button
      className="replay-button"
      onClick={replay}
      aria-label="Replay logo intro"
      title="Replay logo intro"
    >
      <Play size={13} />
      <span>Play intro</span>
    </button>
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
      initial={animate ? { opacity: 0, transform: "translateY(8px)" } : false}
      animate={{ opacity: 1, transform: "translateY(0px)" }}
      transition={{ duration: animate ? 0.22 : 0, ease }}
    >
      {children}
    </motion.div>
  );
}
