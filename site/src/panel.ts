import type { Catalog, CatalogLayer } from "./catalog.ts";
import type { Strings } from "./i18n.ts";
import { FALLBACK_LINE, LINES, POINT } from "./palette.ts";
import type { Choice } from "./resolution.ts";
import type { Lang, ViewState } from "./state.ts";

export type PanelHandlers = {
  toggle(layerId: string, shown: boolean): void;
  opacity(layerId: string, value: number): void;
  choose(layerId: string, choice: Choice): void;
};

const SVG = "http://www.w3.org/2000/svg";

function el<K extends keyof HTMLElementTagNameMap>(tag: K, props: Partial<HTMLElementTagNameMap[K]> = {}, ...children: (Node | string)[]): HTMLElementTagNameMap[K] {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function sample(layer: CatalogLayer): SVGSVGElement {
  const svg = document.createElementNS(SVG, "svg");
  svg.setAttribute("viewBox", "0 0 44 12");
  svg.setAttribute("class", "sample");
  svg.setAttribute("aria-hidden", "true");
  if (layer.geometry === "point") {
    svg.innerHTML = `<circle cx="8" cy="6" r="2.6" fill="none" stroke="${POINT.color}" stroke-width="1.2"/>`;
    return svg;
  }
  const look = LINES[layer.id] ?? FALLBACK_LINE;
  const w = look.width[1];
  const dash = look.dash ? ` stroke-dasharray="${look.dash.map((d) => d * w).join(" ")}"` : "";
  const glow = look.glow
    ? `<line x1="2" y1="6" x2="42" y2="6" stroke="${look.color}" stroke-width="${w * 3.4}" opacity=".22" stroke-linecap="round"/>`
    : "";
  svg.innerHTML = `${glow}<line x1="2" y1="6" x2="42" y2="6" stroke="${look.color}" stroke-width="${w}"${dash}/>`;
  return svg;
}

export function createPanel(root: HTMLElement, catalog: Catalog, handlers: PanelHandlers): (state: ViewState, t: Strings) => void {
  let lang: Lang | null = null;
  const list = root.querySelector<HTMLUListElement>(".layers") as HTMLUListElement;
  const resolutions = root.querySelector<HTMLElement>(".res") as HTMLElement;

  function build(t: Strings, state: ViewState): void {
    list.replaceChildren(
      ...catalog.layers.map((layer) => {
        const title = layer.title[state.lang];
        const toggle = el("input", { type: "checkbox", className: "toggle" });
        toggle.dataset.layer = layer.id;
        toggle.setAttribute("aria-label", t.show(title));
        toggle.addEventListener("change", () => handlers.toggle(layer.id, toggle.checked));
        const range = el("input", { type: "range", min: "0", max: "100", step: "5" });
        range.dataset.layer = layer.id;
        range.setAttribute("aria-label", t.opacity(title));
        const output = el("output");
        range.addEventListener("input", () => {
          output.value = range.value;
          handlers.opacity(layer.id, Number(range.value) / 100);
        });
        return el(
          "li",
          { className: "layer" },
          sample(layer),
          el("span", { className: "name" }, title, el("small", {}, layer.resolutions.map((r) => r.id).join(" · "))),
          toggle,
          el("div", { className: "opacity" }, range, output),
        );
      }),
    );
    resolutions.replaceChildren(
      ...catalog.layers
        .filter((layer) => layer.resolutions.length > 1)
        .map((layer) => {
          const group = el("div", { className: "seg" });
          group.setAttribute("role", "group");
          group.setAttribute("aria-label", t.resolution(layer.title[state.lang]));
          for (const choice of ["auto", ...layer.resolutions.map((r) => r.id)]) {
            const button = el("button", { type: "button", textContent: choice === "auto" ? t.auto : choice });
            button.dataset.layer = layer.id;
            button.dataset.choice = choice;
            button.addEventListener("click", () => handlers.choose(layer.id, choice));
            group.append(button);
          }
          return el("div", { className: "res-row" }, el("span", { className: "res-label" }, layer.title[state.lang]), group);
        }),
    );
    const credits = root.querySelector<HTMLElement>(".credits") as HTMLElement;
    credits.replaceChildren(
      el("span", { className: "credits-head" }, t.credits),
      ...catalog.layers.map((layer) => el("span", {}, layer.credit[state.lang])),
    );
  }

  return (state, t) => {
    if (state.lang !== lang) {
      lang = state.lang;
      build(t, state);
    }
    for (const toggle of list.querySelectorAll<HTMLInputElement>("input.toggle")) {
      toggle.checked = !state.hidden.has(toggle.dataset.layer as string);
    }
    for (const range of list.querySelectorAll<HTMLInputElement>("input[type=range]")) {
      const value = String(Math.round((state.opacity[range.dataset.layer as string] ?? 1) * 100));
      if (range.value !== value) range.value = value;
      const output = range.nextElementSibling as HTMLOutputElement;
      output.value = value;
    }
    for (const button of resolutions.querySelectorAll<HTMLButtonElement>("button")) {
      const choice = state.choices[button.dataset.layer as string] ?? "auto";
      button.setAttribute("aria-pressed", String(choice === button.dataset.choice));
    }
  };
}
