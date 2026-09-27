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

## Baixar e usar (sem instalar nada)

Vá em **Actions** no repositório no GitHub → abra a execução mais recente
de **"Build SkyForge.exe (Windows, for dummies)"** → baixe o artefato
**`SkyForge-windows`** → extraia → dê duplo clique em `SkyForge.exe`.

Não precisa instalar Python, PySide6 nem o `cmft` separadamente — tudo já
vem embutido num único executável (gerado via PyInstaller,
`build_windows.spec`). Esse é o caminho recomendado pra quem só quer usar
o programa; as seções abaixo (Setup, compilar o `cmft`) são só pra quem
vai mexer no código.

## Status

Pipeline de conversão funcional, testado com fotos reais e **validado
dentro do jogo (PrimeXT)**: `ft`/`bk`/`rt`/`lf`/`up` já confirmados sem
costura visível — só `dn` ainda não foi testado em jogo (raramente
visível, coberto por terreno na maioria dos mapas). Detalhes em
`docs/DECISOES.md`.

Testado até agora só via linha de comando/scripts em Linux. A GUI
(`main.py`) ainda não foi rodada de verdade em Windows, que é onde o mod
roda — ver seção de build abaixo.

## Setup (para desenvolvimento)

```bash
git clone --recurse-submodules https://github.com/Hidrocarbono/skyforge
cd skyforge
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Compilar o `cmft`

O SkyForge chama o binário `cmft_cli` como processo externo — precisa ser
compilado uma vez, não vem pronto no repositório.

**Linux** (testado nesta sessão de desenvolvimento):

```bash
cd external/cmft
chmod +x dependency/bx/tools/bin/linux/genie
./dependency/bx/tools/bin/linux/genie --file=scripts/main.lua --gcc=linux-gcc gmake
cd _projects/gmake-linux
make config=release64 cmft_cli
```

O binário fica em `external/cmft/_build/linux64_gcc/bin/cmftRelease` (nome
interno do alvo `cmft_cli`, não é engano — ver comentário em
`src/skyforge/cmft_wrapper.py`).

**Windows (cmft.exe)**: a forma mais simples e já validada não é compilar
no próprio Windows — é baixar o `.exe` pronto do **GitHub Actions**
(`.github/workflows/build-cmft-windows.yml`), que compila via
cross-compilação a cada push relevante. Vá em **Actions** no repositório
no GitHub, abra a execução mais recente de "Build cmft.exe (Windows)" e
baixe o artefato `cmft-windows-x64`.

Por que não compilar direto no Windows: o `cmft` tem um bug de detecção de
compilador que confunde qualquer GCC/MinGW mirando Windows com MSVC
(`_WIN32` é checado antes de `__GNUC__`), quebrando a build com MinGW
nativo do mesmo jeito que quebraria cruzando do Linux. **Corrigido** via
`patches/cmft-fix-mingw-compiler-detection.patch` (aplicado automaticamente
pelo workflow do GitHub Actions) — ver o cabeçalho do patch pra detalhes.
Testado nesta sessão: compilado por cross-compilação (`mingw-w64` no
Linux) e **rodado de verdade sob Wine**, convertendo um panorama real com
sucesso.

Se preferir compilar você mesmo em vez de baixar do Actions (Linux, com
`mingw-w64` instalado):
```bash
git -C external/cmft apply ../../patches/cmft-fix-mingw-compiler-detection.patch
cd external/cmft
x86_64-w64-mingw32-g++ -std=c++11 -msse2 -fno-rtti -fno-exceptions -O2 \
  -D__STDC_LIMIT_MACROS -D__STDC_FORMAT_MACROS -D__STDC_CONSTANT_MACROS \
  -Idependency -Isrc/cmft -Isrc -Iinclude \
  src/cmft/allocator.cpp src/cmft/cubemapfilter.cpp src/cmft/clcontext.cpp \
  src/cmft/image.cpp src/cmft/common/stb_image.cpp src/cmft/common/print.cpp \
  src/main.cpp -o cmft.exe -static -lgdi32 -lopengl32
```

Em qualquer plataforma: aponte a variável de ambiente `SKYFORGE_CMFT_PATH`
pro binário compilado, ou informe o caminho na própria GUI.

## Rodar

```bash
python3 main.py
```

Ao abrir, aparece uma tela de carregamento (splash) com o logo do
SkyForge por ~1,2s antes da janela principal — gerada por
`scripts/gen_splash.py` (PIL puro, sem asset externo; rode de novo se
quiser mudar o visual).

## Arquitetura

```
src/skyforge/
├── cmft_wrapper.py     # monta e chama o cmft (--output0params tga,bgra8,facelist)
├── goldsrc_export.py   # renomeia posx/negx/... -> ft/bk/up/dn/rt/lf (VER AVISO NO ARQUIVO)
├── pipeline.py          # orquestra: seam_check -> pole_treatment -> cmft -> goldsrc_export
├── pole_treatment.py   # tratamento de baixa-frequência da face `up`/`dn`
├── seam_check.py       # valida a costura de longitude do equirect de entrada
└── testpattern.py      # gera padrão de teste rotulado por face, p/ validar orientação em jogo
gui/
├── main_window.py      # janela PySide6 (entrada, parâmetros, preview, log, progresso)
└── assets/splash.png   # tela de carregamento, gerada por scripts/gen_splash.py
scripts/
└── gen_splash.py       # gera gui/assets/splash.png (reprodutível, sem asset externo)
patches/
└── cmft-fix-mingw-compiler-detection.patch  # corrige bug de deteção de compilador do cmft
build_windows.spec       # empacota tudo (app + cmft.exe) num SkyForge.exe unico (PyInstaller)
requirements-build.txt   # requirements.txt + pyinstaller
.github/workflows/
├── build-cmft-windows.yml     # compila so o cmft.exe (cross-compile) a cada push relevante
└── build-skyforge-windows.yml # empacota o SkyForge.exe completo (2 jobs: cmft + PyInstaller)
```

### Gerar o `.exe` empacotado você mesmo (em vez de baixar do Actions)

Precisa rodar no Windows (PyInstaller empacota o próprio interpretador
Python, não dá pra cross-compilar isso do Linux, diferente do `cmft.exe`):

```
pip install -r requirements-build.txt
# coloque um cmft.exe compilado na raiz do repo antes deste passo
pyinstaller --noconfirm build_windows.spec
```

Resultado em `dist/SkyForge.exe`.

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
