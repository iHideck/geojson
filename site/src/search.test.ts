import assert from "node:assert/strict";
import { test } from "node:test";
import { normalize, type SearchIndex, search } from "./search.ts";

const box: [number, number, number, number] = [0, 0, 1, 1];
const INDEX: SearchIndex = {
  layers: {
    "world/countries": [
      { iso_a2: "JP", iso_a3: "JPN", iso_n3: "392", name_ja: "日本", name_en: "Japan", bbox: box },
      { iso_a2: "KR", iso_a3: "KOR", iso_n3: "410", name_ja: "大韓民国", name_en: "South Korea", bbox: box },
    ],
    "japan/islands": [
      { name_ja: "沖縄島", name_kana: "おきなわじま", name_en: "Okinawa Island", lg_codes: "472018,473146", bbox: box },
      { name_ja: "大島", name_kana: "おおしま", name_en: "Oshima", bbox: box },
      { name_ja: "伊豆大島", name_kana: "いずおおしま", name_en: "Izu Oshima", bbox: box },
    ],
  },
};

test("全角・半角、大文字・小文字、カタカナ・ひらがなの違いを無くす", () => {
  assert.equal(normalize("ＪＰＮ"), "jpn");
  assert.equal(normalize("オオシマ"), "おおしま");
  assert.equal(normalize(" Izu  Oshima "), "izuoshima");
});

test("コードは完全に一致したものだけを返し、カンマ区切りのコードも一つずつ見る", () => {
  assert.deepEqual(
    search(INDEX, "jpn").map((h) => h.entry.name_ja),
    ["日本"],
  );
  assert.deepEqual(
    search(INDEX, "473146").map((h) => h.entry.name_ja),
    ["沖縄島"],
  );
  assert.deepEqual(search(INDEX, "39"), []);
});

test("名前は、一致・前方一致・部分一致の順に並べる", () => {
  assert.deepEqual(
    search(INDEX, "おおしま").map((h) => h.entry.name_ja),
    ["大島", "伊豆大島"],
  );
  assert.deepEqual(
    search(INDEX, "oshima").map((h) => [h.layer, h.index]),
    [
      ["japan/islands", 1],
      ["japan/islands", 2],
    ],
  );
});
