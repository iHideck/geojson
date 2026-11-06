# VLIZ への再配布の確認メール（下書き）

Marine Regions の海域データを、このリポジトリで配布・表示してよいかを VLIZ に確かめるためのメールです。送るのはリポジトリの管理者です。

VLIZ から、このメールの使い方のすべてについて、問題ないとの返事を得ました。許可の範囲と、守ることは `docs/license-review.md` にあります。

- 送り先は info@marineregions.org です（Marine Regions の Disclaimer ページの問い合わせ先）。
- 送る前に、`<...>` の部分を埋めます。
- 返事を受けたら、許可の範囲と条件を `docs/license-review.md` に書き写し、返事のメールを保存しておきます。許可の範囲に入る形式と配信先だけを、feature flag で有効にします。
- 選択肢 A〜C は、全部の許可が得られない場合でも、一部だけ許可してもらえるようにするためのものです。

```text
Subject: Permission request: redistributing simplified Marine Regions maritime boundaries in an open-data repository

Dear Marine Regions team,

I maintain "geojson", an open-data repository of lightweight boundary data for Japan and the world:
https://github.com/iHideck/geojson

The repository publishes simplified boundaries that can be overlaid on one consistent basis, together with a static web map viewer ("Midnight Chart") on GitHub Pages:
https://ihideck.github.io/geojson/

It is free of charge, has no advertising or sales, and collects no user data. The code is MIT-licensed. Each dataset keeps its original license and attribution.

Your disclaimer page asks users not to make Marine Regions products available for download elsewhere. Because of that, the repository does not include any Marine Regions data yet. The processing code exists, but it is switched off. I would like to ask whether the uses below are acceptable to you.

1. Datasets
   - Maritime Boundaries v12: Exclusive Economic Zones (200NM), and the EEZ boundary lines
   - Territorial Seas (12NM), version 4
   - Contiguous Zones (24NM), version 4
   - High Seas, version 2
   - Internal Waters, version 4, and Archipelagic Waters, version 4, only to derive straight and archipelagic baselines as lines

2. Processing
   - Simplification to two small-scale levels, comparable to Natural Earth 1:50m and 1:110m, with topology preserved.
   - Coordinates rounded to 5 decimal places (1:50m level) and 4 decimal places (1:110m level).
   - Attributes reduced to names, ISO 3166-1 codes, and your feature identifiers (for example MRGID).
   - Features that cross the 180th meridian split so that they display correctly.
   - No full-resolution data would be redistributed. Users who need detailed shapes would be sent to marineregions.org.

3. Distribution and display
   a) Downloadable files of the simplified data in GeoJSON, TopoJSON, GeoPackage, Shapefile, FlatGeobuf, and GeoParquet, published in the GitHub repository, as GitHub Release assets, on GitHub Pages, and possibly as an npm package.
   b) Display in the web map viewer. For this, the simplified data would be converted to PMTiles (vector tiles in a single file) and served from GitHub Pages. The viewer reads the file with HTTP range requests, so the file itself would be publicly reachable.
   c) A QGIS project file and styles that load the simplified layers.

4. Attribution
   Every file, the metadata, the README, and the viewer would carry your preferred citation, the DOI of each product, the CC BY 4.0 license, a link to https://www.marineregions.org, and a note that the data was simplified. For example:
   "Flanders Marine Institute (2023). Maritime Boundaries Geodatabase: Maritime Boundaries and Exclusive Economic Zones (200NM), version 12. Available online at https://www.marineregions.org/. https://doi.org/10.14284/632 Simplified by the geojson project."

5. Disclaimers
   The repository and the viewer state that the boundaries have no legal value and must not be used for navigation, legal, or economic purposes, in line with your terms of use.

6. Build process
   The build script would download the source files from marineregions.org when the data is rebuilt, a few times per year at most. May the script download them automatically, and if so, which URL or service do you prefer (the download page or your web services)?

Questions
   - Do you permit each of the uses in 3 a), b), and c)?
   - If you cannot permit all of them, would you permit one of these narrower options?
     A. Display only: PMTiles for the viewer (3 b), with no download links and no files in releases or npm.
     B. Options 3 a) and 3 b), limited to a region around Japan (for example 120°E to 160°E, 20°N to 50°N).
     C. Another scope that you suggest.
   - Do you have conditions on wording, versions, or update frequency?
   - Is the build process in 6 acceptable?

I will follow your answer exactly and keep the data switched off until I hear from you. I am happy to send more details or a preview.

Best regards,
<Your name>
<Contact email>
https://github.com/iHideck/geojson
```

## 送る前に確かめること

1. `https://ihideck.github.io/geojson/` が、送る時点で開けるかを確かめます。まだ公開していなければ、2段落目の URL の行を消すか、「will be published at」と書き換えます。
2. 依頼する地域（選択肢 B の範囲）が、ビューアで見せたい範囲と合っているかを確かめます。
3. 名前と連絡先を入れます。
