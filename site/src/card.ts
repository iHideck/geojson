import type { CatalogLayer } from "./catalog.ts";
import type { Strings } from "./i18n.ts";
import type { Entry } from "./search.ts";
import type { Lang } from "./state.ts";

export type CardHandlers = {
  close(): void;
  flyTo(bbox: Entry["bbox"]): void;
  copy(): Promise<void>;
};

function text(value: Entry[string] | undefined): string | null {
  if (value === undefined || Array.isArray(value)) return null;
  return String(value);
}

export function createCard(root: HTMLElement, handlers: CardHandlers): {
  show(layer: CatalogLayer, entry: Entry, lang: Lang, t: Strings): void;
  hide(): void;
} {
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape") handlers.close();
  });
  return {
    show(layer, entry, lang, t) {
      // 海域の地物には日本語の名前が無いので、英語の名前で埋める
      const name = lang === "en" ? (text(entry.name_en) ?? text(entry.name_ja)) : (text(entry.name_ja) ?? text(entry.name_en));
      const other = lang === "en" ? text(entry.name_ja) : text(entry.name_ja) ? text(entry.name_en) : null;
      const rows = Object.entries(t.field)
        .map(([field, label]) => [label, text(entry[field])] as const)
        .filter((row): row is readonly [string, string] => row[1] !== null);
      const close = Object.assign(document.createElement("button"), { type: "button", className: "card-close", textContent: "×" });
      close.setAttribute("aria-label", t.close);
      close.addEventListener("click", handlers.close);
      const kind = Object.assign(document.createElement("div"), { className: "card-kind", textContent: t.kind[layer.id] ?? layer.title[lang] });
      const heading = Object.assign(document.createElement("h2"), { className: "card-name", id: "card-name", textContent: name ?? "—" });
      const sub = Object.assign(document.createElement("div"), { className: "card-en", textContent: other ?? "" });
      const codes = document.createElement("dl");
      codes.className = "card-codes";
      for (const [label, value] of rows) {
        const row = document.createElement("div");
        row.append(Object.assign(document.createElement("dt"), { textContent: label }), Object.assign(document.createElement("dd"), { textContent: value }));
        codes.append(row);
      }
      const credit = Object.assign(document.createElement("p"), { className: "card-credit", textContent: `${t.source}: ${layer.credit[lang]}` });
      const fly = Object.assign(document.createElement("button"), { type: "button", textContent: t.flyTo });
      fly.addEventListener("click", () => handlers.flyTo(entry.bbox));
      const copy = Object.assign(document.createElement("button"), { type: "button", textContent: t.copyUrl });
      const status = Object.assign(document.createElement("span"), { className: "card-status" });
      status.setAttribute("role", "status");
      copy.addEventListener("click", () => {
        handlers.copy().then(
          () => {
            status.textContent = t.copied;
          },
          () => {
            status.textContent = "";
          },
        );
      });
      const actions = Object.assign(document.createElement("div"), { className: "card-actions" });
      actions.append(fly, copy);
      root.replaceChildren(close, kind, heading, sub, codes, credit, actions, status);
      root.hidden = false;
    },
    hide() {
      root.hidden = true;
      root.replaceChildren();
    },
  };
}
