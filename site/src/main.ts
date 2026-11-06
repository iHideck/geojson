// 最初に読む小さな入口。画面の文言を先に差し込み、MapLibre を含む地図の部分は、そのあとで読む
import "./styles.css";
import { applyTexts, preferredLang, strings } from "./i18n.ts";
import type { Lang } from "./state.ts";

const defaultLang = preferredLang();
const fromUrl = /(?:^#|&)lang=(ja|en)(?:&|$)/.exec(location.hash)?.[1] as Lang | undefined;
const lang = fromUrl ?? defaultLang;
applyTexts(strings(lang), lang);

// 文字だけの画面を先に描いてから、地図の部分を読む。地図の組み立ては重く、そのあいだは画面を描けない
requestAnimationFrame(() =>
  requestAnimationFrame(() => {
    import("./app.ts")
      .then(({ start }) => start(defaultLang))
      .catch((error: unknown) => {
        document.body.dataset.error = "1";
        const status = document.querySelector<HTMLElement>("#status");
        if (status) {
          status.hidden = false;
          status.textContent = strings(lang).loadError;
        }
        console.error(error);
      });
  }),
);
