# Créditos e software de terceiros

O SkyForge existe em cima do trabalho de outras pessoas. Este arquivo lista
cada dependência de terceiro usada no projeto, sua licença e um link para o
projeto original — é importante que esse crédito fique visível e não se
perca com o tempo.

## Autores da versão inicial (v0.1.0)

**Hidrocarboneto** e **Claude** (Anthropic) — desenvolvimento do SkyForge.
Ver [`LICENSE`](LICENSE) (MIT): uso e adaptação livres, sem
responsabilidade dos autores, exigindo apenas manter este crédito.

## Motor de conversão

### cmft

- **Autor**: Dario Manesku
- **Repositório**: <https://github.com/dariomanesku/cmft>
- **Licença**: BSD 2-Clause
- **Uso no SkyForge**: motor de reprojeção equirectangular → cubemap
  (`external/cmft`, submódulo git, chamado como processo externo por
  `src/skyforge/cmft_wrapper.py`). O SkyForge não reimplementa nenhuma
  matemática de projeção própria — toda a conversão geométrica é feita
  pelo `cmft`.

## Inspiração de projeto (sem reuso de código)

### SkyPaint

- Ferramenta clássica da comunidade GoldSrc/Half-Life para conversão de
  panoramas em skybox de 6 faces. O SkyForge é descrito como seu "sucessor
  espiritual" — a motivação e o fluxo de trabalho (importar um panorama,
  gerar as 6 faces já nomeadas) vêm dela, mas nenhum código do SkyPaint foi
  copiado ou consultado (o binário original não está disponível para
  inspeção neste projeto).

## Bibliotecas Python

| Biblioteca | Autor / mantenedores | Licença | Uso |
|---|---|---|---|
| [PySide6](https://pypi.org/project/PySide6/) | The Qt Company | LGPLv3 | Interface gráfica |
| [NumPy](https://numpy.org/) | NumPy Developers | BSD 3-Clause | Processamento de imagem (arrays de pixel) |
| [Pillow](https://python-pillow.org/) | Jeffrey A. Clark e colaboradores (fork de PIL, de Fredrik Lundh) | HPND | Leitura/escrita de TGA, manipulação de imagem |

## Como manter este arquivo atualizado

Sempre que uma nova dependência de terceiro (biblioteca, binário externo,
trecho de código de outro projeto) for adicionada ao SkyForge, ela deve
ganhar uma entrada aqui **antes** do merge — nome do projeto, autor,
licença e para que serve no SkyForge. O README linka pra este arquivo; não
duplicar a lista lá, só resumir.
