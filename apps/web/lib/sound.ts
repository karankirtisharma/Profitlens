/*
  Interface sound, synthesized with the Web Audio API (no audio files).
  The palette is glass: soft sine tones with a quick attack, an exponential
  decay and quiet inharmonic partials, through one master bus with a gentle
  compressor. Off by default; the choice is remembered per browser.
*/

const KEY = "profitlens.sound";
export const SOUND_EVENT = "profitlens-sound";

let context: AudioContext | null = null;
let master: GainNode | null = null;

export function soundEnabled() {
  try {
    return localStorage.getItem(KEY) === "on";
  } catch {
    return false;
  }
}

export function setSoundEnabled(on: boolean) {
  try {
    localStorage.setItem(KEY, on ? "on" : "off");
  } catch {
    /* The choice still applies until the page reloads. */
  }
  window.dispatchEvent(new Event(SOUND_EVENT));
}

function bus() {
  if (!context) {
    const Ctor =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!Ctor) return null;
    context = new Ctor();
    const compressor = context.createDynamicsCompressor();
    compressor.threshold.value = -18;
    compressor.ratio.value = 3;
    master = context.createGain();
    master.gain.value = 0.55;
    master.connect(compressor).connect(context.destination);
  }
  // Audio stays suspended until the visitor has interacted with the page.
  // Without that, skip the sound rather than queue it to play late.
  if (context.state === "suspended") {
    if (!navigator.userActivation?.hasBeenActive) return null;
    void context.resume();
  }
  return context.state === "closed" ? null : context;
}

type Tone = {
  freq: number;
  at?: number;
  gain?: number;
  attack?: number;
  decay?: number;
  type?: OscillatorType;
  glide?: number;
};

function tone(ctx: AudioContext, t: Tone) {
  const start = ctx.currentTime + (t.at ?? 0);
  const peak = t.gain ?? 0.08;
  const attack = t.attack ?? 0.004;
  const decay = t.decay ?? 0.35;
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.type = t.type ?? "sine";
  osc.frequency.setValueAtTime(t.freq, start);
  if (t.glide)
    osc.frequency.exponentialRampToValueAtTime(t.glide, start + attack + decay);
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(peak, start + attack);
  env.gain.exponentialRampToValueAtTime(0.0001, start + attack + decay);
  osc.connect(env).connect(master!);
  osc.start(start);
  osc.stop(start + attack + decay + 0.05);
}

/** A struck glass note: a fundamental plus two soft inharmonic partials. */
function glass(
  ctx: AudioContext,
  freq: number,
  at = 0,
  gain = 0.07,
  decay = 0.9,
) {
  tone(ctx, { freq, at, gain, decay });
  tone(ctx, { freq: freq * 2.76, at, gain: gain * 0.28, decay: decay * 0.45 });
  tone(ctx, { freq: freq * 5.4, at, gain: gain * 0.1, decay: decay * 0.2 });
}

function play(fn: (ctx: AudioContext) => void) {
  if (typeof window === "undefined" || !soundEnabled()) return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const ctx = bus();
  if (ctx) fn(ctx);
}

export const sfx = {
  /** Navigation and small controls: a soft, short tap. */
  tap: () =>
    play((ctx) => {
      tone(ctx, { freq: 1650, gain: 0.03, decay: 0.05 });
      tone(ctx, { freq: 820, gain: 0.02, decay: 0.07, type: "triangle" });
    }),
  /** The intro: a low swell under two glass notes. */
  intro: () =>
    play((ctx) => {
      tone(ctx, { freq: 196, gain: 0.035, attack: 0.35, decay: 1.6 });
      glass(ctx, 880, 0.18, 0.06, 1.3);
      glass(ctx, 1318.5, 0.36, 0.045, 1.5);
    }),
  /** Something saved or confirmed: two rising glass notes. */
  success: () =>
    play((ctx) => {
      glass(ctx, 784, 0, 0.055, 0.6);
      glass(ctx, 1174.7, 0.09, 0.05, 0.8);
    }),
  /** Something went wrong: a muted, falling pair. */
  error: () =>
    play((ctx) => {
      tone(ctx, { freq: 247, gain: 0.06, decay: 0.16, glide: 220 });
      tone(ctx, { freq: 196, at: 0.12, gain: 0.05, decay: 0.22, glide: 175 });
    }),
  /** A dialog or pane coming forward. */
  open: () =>
    play((ctx) => {
      glass(ctx, 1046.5, 0, 0.035, 0.4);
    }),
};

/** Confirms the toggle itself; it plays even though sound was just switched on. */
export function playToggle(on: boolean) {
  const ctx = bus();
  if (!ctx) return;
  glass(ctx, on ? 1046.5 : 659.3, 0, 0.05, on ? 0.6 : 0.3);
}
