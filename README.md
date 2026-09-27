# SkyForge

Ferramenta com GUI para transformar um panorama equirectangular (2:1), já
tratado por IA para ter continuidade mínima, num skybox de 6 faces no
formato clássico GoldSrc/Xash3D (`ft/bk/up/dn/rt/lf.tga`).

Sucessor espiritual do antigo SkyPaint, com duas diferenças centrais:

1. Usa o [`cmft`](https://github.com/dariomanesku/cmft) (BSD-2-Clause) como
   motor de reprojeção equirect → cubemap, em vez de reimplementar a
   matemática de projeção do zero.
2. Trata a face `up` (zênite) de forma diferente das outras 5 — é o ponto
   de maior distorção da projeção equirectangular e o mais exposto ao
   jogador (ver `docs/DECISOES.md`).

## Status

Protótipo inicial. Pipeline de conversão funcional (equirect → 6 faces
nomeadas), tratamento de polo e checagem de costura ainda em ajuste. A
correspondência de orientação `cmft` → GoldSrc (`goldsrc_export.py`) **ainda
não foi validada empiricamente em jogo** — ver aviso no próprio módulo.

## Setup

```bash
git clone --recurse-submodules https://github.com/Hidrocarbono/skyforge
cd skyforge
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Compilar o `cmft`

O SkyForge chama o binário `cmft_cli` como processo externo. Compilar (Linux):

```bash
cd external/cmft
chmod +x dependency/bx/tools/bin/linux/genie
./dependency/bx/tools/bin/linux/genie --file=scripts/main.lua --gcc=linux-gcc gmake
cd _projects/gmake-linux
make config=release64 cmft_cli
```

O binário fica em `external/cmft/_build/linux64_gcc/bin/cmftRelease` (nome
interno do alvo `cmft_cli`, não é engano — ver comentário em
`src/skyforge/cmft_wrapper.py`). Aponte `SKYFORGE_CMFT_PATH` para esse
caminho, ou informe na GUI.

## Rodar

```bash
python3 main.py
```

## Arquitetura

```
src/skyforge/
├── cmft_wrapper.py     # monta e chama o cmft (--output0params tga,bgra8,facelist)
├── goldsrc_export.py   # renomeia posx/negx/... -> ft/bk/up/dn/rt/lf (VER AVISO NO ARQUIVO)
├── pole_treatment.py   # tratamento de baixa-frequência da face `up`/`dn`
├── seam_check.py       # valida a costura de longitude do equirect de entrada
└── testpattern.py      # gera padrão de teste rotulado por face, p/ validar orientação em jogo
gui/
└── main_window.py      # janela PySide6
```

Decisões e debate técnico completo que levou a essa arquitetura:
`docs/DECISOES.md`.

## Créditos

O SkyForge é construído em cima do trabalho de outras pessoas e depende
diretamente do [`cmft`](https://github.com/dariomanesku/cmft) (Dario
Manesku, BSD-2-Clause) como motor de conversão — nenhuma matemática de
reprojeção equirect→cubemap foi reimplementada aqui. Lista completa de
dependências, autores e licenças (bibliotecas Python inclusas):
**[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)**.

A mesma lista também aparece dentro do programa, no menu **Ajuda → Sobre**.
