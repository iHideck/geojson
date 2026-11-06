import type { Lang } from "./state.ts";

const ja = {
  title: "MIDNIGHT CHART",
  subtitle: "日本と世界の陸と海の境界",
  pageTitle: "Midnight Chart — 日本と世界の境界",
  search: "地名・コードで検索（例: 佐渡島、JPN）",
  searchLabel: "地名またはコードで検索",
  noResults: "見つかりません",
  menu: "メニュー",
  openMenu: "メニューを開く",
  data: "データ",
  howto: "使い方",
  license: "ライセンス",
  language: "言語",
  layers: "凡例",
  layersEn: "LAYERS",
  show: (name: string) => `${name}を表示`,
  opacity: (name: string) => `${name}の不透明度`,
  resolution: (name: string) => `${name}の解像度`,
  auto: "自動",
  position: "位置",
  zoom: "ズーム",
  scale: "縮尺",
  disclaimer: "境界は法的な境界を示しません。測量や航海など、位置の精度や安全に関わる用途には使えません。",
  disclaimerShort: "法的な境界ではありません。測量や航海には使えません。",
  skip: "演出をスキップ",
  close: "閉じる",
  flyTo: "この範囲へ移動",
  copyUrl: "URL をコピー",
  copied: "コピーしました",
  source: "出典",
  retrieved: "取得日",
  credits: "出典",
  northUp: "北を上にする",
  sheet: "凡例を開く・閉じる",
  noWebgl: "この端末のブラウザでは地図を描けません（WebGL が使えません）。データは、メニューの「データ」から取得できます。",
  loadError: "データを読めませんでした。時間をおいて開き直してください。",
  mapLabel: "境界の地図",
  download: "ダウンロード",
  browserUrl: "ブラウザから読む URL",
  files: "ファイル",
  allInOne: "全レイヤーをまとめたもの",
  gpkg: "GeoPackage（QGIS のスタイル入り）",
  qgis: "QGIS プロジェクト（GeoPackage と一緒に展開して開く）",
  stac: "STAC カタログ",
  sums: "SHA256SUMS",
  pinned: "版を固定するときは、URL の latest/download を download/v1.2.3 のように書き換えます。",
  howtoQgis: "QGIS では、「QGIS プロジェクト」の zip を展開し、.qgz を開きます。スタイル付きで全レイヤーが表示されます。",
  howtoGdal: "GDAL では、GitHub Pages の FlatGeobuf をダウンロードせずに読めます。",
  howtoWeb: "MapLibre GL JS では、PMTiles を pmtiles プロトコルで読みます。",
  privacy: "このサイトは、アクセス解析・広告・外部の地図タイルを使いません。",
  codeLicense: "コードは MIT ライセンスです。",
  dataLicense: "データのライセンスとクレジットの書き方",
  maritimeNote: "海域（EEZ・領海・接続水域・基線・公海）のデータは、まだ配っていません。",
  kind: { "world/countries": "国・地域", "japan/prefectures": "都道府県", "japan/municipalities": "市区町村", "japan/islands": "島" } as Record<string, string>,
  field: {
    iso_a2: "ISO 3166-1 alpha-2",
    iso_a3: "ISO 3166-1 alpha-3",
    iso_n3: "ISO 3166-1 numeric",
    pref_code: "都道府県コード",
    iso_3166_2: "ISO 3166-2",
    lg_code: "団体コード",
    lg_codes: "団体コード",
    name_kana: "読み",
    area_km2: "面積（km²）",
    pref_ja: "都道府県",
  } as Record<string, string>,
};

