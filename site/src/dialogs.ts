import type { Catalog } from "./catalog.ts";
import type { Strings } from "./i18n.ts";
import type { Lang } from "./state.ts";

const REPO = "https://github.com/iHideck/geojson";
// リリースのファイル名は、データを作る側（scripts/boundaries/distribution.py）と同じにする
const BUNDLES = [
  ["gpkg", "geojson-boundaries.gpkg"],
  ["qgis", "geojson-boundaries-qgis.zip"],
  ["sums", "SHA256SUMS"],
] as const;
const RELEASE = `${REPO}/releases/latest/download`;

type FileEntry = { format: string; name: string; bytes: number; url: string; pages_url?: string };
type Metadata = { resolutions: { id: string; files: FileEntry[] }[]; sources: { title: string; retrieved: string | null }[] };

export type DialogKind = "data" | "howto" | "license";

function size(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function el(tag: string, attrs: Record<string, string> = {}, ...children: (Node | string)[]): HTMLElement {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  node.append(...children);
  return node;
}

function link(href: string, label: string): HTMLElement {
  return el("a", { href, rel: "noopener" }, label);
}

function copyButton(value: string, t: Strings): HTMLElement {
  const button = el("button", { type: "button", class: "copy" }, t.copyUrl);
  button.addEventListener("click", () => {
    navigator.clipboard.writeText(value).then(() => {
      button.textContent = t.copied;
    });
  });
  return button;
}

function code(text: string): HTMLElement {
  return el("pre", {}, el("code", {}, text));
}

export function createDialogs(dialog: HTMLDialogElement, catalog: Catalog, base: URL): (kind: DialogKind, lang: Lang, t: Strings) => void {
  const metadata = new Map<string, Promise<Metadata>>();
  const load = (path: string): Promise<Metadata> => {
    if (!metadata.has(path)) {
      metadata.set(
        path,
        fetch(new URL(path, base)).then((r) => r.json() as Promise<Metadata>),
      );
    }
    return metadata.get(path) as Promise<Metadata>;
  };
  dialog.addEventListener("click", (e) => {
    // 外側（背景）を押したら閉じる
    if (e.target === dialog) dialog.close();
  });

  async function dataBody(lang: Lang, t: Strings): Promise<HTMLElement[]> {
    const sections: HTMLElement[] = [];
    for (const layer of catalog.layers) {
      const meta = await load(layer.metadata);
      const retrieved = meta.sources.map((s) => s.retrieved).filter((d): d is string => d !== null).sort().at(-1) ?? "—";
      const table = el("table", {}, el("tr", {}, el("th", {}, t.files), el("th", {}, t.download), el("th", {}, t.browserUrl)));
      for (const res of meta.resolutions) {
        for (const file of res.files) {
          table.append(
            el(
              "tr",
              {},
              el("td", {}, `${res.id} · ${file.format}`),
              el("td", {}, link(file.url, `${file.name}（${size(file.bytes)}）`)),
              el("td", {}, file.pages_url ? copyButton(file.pages_url, t) : "—"),
            ),
          );
        }
      }
      sections.push(
        el(
          "section",
          {},
          el("h3", {}, layer.title[lang]),
          el("p", { class: "meta" }, `${t.source}: ${layer.credit[lang]}`),
          el("p", { class: "meta" }, `${layer.license} · ${t.retrieved}: ${retrieved}`),
          table,
        ),
      );
    }
    const bundles = el("ul", {});
    for (const [key, name] of BUNDLES) bundles.append(el("li", {}, link(`${RELEASE}/${name}`, `${t[key]}`)));
    bundles.append(el("li", {}, link(new URL("stac/catalog.json", base).href, t.stac)));
    sections.push(el("section", {}, el("h3", {}, t.allInOne), bundles, el("p", { class: "meta" }, t.pinned), el("p", { class: "meta" }, t.maritimeNote)));
    return sections;
  }

  function howtoBody(t: Strings): HTMLElement[] {
    const first = catalog.layers[0];
    const res = first?.resolutions.at(-1);
    const fgb = first && res ? new URL(`latest/${first.id}/${res.id}.fgb`, base).href : "";
    const pmtiles = first && res ? new URL(res.pmtiles, base).href : "";
    return [
      el("h3", {}, "QGIS"),
      el("p", {}, t.howtoQgis),
      el("h3", {}, "GDAL"),
      el("p", {}, t.howtoGdal),
      code(`ogrinfo -so -al /vsicurl/${fgb}`),
      el("h3", {}, "MapLibre GL JS"),
      el("p", {}, t.howtoWeb),
      code(`import { Protocol } from "pmtiles";\nmaplibregl.addProtocol("pmtiles", new Protocol().tile);\n// source: { type: "vector", url: "pmtiles://${pmtiles}" }`),
      el("p", { class: "meta" }, t.pinned),
    ];
  }

  function licenseBody(lang: Lang, t: Strings): HTMLElement[] {
    const credits = el("ul", {});
    for (const layer of catalog.layers) credits.append(el("li", {}, `${layer.title[lang]}: ${layer.credit[lang]}（${layer.license}）`));
    return [
      credits,
      el("p", {}, link(`${REPO}/blob/main/DATA_LICENSE.md`, t.dataLicense)),
      el("p", {}, t.codeLicense, " ", link(`${REPO}/blob/main/LICENSE`, "LICENSE")),
      el("p", {}, t.disclaimer),
      el("p", {}, t.maritimeNote),
      el("p", {}, t.privacy),
    ];
  }

  return (kind, lang, t) => {
    const title = { data: t.data, howto: t.howto, license: t.license }[kind];
    const close = el("button", { type: "button", class: "dialog-close", "aria-label": t.close }, "×");
    close.addEventListener("click", () => dialog.close());
    const body = el("div", { class: "dialog-body" });
    dialog.replaceChildren(close, el("h2", { id: "dialog-title" }, title), body);
    dialog.setAttribute("aria-labelledby", "dialog-title");
    if (kind === "data") {
      body.append(el("p", { class: "meta" }, "…"));
      dataBody(lang, t).then(
        (sections) => body.replaceChildren(...sections),
        () => body.replaceChildren(el("p", {}, t.loadError)),
      );
    } else {
      body.append(...(kind === "howto" ? howtoBody(t) : licenseBody(lang, t)));
    }
    if (!dialog.open) dialog.showModal();
  };
}
