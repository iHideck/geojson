import "maplibre-gl/dist/maplibre-gl.css";
import { addProtocol, type MapGeoJSONFeature, Map as MapLibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";
// MapLibre はワーカーの場所を自分の置き場所から組み立てるので、まとめた後の場所を教える
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { Protocol } from "pmtiles";
import { createCard } from "./card.ts";
import { type Catalog, featureIndex, loadCatalog } from "./catalog.ts";
import { createDialogs, type DialogKind } from "./dialogs.ts";
import { applyTexts, type Strings, strings } from "./i18n.ts";
import { homeView, type Intro, playIntro } from "./intro.ts";
import { createPanel } from "./panel.ts";
import { attachReadout } from "./readout.ts";
import { type Hit, loadSearch, search } from "./search.ts";
import { initialState, type Lang, readHash, STAGES, type ViewState, writeHash } from "./state.ts";
import { buildStyle, PICK_PARTS } from "./style.ts";

const BASE = new URL(import.meta.env.BASE_URL, location.href);
const $ = <T extends Element = HTMLElement>(selector: string): T => document.querySelector(selector) as T;
const reducedMotion = (): boolean => matchMedia("(prefers-reduced-motion: reduce)").matches;

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

function attachSearch(catalog: Catalog, t: () => Strings, lang: () => Lang, pick: (hit: Hit) => void): void {
  const input = $<HTMLInputElement>("#search");
  const list = $<HTMLUListElement>("#search-results");
  let hits: Hit[] = [];
  let active = -1;
  const titles = new Map(catalog.layers.map((l) => [l.id, l.title]));
  const close = (): void => {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };
  const render = (): void => {
    list.replaceChildren(
      ...hits.map((hit, i) => {
        const item = document.createElement("li");
        item.id = `search-${i}`;
        item.setAttribute("role", "option");
        item.setAttribute("aria-selected", String(i === active));
        const name = lang() === "en" ? (hit.entry.name_en ?? hit.entry.name_ja) : hit.entry.name_ja;
        item.append(String(name ?? ""), Object.assign(document.createElement("small"), { textContent: titles.get(hit.layer)?.[lang()] ?? "" }));
        item.addEventListener("mousedown", (e) => {
          e.preventDefault();
          choose(i);
        });
        return item;
      }),
    );
    if (!hits.length && input.value.trim()) {
      list.append(Object.assign(document.createElement("li"), { className: "empty", textContent: t().noResults }));
    }
    list.hidden = !input.value.trim();
    input.setAttribute("aria-expanded", String(!list.hidden));
    if (active >= 0) input.setAttribute("aria-activedescendant", `search-${active}`);
    else input.removeAttribute("aria-activedescendant");
  };
  const choose = (i: number): void => {
    const hit = hits[i];
    if (!hit) return;
    close();
    input.blur();
    pick(hit);
  };
  input.addEventListener("focus", () => void loadSearch(BASE.href));
  input.addEventListener("input", () => {
    loadSearch(BASE.href).then((index) => {
      hits = search(index, input.value);
      active = hits.length ? 0 : -1;
      render();
    });
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!hits.length) return;
      active = (active + (e.key === "ArrowDown" ? 1 : hits.length - 1)) % hits.length;
      render();
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(active);
    } else if (e.key === "Escape") {
      close();
    }
  });
  input.addEventListener("blur", close);
}

