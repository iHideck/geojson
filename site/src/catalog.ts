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
