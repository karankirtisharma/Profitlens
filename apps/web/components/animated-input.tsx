"use client";
import {
  InputEvent as InputChange,
  InputHTMLAttributes,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

/*
  A text input whose newly typed character settles into place: it rises a
  few pixels out of a soft blur. The native input stays in charge of the
  value, caret, selection, autofill and accessibility; its own glyphs are
  transparent and an aria-hidden mirror draws the text on top. Types that
  cannot be mirrored faithfully (numbers, dates, files) render natively.
*/
const MIRRORED = new Set(["text", "email", "password", "search", undefined]);
const COPIED = [
  "fontFamily",
  "fontSize",
  "fontWeight",
  "fontFeatureSettings",
  "letterSpacing",
  "paddingRight",
] as const;

export function AnimatedInput({
  type,
  value,
  defaultValue,
  onInput,
  ...rest
}: InputHTMLAttributes<HTMLInputElement>) {
  const input = useRef<HTMLInputElement>(null);
  const layer = useRef<HTMLSpanElement>(null);
  const track = useRef<HTMLSpanElement>(null);
  const [typed, setTyped] = useState(String(defaultValue ?? ""));
  const [fresh, setFresh] = useState({ index: -1, key: 0 });
  const previous = useRef(String(value ?? defaultValue ?? ""));

  // Follow the input's horizontal scroll so long values stay aligned.
  const sync = () => {
    if (input.current && track.current)
      track.current.style.transform = `translateX(${-input.current.scrollLeft}px)`;
  };

  useLayoutEffect(() => {
    const el = input.current;
    const mirror = layer.current;
    if (!el || !mirror) return;
    const copy = () => {
      const style = getComputedStyle(el);
      for (const name of COPIED) mirror.style[name] = style[name];
      mirror.style.paddingLeft = `${
        parseFloat(style.paddingLeft) + parseFloat(style.borderLeftWidth)
      }px`;
    };
    copy();
    const ro = new ResizeObserver(copy);
    ro.observe(el);
    return () => ro.disconnect();
  }, [type]);
  useLayoutEffect(sync);

  if (!MIRRORED.has(type))
    return (
      <input
        type={type}
        value={value}
        defaultValue={defaultValue}
        onInput={onInput}
        {...rest}
      />
    );

  const handleInput = (event: InputChange<HTMLInputElement>) => {
    const next = event.currentTarget.value;
    const before = value !== undefined ? String(value) : previous.current;
    previous.current = next;
    setTyped(next);
    // Locate the inserted text by comparing values: email inputs expose no
    // caret position, so selectionStart cannot be relied on.
    let start = 0;
    while (start < before.length && before[start] === next[start]) start++;
    const inserted = next.length - before.length;
    setFresh((current) =>
      event.nativeEvent.inputType?.startsWith("insert") && inserted > 0
        ? { index: start + inserted - 1, key: current.key + 1 }
        : { index: -1, key: current.key },
    );
    onInput?.(event);
  };

  const raw = value !== undefined ? String(value) : typed;
  const shown = type === "password" ? "•".repeat(raw.length) : raw;
  const at = fresh.index < shown.length ? fresh.index : -1;
  return (
    <span className="ainput">
      <input
        ref={input}
        type={type}
        value={value}
        defaultValue={defaultValue}
        onInput={handleInput}
        onKeyUp={sync}
        onSelect={sync}
        onFocus={sync}
        onBlur={sync}
        {...rest}
      />
      <span className="ainput-layer" ref={layer} aria-hidden="true">
        <span className="ainput-track" ref={track}>
          {at < 0 ? (
            shown
          ) : (
            <>
              {shown.slice(0, at)}
              <span className="ainput-fresh" key={fresh.key}>
                {shown[at]}
              </span>
              {shown.slice(at + 1)}
            </>
          )}
        </span>
      </span>
    </span>
  );
}
