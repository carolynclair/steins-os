# Licensing and credits

Steins;OS combines original project work with independently maintained Linux
software. The root [LICENSE](LICENSE) covers original project code under MIT;
more specific component notices take precedence.

| Material | Terms and attribution |
| --- | --- |
| Original scripts, QML, UI code and vector UI geometry | MIT, Steins;OS contributors, unless a component states otherwise |
| Original illustrated worldline wallpapers in `design/*/art/` and `prototype/artwork-v3/` | CC BY 4.0, Steins;OS contributors; provenance accompanies the artwork |
| Original wallpaper assets and Steins;OS emblem under `config/includes.chroot/` | CC BY 4.0, Steins;OS contributors |
| V4 semantic icon family | CC BY 4.0, Steins;OS contributors; see `prototype/identity-v4/PROVENANCE.json` and its generated package copyright |
| New native panel SVG geometry | MIT; see `prototype/panel-v4/README.md` |
| Original screenshots and documentation | MIT for project documentation; screenshots also depict separately licensed upstream software |
| Upstream Plymouth source extracts under `prototype/startup/evidence/upstream-*` | GPL-2.0-or-later; the upstream copyright/license and provenance are retained alongside the extracts |

CC BY 4.0 license text: <https://creativecommons.org/licenses/by/4.0/>.
Attribution example: “Steins;OS artwork by Steins;OS contributors, CC BY 4.0.”
Retain the component's attribution and describe modifications when adapting it.

The terminal frontend source has an MIT notice. Its packaged executable links
against the GPL-2.0-or-later QTermWidget engine, so binary redistribution follows
that combination's GPL obligations. The terminal build includes frontend source,
build instructions and the Debian engine license record. See
[the terminal documentation](prototype/surfaces-v4/terminal/README.md).

Debian, Linux, KDE Plasma, XFCE, Calamares, GRUB, Plymouth, Thunderbird, Breeze,
Papirus and fonts retain their own licenses and trademarks. Inherited icon and
desktop themes are dependencies, rather than relicensed project assets. A binary
ISO release must preserve its package notices and corresponding-source strategy;
see [the release procedure](docs/RELEASE.md).

This is an independent fan-inspired project. It is not affiliated with or endorsed
by the creators or rights holders of Steins;Gate or other referenced stories.
No official anime screenshots, character artwork, music or voice recordings are
included in this source publication.
