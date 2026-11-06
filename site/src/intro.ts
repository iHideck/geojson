import type { Map as MapLibreMap, PaddingOptions } from "maplibre-gl";
import { STAGES } from "./state.ts";

// 演出の段階を見せ始める時間（ミリ秒）。i 番目で段階 i + 1 を見せる
const SCHEDULE = [0, 700, 2300, 3400];
const FLIGHT_MS = 5200;
const START = { center: [158, 18] as [number, number], zoom: 1.15 };

export type View = { center: [number, number]; zoom: number; padding: PaddingOptions };

/** 日本を見せる最初の位置。パネルやボトムシートに隠れないよう、余白をとる。 */
export function homeView(): View {
  if (matchMedia("(max-width: 640px)").matches) {
    return {
      center: [137.2, 36.2],
      zoom: 3.85,
      // スマートフォンでは、凡例をたたんだボトムシートと読み取りの分だけ下を空ける
      padding: { top: 120, bottom: 130, left: 0, right: 0 },
    };
  }
  return { center: [138.2, 36.4], zoom: 4.85, padding: { top: 80, bottom: 40, left: 330, right: 60 } };
}

export type Intro = {
  // 演出を終わりの状態にする。home なら日本の位置へ飛ぶ（利用者が地図を動かしたときは飛ばない）
  end(home: boolean): void;
};

/** 地球全体から日本へ移りながら、境界を順に見せる。 */
export function playIntro(map: MapLibreMap, reveal: (stage: number) => void, done: () => void): Intro {
  const view = homeView();
  map.jumpTo(START);
  const timers = SCHEDULE.map((at, i) => setTimeout(() => reveal(i + 1), at));
  let finished = false;
  const finish = (): void => {
    if (finished) return;
    finished = true;
    for (const timer of timers) clearTimeout(timer);
    reveal(STAGES);
    done();
  };
  map.flyTo({ ...view, duration: FLIGHT_MS, curve: 1.25, essential: true });
  map.once("moveend", finish);
  return {
    end(home) {
      if (finished) return;
      if (home) {
        map.stop();
        map.jumpTo(view);
      }
      finish();
    },
  };
}
