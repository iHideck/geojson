import type { Catalog } from "./catalog.ts";
import type { Choice } from "./resolution.ts";

export type Lang = "ja" | "en";
export type Selected = { layer: string; index: number };

// 画面の状態はこれだけで、地図のスタイルと URL はここから作る
export type ViewState = {
  // 目録のレイヤーの id ごとの解像度の選び方。無ければ自動
  choices: Readonly<Record<string, Choice>>;
  hidden: ReadonlySet<string>;
  // 0〜1。無ければ 1
  opacity: Readonly<Record<string, number>>;
  // 演出で見せ終えた段階。STAGES ならすべて見せている
  revealed: number;
  lang: Lang;
  selected: Selected | null;
};

export const STAGES = 4;
// 最初は隠しておくレイヤー
export const HIDDEN_BY_DEFAULT: readonly string[] = ["japan/municipalities"];

export function initialState(catalog: Catalog, lang: Lang): ViewState {
  const ids = new Set(catalog.layers.map((l) => l.id));
  return {
    choices: {},
    hidden: new Set(HIDDEN_BY_DEFAULT.filter((id) => ids.has(id))),
    opacity: {},
    revealed: 0,
    lang,
    selected: null,
  };
}

function params(hash: string): [string, string][] {
  return hash
    .replace(/^#/, "")
    .split("&")
    .filter(Boolean)
    .map((part): [string, string] => {
      const i = part.indexOf("=");
      return i < 0 ? [part, ""] : [part.slice(0, i), decodeURIComponent(part.slice(i + 1))];
    });
}

/** URL のハッシュから、画面の状態のうち URL に書いたものを読む。知らないレイヤーや値は捨てる。 */
export function readHash(hash: string, catalog: Catalog): Partial<ViewState> {
  const layers = new Map(catalog.layers.map((l) => [l.id, l]));
  const out: Partial<ViewState> = {};
  for (const [key, value] of params(hash)) {
    if (key === "layers") {
      const shown = new Set(value.split(",").filter((id) => layers.has(id)));
      out.hidden = new Set([...layers.keys()].filter((id) => !shown.has(id)));
    } else if (key === "res") {
      const choices: Record<string, Choice> = {};
      for (const pair of value.split(",")) {
        const [id = "", res = ""] = pair.split(":");
        if (layers.get(id)?.resolutions.some((r) => r.id === res)) choices[id] = res;
      }
      out.choices = choices;
    } else if (key === "lang" && (value === "ja" || value === "en")) {
      out.lang = value;
    } else if (key === "sel") {
      const [id = "", index = ""] = value.split(":");
      if (layers.has(id) && /^\d+$/.test(index)) out.selected = { layer: id, index: Number(index) };
    }
  }
  return out;
}

/**
 * 画面の状態を URL のハッシュに書く。初めの状態と同じものは書かない。
 * 地図の位置（map=）は MapLibre が書くので、そのまま残す。
 */
export function writeHash(hash: string, state: ViewState, catalog: Catalog, defaultLang: Lang): string {
  const ours = new Set(["layers", "res", "lang", "sel"]);
  const kept = params(hash)
    .filter(([key]) => !ours.has(key))
    .map(([key, value]) => (value ? `${key}=${value}` : key));
  const base = initialState(catalog, defaultLang);
  const shown = catalog.layers.map((l) => l.id).filter((id) => !state.hidden.has(id));
  const defaultShown = catalog.layers.map((l) => l.id).filter((id) => !base.hidden.has(id));
  if (shown.join(",") !== defaultShown.join(",")) kept.push(`layers=${shown.join(",")}`);
  const res = Object.entries(state.choices).filter(([, choice]) => choice !== "auto");
  if (res.length) kept.push(`res=${res.map(([id, choice]) => `${id}:${choice}`).join(",")}`);
  if (state.lang !== defaultLang) kept.push(`lang=${state.lang}`);
  if (state.selected) kept.push(`sel=${state.selected.layer}:${state.selected.index}`);
  return kept.length ? `#${kept.join("&")}` : "";
}
