import type { LngLat, Map as MapLibreMap } from "maplibre-gl";

// MapLibre のタイルは 512px。1 CSS ピクセルは 0.0254 / 96 m
const EARTH = 40075016.686;
const METERS_PER_CSS_PIXEL = 0.0254 / 96;

const pad = (value: number, width: number): string => String(value).padStart(width, "0");

export function formatAngle(value: number, positive: string, negative: string, degreeWidth: number): string {
  const abs = Math.abs(value);
  let degrees = Math.floor(abs);
  let minutes = Math.round((abs - degrees) * 600) / 10;
  if (minutes >= 60) {
    degrees += 1;
    minutes = 0;
  }
  return `${pad(degrees, degreeWidth)}°${minutes.toFixed(1).padStart(4, "0")}′${value >= 0 ? positive : negative}`;
}

export function formatPosition(lngLat: Pick<LngLat, "lng" | "lat">): string {
  const lng = ((((lngLat.lng + 180) % 360) + 360) % 360) - 180;
  return `${formatAngle(lngLat.lat, "N", "S", 2)}  ${formatAngle(lng, "E", "W", 3)}`;
}

export function metersPerPixel(lat: number, zoom: number): number {
  return (EARTH * Math.cos((lat * Math.PI) / 180)) / (512 * 2 ** zoom);
}

/** 縮尺の分母を、上から2桁で丸める（1:2,500,000 など）。 */
export function scaleDenominator(lat: number, zoom: number): number {
  const exact = metersPerPixel(lat, zoom) / METERS_PER_CSS_PIXEL;
  const unit = 10 ** Math.max(0, Math.floor(Math.log10(exact)) - 1);
  return Math.round(exact / unit) * unit;
}

/** 縮尺の棒の長さ。最大の長さに収まる、1・2・5 の 10 の累乗の距離を選ぶ。 */
export function scaleBar(lat: number, zoom: number, maxPixels: number): { meters: number; pixels: number } {
  const mpp = metersPerPixel(lat, zoom);
  const max = mpp * maxPixels;
  const base = 10 ** Math.floor(Math.log10(max));
  const meters = [5, 2, 1].map((m) => m * base).find((m) => m <= max) ?? base;
  return { meters, pixels: meters / mpp };
}

function tickStep(zoom: number): number {
  if (zoom < 4) return 10;
  if (zoom < 6) return 5;
  if (zoom < 8) return 1;
  return 0.5;
}

/** 画面の縁に、経緯線が縁を横切る位置の目盛りと値を描く。地球の全体が見えるズームでは描かない。 */
function drawFrame(map: MapLibreMap, canvas: HTMLCanvasElement): void {
  const ratio = devicePixelRatio;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);
  const zoom = map.getZoom();
  if (zoom < 3) return;
  const step = tickStep(zoom);
  const color = getComputedStyle(canvas).color;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.75;
  const label = (value: number, positive: string, negative: string): string =>
    `${Math.abs(value) % 1 ? Math.abs(value).toFixed(1) : Math.abs(value)}°${value >= 0 ? positive : negative}`;
  const edges: { at: (s: number) => [number, number]; length: number; value: (l: LngLat) => number; axis: "x" | "y" }[] = [
    { at: (s) => [s, 0], length: width, value: (l) => l.lng, axis: "x" },
    { at: (s) => [s, height], length: width, value: (l) => l.lng, axis: "x" },
    { at: (s) => [0, s], length: height, value: (l) => l.lat, axis: "y" },
    { at: (s) => [width, s], length: height, value: (l) => l.lat, axis: "y" },
  ];
  for (const edge of edges) {
    let previous: number | null = null;
    for (let s = 0; s <= edge.length; s += 3) {
      const point = edge.at(s);
      const current = edge.value(map.unproject(point));
      if (previous !== null && Math.floor(previous / step) !== Math.floor(current / step) && Math.abs(current - previous) < 90) {
        const crossing = Math.max(Math.floor(previous / step), Math.floor(current / step)) * step;
        const [x, y] = point;
        ctx.beginPath();
        if (edge.axis === "x") {
          const dir = y === 0 ? 1 : -1;
          ctx.moveTo(x, y);
          ctx.lineTo(x, y + 7 * dir);
          ctx.stroke();
          ctx.textAlign = "center";
          ctx.fillText(label(crossing, "E", "W"), x, y === 0 ? 18 : height - 10);
        } else {
          const dir = x === 0 ? 1 : -1;
          ctx.moveTo(x, y);
          ctx.lineTo(x + 7 * dir, y);
          ctx.stroke();
          ctx.textAlign = x === 0 ? "left" : "right";
          ctx.fillText(label(crossing, "N", "S"), x === 0 ? 10 : width - 10, y + 3);
        }
      }
      previous = current;
    }
  }
}

export type ReadoutElements = {
  position: HTMLElement;
  zoom: HTMLElement;
  scale: HTMLElement;
  bar: HTMLCanvasElement;
  barLabel: HTMLElement;
  compass: HTMLElement;
  frame: HTMLCanvasElement;
};

export function attachReadout(map: MapLibreMap, el: ReadoutElements): void {
  let pointer: LngLat | null = null;
  let queued = false;
  const update = (): void => {
    queued = false;
    const center = map.getCenter();
    const zoom = map.getZoom();
    el.position.textContent = formatPosition(pointer ?? center);
    el.zoom.textContent = zoom.toFixed(2);
    el.scale.textContent = `1:${scaleDenominator(center.lat, zoom).toLocaleString("en-US")}`;
    const { meters, pixels } = scaleBar(center.lat, zoom, 120);
    el.barLabel.textContent = meters >= 1000 ? `${meters / 1000} km` : `${meters} m`;
    const ctx = el.bar.getContext("2d");
    if (ctx) {
      const ratio = devicePixelRatio;
      el.bar.width = 124 * ratio;
      el.bar.height = 10 * ratio;
      ctx.scale(ratio, ratio);
      ctx.strokeStyle = getComputedStyle(el.bar).color;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(1, 2);
      ctx.lineTo(1, 8);
      ctx.lineTo(1 + pixels, 8);
      ctx.lineTo(1 + pixels, 2);
      ctx.stroke();
    }
    el.compass.style.setProperty("--bearing", `${-map.getBearing()}deg`);
    drawFrame(map, el.frame);
  };
  const schedule = (): void => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  };
  map.on("move", schedule);
  map.on("resize", schedule);
  map.on("mousemove", (e) => {
    pointer = e.lngLat;
    schedule();
  });
  map.getCanvas().addEventListener("mouseleave", () => {
    pointer = null;
    schedule();
  });
  schedule();
}
