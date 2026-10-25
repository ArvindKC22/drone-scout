# Third-party notices

Drone Scout's own code is MIT-licensed ([`LICENSE`](LICENSE)). **No third-party source code, dataset image or model is bundled in the code or in the simulators.** The only third-party material in this repository is reproduced inside the technical report PDF and in three screenshots taken from it (see "What is redistributed here"). Everything else is cited and linked.

Licence information below was read from each project's own GitHub page on 25 October 2026. Licences can change and a page's label is not a substitute for reading the licence file; check the upstream project before you reuse anything, especially commercially.

## Resources used by the technical report

| Resource | Role in the report | Licence stated upstream | Obligations that matter here |
|---|---|---|---|
| [FIELDimageR](https://github.com/OpenDroneMap/FIELDimageR) (Matias, Caraza-Harter & Endelman, 2020) | Source of the potato orthomosaic derivative; method reference | GPL-2.0 | Not incorporated. Cite the paper if you use the package. |
| [ADD256, Embrapa Apples by Drones Detection Dataset](https://github.com/thsant/add256) (Santos & Gebler, 2021) | Apple images and circle annotations in the Data Library | Data under **CC BY-NC 4.0**; upstream asks commercial users to contact Embrapa Agricultural Informatics | Attribution required, **non-commercial use only**. Cite the paper. A few ADD256 thumbnails appear in report figures (attribution given here). |
| [CoFly-WeedDB](https://github.com/CoFly-Project/CoFly-WeedDB) (Krestenitis et al., 2022) | Weed images, masks and overlays | GPL-3.0 (as shown on the repository page) | Not redistributed. Cite the *Data in Brief* paper. |
| [CADI-AI, KaraAgro](https://github.com/karaagro/cadi-ai) | Cashew test-subset images with YOLO annotations | Dataset, model and demo stated as AGPL-3.0 | Not redistributed. AGPL asks derived projects to share alike, so treat any reuse of its data carefully. |
| [WebODM / OpenDroneMap](https://github.com/OpenDroneMap/WebODM) | Origin of the multispectral frame transect | WebODM: AGPL-3.0 | Not incorporated. WebODM is a trademarked name; see its `TRADEMARK.md`. |
| [DJI Phantom 4 Multispectral](https://www.dji.com/p4-multispectral) | Reference airframe and camera values (battery, speeds, GSD relation) | Proprietary manufacturer specifications; no open licence | Specifications are factual parameters used for modelling. DJI and Phantom are trademarks of SZ DJI Technology. **This project is not affiliated with, endorsed by or sponsored by DJI.** |
| Cherry-orchard imagery and TreeMapping workbooks | Local UF/IFAS project data | Not stated in the report | Not redistributed. Add the correct terms before sharing any of it. |

Full references with DOIs: [`docs/REFERENCES.bib`](docs/REFERENCES.bib).

## What is redistributed here

- `docs/Drone_Scout_Technical_Thesis_Report.pdf` and `assets/report-*.jpg`: figures from the report. Some show ADD256 apple imagery and dataset inventory screens. Those pixels remain subject to **CC BY-NC 4.0** (attribution: Santos & Gebler, Embrapa). Keep this repository non-commercial in that respect or remove those figures before commercial reuse.
- Report text, original figures and the generated plots are covered by [`LICENSE-DOCS.md`](LICENSE-DOCS.md), except for third-party content as described above.

## Related open-source projects

[`docs/RELATED_PROJECTS.md`](docs/RELATED_PROJECTS.md) lists autopilot, ground-station, simulation and photogrammetry projects that are the natural route to physical validation. They are linked, not copied.

## Python dependencies

| Package | Licence (upstream) |
|---|---|
| NumPy | BSD-3-Clause |
| Matplotlib (optional, plots) | Matplotlib licence (BSD-style) |

Both are installed from PyPI, not vendored.

## Takedown / corrections

If you are a rights holder and believe something here is mis-attributed or should not be redistributed, open an issue and it will be fixed promptly.
