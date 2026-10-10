"use client";
import { useEffect, useRef } from "react";

/*
  The room the glass sits in, drawn in three layers:
  1. a CSS spotlight gradient (always present; the fallback without WebGL),
  2. a small WebGL "studio sweep" shader: a key light breathing from above,
     a teal back light drifting slowly behind, a faint light that follows the
     pointer, vignette and film grain (which also dithers away banding),
  3. a field of dotted waves receding toward a horizon.
  Live mode (sign-in, intro) animates at about 30fps at reduced resolution.
  Inside the workspace both canvases are drawn once, so the blurred glass
  panes never recompute against a moving background.
*/

const VERTEX = `attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;
const FRAGMENT = `precision mediump float;
uniform vec2 r;uniform float t;uniform vec2 m;uniform float mi;
uniform vec3 base;uniform vec3 key;uniform vec3 back;uniform float grain;uniform float depth;
float hash(vec2 q){return fract(sin(dot(q,vec2(12.9898,78.233)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/r;
  float a=r.x/r.y;
  vec2 p=vec2((uv.x-.5)*a,uv.y);
  vec3 c=base*mix(1.,.78+.3*uv.y,depth);
  vec2 kc=vec2(.05*sin(t*.11),1.2+.03*sin(t*.17));
  float kd=length((p-kc)*vec2(.62,1.));
  c+=key*pow(smoothstep(1.15,0.,kd),1.6)*(.92+.08*sin(t*.23));
  vec2 b1=vec2(.42*a*.5*sin(t*.06),.32+.07*cos(t*.08));
  c+=back*smoothstep(.95,0.,length((p-b1)*vec2(.8,1.25)))*.55;
  vec2 b2=vec2(-.38*a*.5*cos(t*.05+1.7),.18+.05*sin(t*.07));
  c+=back*.6*smoothstep(.75,0.,length((p-b2)*vec2(.9,1.4)))*.4;
  vec2 mp=vec2((m.x-.5)*a,m.y);
  c+=key*smoothstep(.5,0.,length(p-mp))*.22*mi;
  float v=smoothstep(1.3,.3,length((uv-vec2(.5,.6))*vec2(1.,1.25)));
  c*=mix(1.-.3*depth,1.,v);
  c+=(hash(gl_FragCoord.xy+fract(t*.37)*61.)-.5)*grain;
  gl_FragColor=vec4(c,1.);
}`;

function rgb(name: string) {
  const parts = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
    .split(/\s+/)
    .map(Number);
  return parts.length === 3 ? parts.map((n) => n / 255) : [0, 0, 0];
}

function useStudioShader(
  ref: React.RefObject<HTMLCanvasElement | null>,
  live: boolean,
) {
  useEffect(() => {
    const canvas = ref.current;
    const gl = canvas?.getContext("webgl", {
      antialias: false,
      depth: false,
      powerPreference: "low-power",
      premultipliedAlpha: false,
    });
    if (!canvas || !gl) return;
    const compile = (type: number, source: string) => {
      const shader = gl.createShader(type)!;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return shader;
    };
    const program = gl.createProgram()!;
    gl.attachShader(program, compile(gl.VERTEX_SHADER, VERTEX));
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAGMENT));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return;
    gl.useProgram(program);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 3, -1, -1, 3]),
      gl.STATIC_DRAW,
    );
    const loc = gl.getAttribLocation(program, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const u = (name: string) => gl.getUniformLocation(program, name);
    const uRes = u("r");
    const uTime = u("t");
    const uMouse = u("m");
    const uMouseOn = u("mi");
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const colors = () => {
      gl.uniform3fv(u("base"), rgb("--shader-base"));
      gl.uniform3fv(u("key"), rgb("--shader-key"));
      gl.uniform3fv(u("back"), rgb("--shader-back"));
      const root = getComputedStyle(document.documentElement);
      gl.uniform1f(u("grain"), Number(root.getPropertyValue("--shader-grain")));
      gl.uniform1f(u("depth"), Number(root.getPropertyValue("--shader-depth")));
    };
    const resize = () => {
      // Soft gradients survive a lower resolution; the GPU cost drops by the square.
      const scale = Math.min(1, (window.devicePixelRatio || 1) * 0.6);
      canvas.width = Math.max(1, Math.round(canvas.clientWidth * scale));
      canvas.height = Math.max(1, Math.round(canvas.clientHeight * scale));
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform2f(uRes, canvas.width, canvas.height);
    };
    const pointer = { x: 0.5, y: 0.75, on: 0, tx: 0.5, ty: 0.75, ton: 0 };
    let time = 12;
    let raf = 0;
    let last = 0;
    const render = () => {
      gl.uniform1f(uTime, time);
      gl.uniform2f(uMouse, pointer.x, pointer.y);
      gl.uniform1f(uMouseOn, pointer.on);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    };
    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      if (now - last < 32) return;
      time += Math.min(0.08, (now - last) / 1000);
      last = now;
      // The pointer light follows with lag, like light moving behind glass.
      pointer.x += (pointer.tx - pointer.x) * 0.06;
      pointer.y += (pointer.ty - pointer.y) * 0.06;
      pointer.on += (pointer.ton - pointer.on) * 0.05;
      render();
    };
    const start = () => {
      cancelAnimationFrame(raf);
      if (live && !reduced.matches && document.visibilityState === "visible") {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      } else render();
    };
    const move = (e: PointerEvent) => {
      pointer.tx = e.clientX / window.innerWidth;
      pointer.ty = 1 - e.clientY / window.innerHeight;
      pointer.ton = 1;
    };
    const leave = () => {
      pointer.ton = 0;
    };
    colors();
    resize();
    start();
    const ro = new ResizeObserver(() => {
      resize();
      render();
    });
    ro.observe(canvas);
    const recolor = () => {
      colors();
      render();
    };
    const theme = new MutationObserver(recolor);
    theme.observe(document.documentElement, {
      attributeFilter: ["data-theme"],
    });
    const scheme = matchMedia("(prefers-color-scheme: dark)");
    scheme.addEventListener("change", recolor);
    reduced.addEventListener("change", start);
    document.addEventListener("visibilitychange", start);
    if (live) {
      window.addEventListener("pointermove", move, { passive: true });
      document.documentElement.addEventListener("pointerleave", leave);
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      theme.disconnect();
      scheme.removeEventListener("change", recolor);
      reduced.removeEventListener("change", start);
      document.removeEventListener("visibilitychange", start);
      window.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", leave);
      // Keep the context alive: a remount reuses this canvas and its context.
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    };
  }, [ref, live]);
}

function useWaveField(
  ref: React.RefObject<HTMLCanvasElement | null>,
  live: boolean,
) {
  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let w = 0;
    let h = 0;
    let color = "120 175 190";
    let raf = 0;
    let last = 0;
    let t = 0;
    const readColor = () => {
      color = getComputedStyle(document.documentElement)
        .getPropertyValue("--wave")
        .trim();
    };
    const resize = () => {
      const dpr = Math.min(1.5, window.devicePixelRatio || 1);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const rows = 46;
      for (let r = 0; r < rows; r++) {
        // Rows bunch toward the horizon and spread toward the viewer.
        const ease = (r / (rows - 1)) ** 2;
        const y0 = h * (0.08 + 0.92 * ease);
        const amp = 6 + 26 * ease;
        const step = 5 + 5 * ease;
        const size = 0.7 + 1.1 * ease;
        ctx.fillStyle = `rgb(${color} / ${(0.08 + 0.42 * ease).toFixed(3)})`;
        for (let x = 0; x <= w; x += step) {
          const u = x / w;
          const edge = Math.sin(Math.PI * u);
          if (edge < 0.08) continue;
          const y =
            y0 +
            amp *
              (Math.sin(u * 7.5 + t * 0.55 + r * 0.22) * 0.6 +
                Math.sin(u * 3.1 - t * 0.35 + r * 0.11) * 0.4);
          ctx.globalAlpha = edge;
          ctx.fillRect(x, y, size, size);
        }
      }
      ctx.globalAlpha = 1;
    };
    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      if (now - last < 32) return;
      t += Math.min(0.08, (now - last) / 1000);
      last = now;
      draw();
    };
    const start = () => {
      cancelAnimationFrame(raf);
      if (live && !reduced.matches && document.visibilityState === "visible") {
        last = performance.now();
        raf = requestAnimationFrame(frame);
      } else draw();
    };
    readColor();
    resize();
    start();
    const ro = new ResizeObserver(() => {
      resize();
      draw();
    });
    ro.observe(canvas);
    const recolor = () => {
      readColor();
      draw();
    };
    const theme = new MutationObserver(recolor);
    theme.observe(document.documentElement, {
      attributeFilter: ["data-theme"],
    });
    const scheme = matchMedia("(prefers-color-scheme: dark)");
    scheme.addEventListener("change", recolor);
    reduced.addEventListener("change", start);
    document.addEventListener("visibilitychange", start);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      theme.disconnect();
      scheme.removeEventListener("change", recolor);
      reduced.removeEventListener("change", start);
      document.removeEventListener("visibilitychange", start);
    };
  }, [ref, live]);
}

export function Stage({ live }: { live: boolean }) {
  const shader = useRef<HTMLCanvasElement>(null);
  const waves = useRef<HTMLCanvasElement>(null);
  useStudioShader(shader, live);
  useWaveField(waves, live);
  return (
    <div className={`stage-bg ${live ? "" : "is-quiet"}`} aria-hidden="true">
      <canvas ref={shader} className="stage-shader" />
      <canvas ref={waves} className="stage-waves" />
    </div>
  );
}
