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
  especificamente mostra descontinuidade, isso aponta para
  **rotação/orientação errada da face `up`** (`FACE_TRANSFORMS["up"]`
  ainda está `None`) — não para o eixo (posy→up já está confirmado desde
  a medição programática) nem para o conteúdo em si (o próprio `up` sem
  tratamento de polo já tinha sido validado como visualmente limpo).
- Como não há acesso ao engine PrimeXT nesta sessão para iterar
  renderizando, foram geradas as 8 variações possíveis de orientação de
  um quadrado (identidade + rotações de 90/180/270° + 4 reflexões) da
  face `up`, para o usuário testar por troca direta de arquivo em
  `gfx/env/` até achar a que fecha sem costura. Assim que confirmado,
  atualizar `FACE_TRANSFORMS["up"]` em `goldsrc_export.py` com o
  `PIL.Image.Transpose` correspondente e apagar esse item da lista de
  pendências.
- `dn` não foi testado em jogo ainda (raramente visível, prioridade
  menor) — mas como usa a mesma lógica de eixo que `up`, é provável que
  precise da mesma correção de rotação assim que `up` for resolvido.