// 日本語と同じ形にする（足りない文言は型の検査で落ちる）
const en: typeof ja = {
  title: "MIDNIGHT CHART",
  subtitle: "Land and maritime boundaries of Japan and the world",
  pageTitle: "Midnight Chart — Japan & World Boundaries",
  search: "Search names or codes (e.g. Sado, JPN)",
  searchLabel: "Search names or codes",
  noResults: "No results",
  menu: "Menu",
  openMenu: "Open menu",
  data: "Data",
  howto: "How to use",
  license: "License",
  language: "Language",
  layers: "Layers",
  layersEn: "LAYERS",
  show: (name: string) => `Show ${name}`,
  opacity: (name: string) => `${name} opacity`,
  resolution: (name: string) => `${name} resolution`,
  auto: "Auto",
  position: "Position",
  zoom: "Zoom",
  scale: "Scale",
  disclaimer: "The boundaries have no legal status and must not be used for surveying, navigation or other purposes that need positional accuracy or safety.",
  disclaimerShort: "Not legal boundaries. Not for surveying or navigation.",
  skip: "Skip intro",
  close: "Close",
  flyTo: "Zoom to",
  copyUrl: "Copy URL",
  copied: "Copied",
  source: "Source",
  retrieved: "Retrieved",
  credits: "Credits",
  northUp: "Reset north",
  sheet: "Show or hide layers",
  noWebgl: "This browser cannot draw the map (WebGL is unavailable). You can still get the data from Data in the menu.",
  loadError: "Could not load the data. Please reload later.",
  mapLabel: "Boundary map",
  download: "Download",
  browserUrl: "URL for browsers",
  files: "Files",
  allInOne: "All layers in one file",
  gpkg: "GeoPackage (with QGIS styles)",
  qgis: "QGIS project (unzip with the GeoPackage, then open)",
  stac: "STAC catalog",
  sums: "SHA256SUMS",
  pinned: "To pin a version, replace latest/download in the URL with download/v1.2.3.",
  howtoQgis: "In QGIS, unzip the QGIS project and open the .qgz. All layers appear with their styles.",
  howtoGdal: "GDAL reads the FlatGeobuf on GitHub Pages without downloading the whole file.",
  howtoWeb: "In MapLibre GL JS, read the PMTiles with the pmtiles protocol.",
  privacy: "This site uses no analytics, no ads and no external map tiles.",
  codeLicense: "The code is under the MIT License.",
  dataLicense: "Data licenses and how to credit",
  maritimeNote: "Maritime zones (EEZ, territorial seas, contiguous zones, baselines, high seas) are not distributed yet.",
  kind: { "world/countries": "Country or area", "japan/prefectures": "Prefecture", "japan/municipalities": "Municipality", "japan/islands": "Island" } as Record<string, string>,
  field: {
    iso_a2: "ISO 3166-1 alpha-2",
    iso_a3: "ISO 3166-1 alpha-3",
    iso_n3: "ISO 3166-1 numeric",
    pref_code: "Prefecture code",
    iso_3166_2: "ISO 3166-2",
    lg_code: "LG code",
    lg_codes: "LG codes",
    name_kana: "Reading",
    area_km2: "Area (km²)",
    pref_ja: "Prefecture",
  } as Record<string, string>,
};

export type Strings = typeof ja;
const STRINGS: Record<Lang, Strings> = { ja, en };

export function strings(lang: Lang): Strings {
  return STRINGS[lang];
}

export function preferredLang(): Lang {
  return navigator.language.toLowerCase().startsWith("ja") ? "ja" : "en";
}

type TextKey = { [K in keyof Strings]: Strings[K] extends string ? K : never }[keyof Strings];

export function applyTexts(t: Strings, lang: Lang): void {
  document.documentElement.lang = lang;
  document.title = t.pageTitle;
  // 同じ文言を書き直すと、描き直しで最大の描画（LCP）が遅れるので、変わるときだけ書く
  for (const node of document.querySelectorAll<HTMLElement>("[data-t]")) {
    const text = t[node.dataset.t as TextKey];
    if (node.textContent !== text) node.textContent = text;
  }
  for (const node of document.querySelectorAll<HTMLElement>("[data-t-label]")) node.setAttribute("aria-label", t[node.dataset.tLabel as TextKey]);
  for (const node of document.querySelectorAll<HTMLInputElement>("[data-t-placeholder]")) node.placeholder = t[node.dataset.tPlaceholder as TextKey];
  for (const button of document.querySelectorAll<HTMLButtonElement>("[data-lang]")) button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
}
