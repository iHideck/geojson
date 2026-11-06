import "maplibre-gl/dist/maplibre-gl.css";
import "./styles.css";
import { AttributionControl, addProtocol, Map as MapLibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";
// MapLibre はワーカーの場所を自分の置き場所から組み立てるので、まとめた後の場所を教える
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { Protocol } from "pmtiles";
import { type Catalog, loadCatalog } from "./catalog.ts";
import type { Choice } from "./resolution.ts";
import { buildStyle, type ViewState } from "./style.ts";

const BASE = new URL(import.meta.env.BASE_URL, location.href);

function renderResolutionControls(catalog: Catalog, onChange: (layerId: string, choice: Choice) => void): void {
  const root = document.getElementById("resolutions") as HTMLElement;
  for (const layer of catalog.layers.filter((l) => l.resolutions.length > 1)) {
    const group = document.createElement("div");
    group.className = "seg";
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", `${layer.title.ja}の解像度`);
    const label = document.createElement("span");
    label.className = "seg-label";
    label.textContent = layer.title.ja;
    group.append(label);
    for (const choice of ["auto", ...layer.resolutions.map((r) => r.id)]) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = choice === "auto" ? "自動" : choice;
      button.dataset.layer = layer.id;
      button.dataset.choice = choice;
      button.setAttribute("aria-pressed", String(choice === "auto"));
      button.addEventListener("click", () => {
        for (const b of group.querySelectorAll("button")) b.setAttribute("aria-pressed", String(b === button));
        onChange(layer.id, choice);
      });
      group.append(button);
    }
    root.append(group);
  }
}

async function start(): Promise<void> {
  setWorkerUrl(workerUrl);
  const protocol = new Protocol({ metadata: true });
  addProtocol("pmtiles", protocol.tile);
  const catalog = await loadCatalog(BASE.href);
  let state: ViewState = { choices: {} };
  const map = new MapLibreMap({
    container: "map",
    style: buildStyle(catalog, BASE, state),
    center: [138.2, 36.4],
    zoom: 4.6,
    maxPitch: 0,
    attributionControl: false,
  });
  map.addControl(new AttributionControl({ compact: true }), "bottom-right");
  map.addControl(new NavigationControl({ visualizePitch: false }), "top-right");
  renderResolutionControls(catalog, (layerId, choice) => {
    state = { ...state, choices: { ...state.choices, [layerId]: choice } };
    map.setStyle(buildStyle(catalog, BASE, state), { diff: true });
  });
  // ブラウザのテストが地図の様子を読むための入口
  Object.assign(window, { __map: map });
}

start().catch((error: unknown) => {
  document.body.dataset.error = "1";
  console.error(error);
});