/** 地図と画面を組み立てる。defaultLang は、URL に言語が書かれていないときの言語。 */
export async function start(defaultLang: Lang): Promise<void> {
  const catalog = await loadCatalog(BASE.href);
  const shared = /(^#|&)map=/.test(location.hash);
  let state: ViewState = {
    ...initialState(catalog, defaultLang),
    ...readHash(location.hash, catalog),
    revealed: shared || reducedMotion() ? STAGES : 0,
  };
  const t = (): Strings => strings(state.lang);
  const openDialog = createDialogs($<HTMLDialogElement>("#dialog"), catalog, BASE);
  for (const button of document.querySelectorAll<HTMLButtonElement>("[data-dialog]")) {
    button.addEventListener("click", () => openDialog(button.dataset.dialog as DialogKind, state.lang, t()));
  }
  if (!webglAvailable()) {
    document.body.dataset.fallback = "1";
    const image = $<HTMLImageElement>(".fallback img");
    image.src = new URL(image.dataset.src as string, BASE).href;
    applyTexts(t(), state.lang);
    return;
  }
  setWorkerUrl(workerUrl);
  addProtocol("pmtiles", new Protocol({ metadata: true }).tile);
  const home = homeView();
  const map = new MapLibreMap({
    container: "map",
    style: buildStyle(catalog, BASE, state),
    center: home.center,
    zoom: home.zoom,
    hash: "map",
    maxPitch: 0,
    attributionControl: false,
  });
  if (!shared) map.jumpTo(home);
  map.addControl(new NavigationControl({ showCompass: false }), "bottom-right");
  map.getCanvas().setAttribute("aria-label", t().mapLabel);

  const card = createCard($("#card"), {
    close: () => set({ selected: null }),
    flyTo: ([west, south, east, north]) =>
      map.fitBounds(
        [
          [west, south],
          [east, north],
        ],
        { padding: 60, maxZoom: 10, duration: reducedMotion() ? 0 : 1200 },
      ),
    copy: () => navigator.clipboard.writeText(location.href),
  });
  let cardToken = 0;
  const showCard = (): void => {
    const token = ++cardToken;
    const selected = state.selected;
    const layer = catalog.layers.find((l) => l.id === selected?.layer);
    if (!selected || !layer) {
      card.hide();
      return;
    }
    loadSearch(BASE.href).then((index) => {
      const entry = index.layers[selected.layer]?.[selected.index];
      if (token !== cardToken) return;
      if (entry) card.show(layer, entry, state.lang, t());
      else card.hide();
    });
  };

  const panel = createPanel($("#panel"), catalog, {
    toggle: (id, shown) => {
      const hidden = new Set(state.hidden);
      if (shown) hidden.delete(id);
      else hidden.add(id);
      set({ hidden });
    },
    opacity: (id, value) => set({ opacity: { ...state.opacity, [id]: value } }),
    choose: (id, choice) => set({ choices: { ...state.choices, [id]: choice } }),
  });

  function set(update: Partial<ViewState>): void {
    const before = state;
    state = { ...state, ...update };
    map.setStyle(buildStyle(catalog, BASE, state), { diff: true });
    panel(state, t());
    if (before.lang !== state.lang) applyTexts(t(), state.lang);
    if (before.selected !== state.selected || before.lang !== state.lang) showCard();
    const hash = writeHash(location.hash, state, catalog, defaultLang);
    history.replaceState(history.state, "", `${location.pathname}${location.search}${hash}`);
  }

  for (const button of document.querySelectorAll<HTMLButtonElement>("[data-lang]")) {
    button.addEventListener("click", () => set({ lang: button.dataset.lang as Lang }));
  }
  $("#compass").addEventListener("click", () => map.easeTo({ bearing: 0, duration: reducedMotion() ? 0 : 500 }));
  $(".menu-button").addEventListener("click", (e) => {
    const top = $(".topbar");
    const open = top.dataset.open !== "1";
    top.dataset.open = open ? "1" : "0";
    (e.currentTarget as HTMLElement).setAttribute("aria-expanded", String(open));
  });
  // スマートフォンでは、地図を広く見せるため、凡例をたたんで始める
  if (matchMedia("(max-width: 640px)").matches) {
    $("#panel").dataset.collapsed = "1";
    $(".sheet-handle").setAttribute("aria-expanded", "false");
  }
  $(".sheet-handle").addEventListener("click", (e) => {
    const sheet = $("#panel");
    const collapsed = sheet.dataset.collapsed !== "1";
    sheet.dataset.collapsed = collapsed ? "1" : "0";
    (e.currentTarget as HTMLElement).setAttribute("aria-expanded", String(!collapsed));
  });

  attachReadout(map, {
    position: $("#ro-pos"),
    zoom: $("#ro-zoom"),
    scale: $("#ro-scale"),
    bar: $<HTMLCanvasElement>("#scalebar"),
    barLabel: $("#scalebar-label"),
    compass: $("#compass"),
    frame: $<HTMLCanvasElement>("#frame"),
  });
  attachSearch(catalog, t, () => state.lang, (hit) => {
    endIntro(false);
    const [west, south, east, north] = hit.entry.bbox;
    map.fitBounds(
      [
        [west, south],
        [east, north],
      ],
      { padding: 80, maxZoom: 9, duration: reducedMotion() ? 0 : 1200 },
    );
    set({ selected: { layer: hit.layer, index: hit.index }, hidden: new Set([...state.hidden].filter((id) => id !== hit.layer)) });
  });

  const pickable = (): string[] =>
    map
      .getStyle()
      .layers.filter((l) => PICK_PARTS.some((part) => l.id.endsWith(`:${part}`)) && l.layout?.visibility !== "none")
      .map((l) => l.id);
  const pick = (features: MapGeoJSONFeature[]): MapGeoJSONFeature | undefined => {
    for (const part of PICK_PARTS) {
      const found = features.find((f) => f.layer.id.endsWith(`:${part}`) && f.id !== undefined);
      if (found) return found;
    }
    return undefined;
  };
  map.on("click", (e) => {
    const feature = pick(map.queryRenderedFeatures(e.point, { layers: pickable() }));
    set({ selected: feature ? { layer: feature.layer.id.split("@")[0] as string, index: featureIndex(feature.id as number) } : null });
  });
  map.on("mousemove", (e) => {
    map.getCanvas().style.cursor = pick(map.queryRenderedFeatures(e.point, { layers: pickable() })) ? "pointer" : "";
  });

  // 演出は、地図を読み込んでから始める。読み込みの前に飛ばされたら始めない
  let introPlanned = state.revealed < STAGES;
  let intro: Intro | null = null;
  const skipButton = $<HTMLButtonElement>("#skip");
  skipButton.hidden = !introPlanned;
  function endIntro(home: boolean): void {
    skipButton.hidden = true;
    if (intro) intro.end(home);
    else if (introPlanned) set({ revealed: STAGES });
    introPlanned = false;
    intro = null;
  }
  skipButton.addEventListener("click", () => endIntro(true));
  map.on("movestart", (e) => {
    // 利用者が地図を動かしたら、演出をその場で終える
    if (e.originalEvent && (intro || introPlanned)) endIntro(false);
  });
  addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (intro || introPlanned) endIntro(true);
    else if (state.selected && !$<HTMLDialogElement>("#dialog").open) set({ selected: null });
  });
  map.once("load", () => {
    panel(state, t());
    showCard();
    if (introPlanned) {
      intro = playIntro(
        map,
        (stage) => set({ revealed: Math.max(state.revealed, stage) }),
        () => {
          intro = null;
          introPlanned = false;
          skipButton.hidden = true;
        },
      );
    }
    map.once("idle", () => {
      document.documentElement.dataset.ready = "1";
    });
  });
  // ブラウザのテストが地図の様子を読むための入口
  Object.assign(window, { __map: map, __state: () => state });
}
