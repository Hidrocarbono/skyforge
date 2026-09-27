# Decisões de arquitetura do SkyForge

Registro resumido do debate técnico que definiu esta arquitetura (conversa
completa no histórico do projeto `road-to-nowhere`).

## Contexto

O objetivo original era gerar skyboxes de 6 faces em altíssima resolução
para o mod PrimeXT/Xash3D (`road-to-nowhere`), a partir de fotos de locais
reais com falhas de continuidade entre as faces.

## Decisões fechadas

1. **Fonte de imagem**: foto → panorama equirectangular 2:1 gerado/tratado
   por IA **fora** do SkyForge (serviços como PanoPulse, PanoramaGenerator
   etc.). O SkyForge só consome o panorama já pronto — não embute geração
   por IA.
2. **Motor de reprojeção**: [`cmft`](https://github.com/dariomanesku/cmft)
   (BSD-2-Clause), em vez de reimplementar a matemática equirect→cubemap.
   Testado empiricamente (compilado e rodado de verdade, não só lido da
   documentação) — aceita TGA de entrada e saída, controla resolução via
   `--srcFaceSize`/`--dstFaceSize`.
3. **Ponto crítico de qualidade**: a face `up` (zênite). A projeção
   equirectangular diverge nos polos — uma faixa fina no topo/base da
   imagem vira uma face quadrada inteira, amplificando qualquer ruído em
   artefato radial. É também a face mais exposta ao jogador (olha pra cima
   com frequência; `dn` raramente aparece, geralmente coberto por
   terreno). Tratamento: suavizar a faixa polar do equirect e misturar com
   um gradiente de cor extraído dali, **antes** da conversão pelo `cmft`
   (`pole_treatment.py`) — não depois, na face quadrada já reprojetada.
4. **Camada de nuvem** (já existente no mod, `clouds.tga` +
   `skybox_fp.glsl`) é complementar, não corretiva — não cobre 100% do
   céu, então não pode mascarar defeito na textura base.
5. **Stack**: Python 3 + PySide6 (GUI) + NumPy/Pillow (processamento de
   imagem), chamando o `cmft` como processo externo via `subprocess`.
   Motivo: iteração rápida, mesma linguagem já usada nos scripts de asset
   do mod, licença LGPL do PySide6 compatível com projeto aberto.

## Pendências conhecidas (ver avisos nos módulos)

- **`goldsrc_export.py`**: o mapeamento `posx/negx/.../negz` (nomeação do
  `cmft`) → `ft/bk/up/dn/rt/lf` (convenção GoldSrc) é uma hipótese pros
  eixos X/Z, não validada em jogo. Duas tentativas de atalho já mostraram
  que não dá pra resolver isso sem carregar o resultado no jogo de fato:
  (1) leitura visual de screenshot gerou conclusão errada (troca acidental
  entre duas imagens parecidas); (2) medição programática da cor dominante
  de cada face (mais confiável que olho humano) confirmou os eixos `up`/`dn`
  corretamente, mas revelou que o `cmft` usa uma convenção de longitude
  diferente da fórmula esférica padrão pros eixos X/Z — ou seja, mesmo a
  medição numérica só prova que `testpattern.py` e o `cmft` usam
  convenções de eixo diferentes entre si, não qual direção física deve
  virar `ft`/`bk`/`rt`/`lf` no jogo. Essa correspondência semântica só se
  resolve carregando em `gfx/env/` e olhando no jogo/pxmv.
- **`pole_treatment.py`**: `blend_weight`/`band_fraction`/`blur_radius`
  são chutes iniciais razoáveis, não calibrados contra percepção humana
  real — precisam de ajuste visual iterativo com panoramas reais.
  **Teste com foto real já revelou um problema concreto**: a primeira
  versão usava corte reto na borda da faixa tratada, e isso virou um
  **disco de borda dura bem visível** nas faces `up`/`dn` depois de
  reprojetado — pior do que não tratar nada, porque a foto (já gerada por
  IA) já vinha com pouco detalhe de alta frequência no céu por conta
  própria. Corrigido trocando o corte reto por uma queda suave
  (`smoothstep`, peso vai a zero exatamente na borda da faixa). Resultado
  após a correção: `up` ficou idêntico à versão sem tratamento nenhum
  (ótimo — o tratamento parou de atrapalhar); `dn` melhorou (sem mais
  borda dura) mas ainda mostra uma mancha suave visível, porque o chão
  tem mais contraste natural que o céu e uma média de cor se destaca mais
  ali. Como `dn` é a face menos exposta ao jogador (normalmente coberta
  por terreno), isso ficou como ajuste fino pendente, não bloqueante.
- **`seam_check.py`**: só mede e relata, não corrige — corrigir
  automaticamente entra na categoria "mitigação heurística, nunca
  garantida" (uma foto real pode ter descontinuidade genuína de
  conteúdo, não só de tom).
