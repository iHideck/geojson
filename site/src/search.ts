import type { Lang } from "./state.ts";

// GitHub Pages の latest/search.json。行の並びは PMTiles の地物の番号と同じ
export type Entry = { [field: string]: string | number | [number, number, number, number] } & {
  bbox: [number, number, number, number];
};
export type SearchIndex = { layers: Record<string, Entry[]> };
export type Hit = { layer: string; index: number; entry: Entry };

const NAMES = ["name_ja", "name_en", "name_kana", "pref_ja"];

/** 画面の言葉での名前。無いときは、もう一方の言葉の名前を使う（海域には日本語の名前が無い）。 */
export function entryName(entry: Entry, lang: Lang): string | null {
  const [first, second] = lang === "en" ? [entry.name_en, entry.name_ja] : [entry.name_ja, entry.name_en];
  const name = first ?? second;
  return typeof name === "string" ? name : null;
}
const CODES = ["iso_a2", "iso_a3", "iso_n3", "pref_code", "iso_3166_2", "lg_code", "lg_codes"];

/** 全角と半角、大文字と小文字、カタカナとひらがなの違いを無くす。 */
export function normalize(text: string): string {
  return text
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[ァ-ヶ]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0x60))
    .replace(/\s+/g, "");
}

/**
 * 名前とコードで探す。コードの一致、名前の前方一致、名前の部分一致の順に並べる。
 * 同じ順位のあいだは、索引の順（レイヤーの順、地物の順）のまま。
 */
export function search(index: SearchIndex, query: string, limit = 8): Hit[] {
  const q = normalize(query);
  if (!q) return [];
  const ranked: [number, Hit][] = [];
  for (const [layer, entries] of Object.entries(index.layers)) {
    entries.forEach((entry, i) => {
      let rank = Number.POSITIVE_INFINITY;
      for (const field of CODES) {
        const value = entry[field];
        if (value === undefined) continue;
        for (const code of String(value).split(",")) {
          if (normalize(code) === q) rank = Math.min(rank, 0);
        }
      }
      for (const field of NAMES) {
        const value = entry[field];
        if (typeof value !== "string") continue;
        const name = normalize(value);
        if (name === q) rank = Math.min(rank, 1);
        else if (name.startsWith(q)) rank = Math.min(rank, 2);
        else if (name.includes(q)) rank = Math.min(rank, 3);
      }
      if (rank < Number.POSITIVE_INFINITY) ranked.push([rank, { layer, index: i, entry }]);
    });
  }
  return ranked
    .sort((a, b) => a[0] - b[0])
    .slice(0, limit)
    .map(([, hit]) => hit);
}

let loading: Promise<SearchIndex> | null = null;

export function loadSearch(base: string): Promise<SearchIndex> {
  loading ??= fetch(`${base}latest/search.json`).then((response) => {
    if (!response.ok) throw new Error(`検索の索引を読めない（${response.status}）`);
    return response.json() as Promise<SearchIndex>;
  });
  return loading;
}
