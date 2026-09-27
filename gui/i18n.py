"""Traducoes da interface do SkyForge (pt-BR / en-US).

Simples de proposito: um dict por idioma, chaves em ingles descrevendo o
elemento. MainWindow guarda o idioma atual e chama retranslate() pra
reaplicar os textos em todos os widgets quando o usuario troca no menu.
"""

from __future__ import annotations

LANGUAGES = {
    "pt": "🇧🇷 Português",
    "en": "🇺🇸 English",
}

DEFAULT_LANGUAGE = "pt"

_STRINGS: dict[str, dict[str, str]] = {
    "pt": {
        "window_title": "SkyForge",
        "menu_help": "&Ajuda",
        "menu_about": "&Sobre o SkyForge",
        "menu_language": "&Idioma",
        "group_input": "Entrada",
        "browse_input": "Selecionar panorama...",
        "file_filter_input": "Imagens (*.png *.jpg *.jpeg *.tga *.bmp)",
        "dialog_select_input": "Selecionar panorama equirectangular",
        "group_params": "Parâmetros",
        "label_sky_name": "Nome do sky:",
        "label_face_size": "Resolução por face:",
        "check_pole_fix": "Tratamento de polo (zênite/nadir)",
        "group_output": "Saída",
        "browse_output": "Selecionar pasta de saída...",
        "dialog_select_output": "Selecionar pasta de saída",
        "run_button": "Gerar skybox",
        "group_preview": "Preview das faces",
        "warn_no_input": "Selecione um panorama de entrada primeiro.",
        "warn_no_output": "Selecione uma pasta de saída primeiro.",
        "log_starting": "Iniciando pipeline...",
        "log_seam": "Costura de longitude: diff média={diff:.1f} (provavelmente visível: {visible})",
        "log_exported": "6 faces exportadas em: {path}",
        "log_done": "Concluído.",
        "log_error": "ERRO: {message}",
        "about_html": """\
<h3>SkyForge {version}</h3>
<p>Ferramenta para gerar skyboxes de 6 faces (convenção GoldSrc/Xash3D) a
partir de panoramas equirectangulares.</p>
<p><b>Autores da versão inicial ({version}):</b> Hidrocarboneto e Claude
(Anthropic).</p>
<p><b>Licença:</b> MIT — gratuito, a comunidade pode adaptar como quiser,
sem responsabilidade dos autores por danos de qualquer tipo; só exige
manter os créditos da versão original. Texto completo em
<code>LICENSE</code> no repositório.</p>
<p><b>Construído em cima do trabalho de terceiros:</b></p>
<ul>
<li><a href="https://github.com/dariomanesku/cmft">cmft</a> — Dario Manesku
    (BSD-2-Clause). Motor de reprojeção equirect→cubemap; o SkyForge
    não reimplementa essa matemática.</li>
<li><a href="https://pypi.org/project/PySide6/">PySide6</a> — The Qt
    Company (LGPLv3). Interface gráfica.</li>
<li><a href="https://numpy.org/">NumPy</a> — NumPy Developers
    (BSD-3-Clause).</li>
<li><a href="https://python-pillow.org/">Pillow</a> — Jeffrey A. Clark e
    colaboradores (HPND).</li>
</ul>
<p>Sucessor espiritual do antigo <b>SkyPaint</b> da comunidade GoldSrc
(inspiração de fluxo de trabalho, nenhum código reaproveitado).</p>
<p>Lista completa de créditos e licenças:
<code>THIRD_PARTY_NOTICES.md</code> no repositório.</p>
""",
    },
    "en": {
        "window_title": "SkyForge",
        "menu_help": "&Help",
        "menu_about": "&About SkyForge",
        "menu_language": "&Language",
        "group_input": "Input",
        "browse_input": "Select panorama...",
        "file_filter_input": "Images (*.png *.jpg *.jpeg *.tga *.bmp)",
        "dialog_select_input": "Select equirectangular panorama",
        "group_params": "Parameters",
        "label_sky_name": "Sky name:",
        "label_face_size": "Resolution per face:",
        "check_pole_fix": "Pole treatment (zenith/nadir)",
        "group_output": "Output",
        "browse_output": "Select output folder...",
        "dialog_select_output": "Select output folder",
        "run_button": "Generate skybox",
        "group_preview": "Face preview",
        "warn_no_input": "Select an input panorama first.",
        "warn_no_output": "Select an output folder first.",
        "log_starting": "Starting pipeline...",
        "log_seam": "Longitude seam: mean diff={diff:.1f} (likely visible: {visible})",
        "log_exported": "6 faces exported to: {path}",
        "log_done": "Done.",
        "log_error": "ERROR: {message}",
        "about_html": """\
<h3>SkyForge {version}</h3>
<p>Tool for generating 6-face skyboxes (GoldSrc/Xash3D convention) from
equirectangular panoramas.</p>
<p><b>Original version authors ({version}):</b> Hidrocarboneto and Claude
(Anthropic).</p>
<p><b>License:</b> MIT — free, the community may adapt it however they
like, with no liability for the authors of any kind; the only requirement
is keeping credit for the original version. Full text in
<code>LICENSE</code> in the repository.</p>
<p><b>Built on top of other people's work:</b></p>
<ul>
<li><a href="https://github.com/dariomanesku/cmft">cmft</a> -- Dario
    Manesku (BSD-2-Clause). Equirect&rarr;cubemap reprojection engine;
    SkyForge does not reimplement this math.</li>
<li><a href="https://pypi.org/project/PySide6/">PySide6</a> -- The Qt
    Company (LGPLv3). GUI.</li>
<li><a href="https://numpy.org/">NumPy</a> -- NumPy Developers
    (BSD-3-Clause).</li>
<li><a href="https://python-pillow.org/">Pillow</a> -- Jeffrey A. Clark
    and contributors (HPND).</li>
</ul>
<p>Spiritual successor to the old GoldSrc community tool
<b>SkyPaint</b> (workflow inspiration only, no code reused).</p>
<p>Full credits and license list:
<code>THIRD_PARTY_NOTICES.md</code> in the repository.</p>
""",
    },
}


def tr(lang: str, key: str, **kwargs) -> str:
    text = _STRINGS[lang][key]
    return text.format(**kwargs) if kwargs else text