- Teto real de resolução por face aceito pelo fork do engine
  (`Hidrocarbono/xash3d-fwgs`) ainda não foi confirmado — fora do escopo
  deste repositório.

## Primeiro teste real em jogo (PrimeXT)

Skybox gerado a partir da foto real do usuário, carregado de verdade em
`gfx/env/` e testado no jogo (não só inspeção de arquivo isolado):

- **`ft`/`bk`/`rt`/`lf`**: sem emenda aparente entre as faces do "anel"
  equatorial. O mapeamento de eixo X/Z (hipótese, nunca validado) parece
  estar correto o bastante para essas 4 faces — ou ao menos consistente
  entre si.
- **`up`**: **linha de costura visível em diagonal** cortando as nuvens,
  nas 4 screenshots enviadas. Diagnóstico: como o "anel" das 4 faces
  laterais fecha sem emenda entre si, mas a transição para `up`
  especificamente mostrava descontinuidade, isso apontava para
  **rotação/orientação errada da face `up`**, não para o eixo (já
  confirmado) nem para o conteúdo (o próprio `up` sem tratamento de polo
  já tinha sido validado como visualmente limpo).
- Geradas as 8 variações possíveis de orientação de um quadrado
  (identidade + rotações de 90/180/270° + 4 reflexões) da face `up` para
  teste direto em jogo, já que não há acesso ao engine PrimeXT nesta
  sessão para iterar renderizando. **`ROTATE_270` confirmado pelo usuário
  como a correta** — já fixado em `FACE_TRANSFORMS["up"]` em
  `goldsrc_export.py`.
- `dn` ainda não foi testado em jogo (raramente visível, coberto por
  terreno na maioria dos mapas) — usa a mesma lógica de eixo que `up`,
  então é uma hipótese razoável que precise de rotação parecida, mas
  **não foi copiado às cegas**: `FACE_TRANSFORMS["dn"]` continua `None`
  até confirmação visual própria.

## Rodando de verdade no Windows: splash, progresso e o bug do `cmft`+MinGW

Pedido do usuário: SkyForge "pronto" significa rodar de verdade no Windows
dele (onde o mod roda), com GUI, splash screen ao abrir, barra de
progresso e interface geral por conta do desenvolvedor (delegado).

Implementado:
- `scripts/gen_splash.py` gera `gui/assets/splash.png` (PIL puro), exibida
  por `main.py` via `QSplashScreen` com duração mínima garantida (~1,2s).
- Barra de progresso indeterminada na GUI durante a geração (o `cmft` roda
  como processo único, sem granularidade fácil de medir — indeterminada é
  honesto, não finge saber "quanto falta").

**Achado importante ao tentar compilar o `cmft` para Windows**: o binário
`cmft.exe` não vem pronto em lugar nenhum — precisa ser compilado. Ao
tentar, o `cmft` tem um bug real de deteção de compilador
(`src/cmft/common/platform.h`): checa `defined(_WIN32) || defined(_WIN64)`
**antes** de `defined(__GNUC__)`, então qualquer GCC/MinGW mirando Windows
(nativo ou cross-compile) é identificado como MSVC — e o código então usa
`__pragma()`, sintaxe exclusiva do MSVC, quebrando a compilação com erro
de sintaxe. Isso teria travado a build tanto cross-compilando do Linux
quanto compilando nativo no Windows com MinGW — não é um problema
específico de ambiente, é um bug real do projeto upstream, nunca reportado
lá.

**Corrigido** via `patches/cmft-fix-mingw-compiler-detection.patch`
(reordena a cadeia `#if/#elif` pra checar `__clang__`/`__GNUC__` antes de
`_WIN32`/`_WIN64`) — não editamos o submódulo diretamente (ficaria com
estado sujo, sem commit real em nenhum remoto); o patch é aplicado como
etapa de build.

**Validação real, não só teórica**: depois do patch, compilei o
`cmft.exe` por cross-compilação (`x86_64-w64-mingw32-g++` no Linux) e
**rodei o binário de Windows de verdade sob Wine** — não só o `--help`,
uma conversão completa de panorama de teste em 6 faces, com sucesso. É a
validação mais próxima de "roda no Windows" que dava pra fazer sem uma
máquina Windows real.

**Automatizado**: `.github/workflows/build-cmft-windows.yml` roda esse
mesmo processo (aplicar patch, cross-compilar, testar sob Wine, publicar
artefato) a cada push relevante — assim o binário de Windows fica sempre
disponível pra baixar em Actions, sem precisar repetir manualmente.
