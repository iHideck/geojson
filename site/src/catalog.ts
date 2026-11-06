// GitHub Pages の latest/catalog.json。データを作る側（scripts/boundaries/site_index.py）が書く

export type Text = { ja: string; en: string };

export type Resolution = {
  id: string;
  minzoom: number;
  maxzoom: number;
  // サイトの根からの相対パス
  pmtiles: string;
};

export type CatalogLayer = {
  id: string;
  title: Text;
  geometry: "polygon" | "line" | "point";
  // 海域。区域どうしが重なり、borders に外側の限界も入る
  outlined: boolean;
  credit: Text;
  license: string;
  metadata: string;
  // 細かい順に並ぶ
  resolutions: Resolution[];
};

export type Catalog = { layers: CatalogLayer[] };

export async function loadCatalog(base: string): Promise<Catalog> {
  const response = await fetch(`${base}latest/catalog.json`);
  if (!response.ok) {
    throw new Error(`目録を読めない（${response.status}）`);
  }
  return (await response.json()) as Catalog;
}

// PMTiles の地物の番号は、tippecanoe の --generate-ids が入力の順に 1 から振る。検索の索引の行は 0 から数える
export const featureIndex = (id: number | string): number => Number(id) - 1;
export const featureId = (index: number): number => index + 1;
