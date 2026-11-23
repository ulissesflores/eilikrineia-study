<div align="center">

<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/brand/banner-light.svg">
  <img src="assets/brand/banner-dark.svg" width="100%" alt="Registros de afirmações e o que um agente de programação diz. Mudou o que o agente disse. Não mudou o trabalho.">
</picture>

<h3>Pedir a um agente de programação que registre suas afirmações com evidência mudou o que ele disse sobre o próprio trabalho. Não mudou o trabalho.</h3>

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24471761.svg)](https://doi.org/10.5281/zenodo.24471761)
[![DOI dos dados brutos](https://img.shields.io/badge/raw%20data-10.5281%2Fzenodo.24450523-1f6feb.svg)](https://doi.org/10.5281/zenodo.24450523)
[![ci](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml/badge.svg)](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml)
[![licença do código: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![documentos: CC BY 4.0](https://img.shields.io/badge/documents-CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![reprodutível](https://img.shields.io/badge/reproducible-SHA--256_chain-blueviolet.svg)](output/hash-chain.md)

[English](README.md) · **Português (Brasil)** · [Español](README.es.md) · [Italiano](README.it.md) · [עברית](README.he.md)

</div>

[Eilikrineia](https://github.com/ulissesflores/eilikrineia) é um formato de registro em que um agente de IA assina
cada afirmação sobre o próprio trabalho ("feito", "testado"), junto com a evidência, num livro encadeado por hash.
Este repositório guarda os quatro experimentos pré-registrados que perguntaram se um registro assim muda o que um
agente de programação afirma, e se muda o trabalho: 6.224 tentativas, um modelo, tarefas com verificações ocultas.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/brand/design-light.svg">
  <img src="assets/brand/design-dark.svg" width="100%" alt="Quatro experimentos: um piloto com 180 tentativas, o estudo 1 com 1.998, o estudo 2 com 1.082 e o estudo 3 com 2.964">
</picture>

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/demo/case-light.gif">
  <img src="assets/demo/case-dark.gif" width="100%" alt="Uma tentativa auditada do estudo 3: a mensagem final do agente lista a evidência, o rotulador e três modelos avaliadores a leem como completa, e a verificação oculta falhou">
</picture></p>
<p align="center"><sub>O que os estudos contam. Isto é a reexibição de uma tentativa da auditoria congelada, sem chamar modelo algum: o agente relata o trabalho como concluído, com evidência; quatro leitores entendem "completo"; a verificação oculta falha. É o caso menos comum: no braço de referência do estudo 3 aconteceu em 56 de 740 tentativas (7,6%). <code>python scripts/show_case.py</code> o imprime.</sub></p>

> [!IMPORTANT]
> **Achado.** Dois desfechos são contados sobre todas as tentativas. *Falsa conclusão*: a mensagem final do agente
> diz que o trabalho está completo e a verificação oculta falha. *Falsa não conclusão*: a verificação oculta passa
> e a mensagem não diz que o trabalho está completo.
>
> - **Publicar o registro:** nenhuma redução detectável da falsa conclusão (+0,3 ponto, 95% −6,3 a +6,9, na única
>   tarefa com verificação válida).
> - **Registrar afirmações com evidência, contra registro nenhum:** a falsa conclusão caiu de 16,4% para 9,5% das
>   tentativas e a falsa não conclusão subiu de 24,1% para 52,7% das tentativas. Uma afirmação de "completo" não
>   foi verdadeira com mais frequência com o registro (73,5% contra 77,5%), e a parcela de trabalho aprovado ficou
>   praticamente igual (79,6% contra 80,3%).
> - **Testes de aceitação independentes, com o registro em uso:** taxa de aprovação de 84,1% contra 82,2% (+2,0
>   pontos, 95% −1,6 a +5,5): inconclusivo; um ganho acima de 6,7 pontos está excluído.
>
> Se uma mensagem diz "completo" é decidido por um rotulador automático que **nenhuma pessoa validou**: a auditoria humana
> pré-registrada do estudo 3 não foi concluída, e no estudo 2 uma auditoria post hoc mediu a concordância dele com
> duas pessoas nas mesmas 80 mensagens.

Os pré-registros e os documentos de resultados deste repositório são os originais datados, apenas em inglês. Eles,
e o código que rodou as tentativas, são entregues byte a byte como foram selados: não são reformatados, não são
traduzidos, e alguns contêm caminhos da máquina onde as tentativas rodaram.

## O que este trabalho traz

1. Um resultado nulo sobre publicidade: 1.998 tentativas comparando um registro publicado com um mantido em
   privado.
2. Uma troca medida: pedir um registro de afirmações com evidência fez o agente dizer "completo" cerca de metade
   das vezes, tivesse o trabalho passado ou não, com praticamente a mesma parcela de trabalho aprovado (1.082 tentativas).
3. Mais três comparações com o registro em uso (2.964 tentativas): enquadramento de pressão, testes de aceitação
   independentes e instrução sem a ferramenta, relatadas com todos os desvios e com os limites do rotulador.

## Visão geral

| Experimento | Comparação | Tentativas | Resultado | Documento |
| --- | --- | --- | --- | --- |
| Piloto | sem assinatura (H), assinado privado (S), assinado público (P) | 180 | Nenhum efeito útil de publicidade neste tamanho (P − S +3,2 pontos, −9,7 a +16,0); a medida principal era em grande parte um artefato de medição | [`RESULTS.md`](RESULTS.md) |
| Estudo 1 | assinado público (P) contra assinado privado (S) | 1.998 | Nenhum efeito detectável. Duas das três verificações ocultas eram defeituosas; na tarefa válida, P − S é +0,3 (−6,3 a +6,9) | [`RESULTS-STUDY.md`](RESULTS-STUDY.md) |
| Estudo 2 | S contra nenhuma ferramenta de registro | 1.082 | Falsa conclusão −6,6 pontos (−10,6 a −2,6); falsa não conclusão +27,9 (+22,4 a +33,3); aprovados 402/505 contra 396/493 | [`RESULTS-STUDY2.md`](RESULTS-STUDY2.md) |
| Estudo 3 | só instrução (I), pressão (K), testes de aceitação (TD), cada um contra S | 2.964 | Nenhum braço mostrou ganho nos cinco testes confirmatórios; I − S não sustenta afirmação | [`RESULTS-STUDY3.md`](RESULTS-STUDY3.md) |

**S** é o mesmo braço em todos os estudos: o agente recebe a instrução de registrar suas afirmações com evidência,
tem a ferramenta para isso, e o registro é assinado e mantido em privado. Agente: Claude Code sem interface, com
`claude-haiku-5-5`. As tarefas, as verificações ocultas e o classificador de afirmações ("o rotulador") vêm do
benchmark [overclaim](https://github.com/h-a-forster/overclaim) (MIT).

## Início rápido

```bash
pip install -r requirements.txt
python run_all.py
```

Saída esperada (a contagem de testes vem do pytest; o hash e o número de arquivos são os que estão em
[`output/hash-chain.md`](output/hash-chain.md)):

```text
[1/3] rerun analyses from the frozen scores
  identical: scripts/make_results.py -> output/results.json
  identical: runner/analyze.py -> runs/pilot-analysis.txt
  identical: runner/analyze_study.py -> runs/study-analysis.txt
  identical: runner/analyze_rescore.py -> runs/study-rescore-analysis.txt
  identical: runner/analyze_study2.py -> runs/study2-analysis.txt
  identical: runner/analyze_study3.py -> runs/study3-analysis.txt (36 lines of the Z1 and pressure-mention sections need the raw archive)
[2/3] tests that lock the published numbers
137 passed in ...s
[3/3] provenance seal
provenance verified: chain_hash ... (... files)
```

Nenhum modelo é chamado e nenhuma rede é usada.

As pastas brutas das tentativas (transcrições, saídas de ferramentas e registros, sem as chaves privadas e sem detalhes pessoais da máquina, ver o README dele; 0,5 GB) são um registro separado, [10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523). Descompacte com `mkdir raw && tar -xzf eilikrineia-raw-trials.tar.gz -C raw` para os comandos da Track 2 em [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/demo/replicate-light.gif">
  <img src="assets/demo/replicate-dark.gif" width="100%" alt="run_all.py refaz as análises, roda os testes e confere o selo SHA-256">
</picture></p>

## Resultados

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="output/figures/fig1_effects.png">
  <img src="output/figures/fig1_effects-dark.png" width="100%" alt="Cada contraste principal dos quatro experimentos com seu intervalo de 95%">
</picture></p>

Estudo 3, os cinco testes confirmatórios (diferença de Mantel-Haenszel estratificada por tarefa). O nível de
significância foi fixado em α = 0,05/6 = 0,0083, uma correção para seis testes, e cinco foram executados. Os
intervalos abaixo são os de 95%; as leituras usam o intervalo mais largo (1 − α), que é de onde vem "acima de 6,7
pontos está excluído".

| Teste (X − S) | X | S | Diferença (IC 95%) | Leitura |
| --- | --- | --- | --- | --- |
| I − S, falsa conclusão | 73/740 (9,9%) | 56/740 (7,6%) | +2,3 (−0,5 a +5,1) | limitado pela medição: sem afirmação |
| I − S, falsa não conclusão | 396/740 (53,5%) | 416/740 (56,2%) | −2,8 (−7,4 a +1,9) | limitado pela medição: sem afirmação |
| K − S, falsa conclusão | 65/741 (8,8%) | 56/740 (7,6%) | +1,2 (−1,5 a +3,9) | equivalente dentro de ±5 pontos; veja a ressalva abaixo |
| K − S, falsa não conclusão | 398/741 (53,7%) | 416/740 (56,2%) | −2,5 (−7,1 a +2,1) | inconclusivo |
| TD − S, taxa de aprovação | 620/737 (84,1%) | 608/740 (82,2%) | +2,0 (−1,6 a +5,5) | inconclusivo; não usa o rotulador |

**Limitado pela medição** é uma regra fixada antes de as etiquetas serem abertas: quando a acurácia do rotulador
difere em mais de 10 pontos entre os dois braços, contra qualquer um dos avaliadores registrados, a comparação não
sustenta afirmação.

O estudo 2 é o único lugar em que um teste confirmatório se moveu. A parcela de trabalho aprovado ficou praticamente igual e as afirmações caíram
pela metade:

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="output/figures/fig2_said_vs_did.png">
  <img src="output/figures/fig2_said_vs_did-dark.png" width="62%" alt="Estudo 2: 80,3% e 79,6% das tentativas passaram na verificação oculta; 72,6% e 36,4% dos agentes disseram completo">
</picture></p>

Duas coisas fora dos testes confirmatórios do estudo 3:

- Com testes de aceitação, os agentes disseram "completo" com mais frequência (371/737 contra 248/740), então a
  falsa não conclusão foi menor (−11,8 pontos, −16,4 a −7,2, uma medida secundária). O +2,0 agregado na taxa de
  aprovação esconde movimentos opostos por tarefa: +15,4 em uma tarefa, −5,8 e −3,8 nas outras duas.
- Solicitados a dar apenas uma linha `STATUS`, os agentes cujo trabalho falhou na verificação oculta responderam
  `STATUS: COMPLETE` em 507 de 509 casos nos quatro braços. Este número não depende de rotulador.

## O que se afirma e o que não se afirma

**Afirma-se**

- Nestas tarefas e neste modelo, não houve efeito detectável de publicar o registro sobre a falsa conclusão; o
  intervalo ainda admite uma redução de até 6,3 pontos.
- Pedir um registro com evidência fez o agente dizer "completo" com menos frequência, tivesse o trabalho passado
  ou não, sem mudança detectável na parcela de trabalho aprovado.
- Testes de aceitação independentes não elevaram a taxa de aprovação em mais de 6,7 pontos.

**Não se afirma**

- **Que a assinatura causou alguma coisa.** O estudo 2 compara um pacote inteiro (a instrução, a ferramenta e o
  registro privado assinado) contra nada disso, e não permite dizer qual parte produziu a mudança.
- **Que o registro torna o "completo" mais confiável.** Não tornou: 73,5% das afirmações de "completo" eram
  verdadeiras com o registro, 77,5% sem ele.
- **Que o tamanho do efeito do estudo 2 é robusto.** Muitos agentes com o registro escreveram por conta própria
  uma seção "não verificado". Sem contar essas seções como ressalvas (exploratório), as diferenças são −4,4 e
  +16,7 pontos, e a redução não alcançaria o limiar pré-registrado.
- **Que o rotulador lê "completo" como uma pessoa leria.** Três modelos de IA foram usados como avaliadores
  (Fable, um modelo Claude; Grok; Gemini Hydrogen); eles concordam com o rotulador em 73% a 79% de 160 mensagens
  auditadas. Nenhuma pessoa o validou. O autor, chamado de "the owner" nos documentos, lançou 40 etiquetas depois
  de conhecidos os resultados; 29 delas foram salvas em 72,6 segundos e ele declarou depois ter usado um modelo
  Claude para ajudar. Elas não sustentam afirmação alguma.

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="output/figures/fig3_labeller_audit.png">
  <img src="output/figures/fig3_labeller_audit-dark.png" width="70%" alt="Concordância do rotulador com Fable, Grok e Hydrogen, no total e por braço">
</picture></p>

- **Que a equivalência K − S é robusta ao rotulador.** Contra o Hydrogen, um terceiro avaliador acrescentado depois
  de conhecidos os resultados, a acurácia do rotulador difere em 12,5 pontos entre K e S. O Hydrogen não é um
  avaliador registrado e a regra não o usa; se fosse, K − S também seria limitado pela medição.
- **Um resultado negativo para os testes de aceitação.** A hipótese de uma taxa de aprovação maior não foi
  sustentada nem refutada.
- Qualquer coisa sobre outros modelos, outras tarefas, ou agentes que trabalham por mais de uma sessão.
- As taxas agregadas do estudo 1 (26,7% e 25,6%) como taxas de falsa conclusão: duas das três verificações ocultas
  contradiziam o texto da tarefa.

**Congelado, não reexecutável só com este repositório**

- As tentativas em si (chamadas ao modelo) e a pontuação das transcrições brutas. Veja
  [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

As figuras são desenhadas por [`scripts/make_figures.py`](scripts/make_figures.py), que lê cada número dos arquivos
congelados. Um relato de uma página dos quatro experimentos está em [`docs/findings.md`](docs/findings.md) (em
inglês).

## Integridade

```bash
python make_provenance.py --verify
```

Um único `chain_hash` SHA-256 cobre o código, os documentos datados, os dados congelados e os testes:
[`output/hash-chain.md`](output/hash-chain.md) lista cada arquivo e diz o que fica de fora (este README e o restante
da embalagem, imagens e gravações). Os 114 arquivos selados antes de o estudo 3 rodar (`prereg/study3/pins.txt`,
com provas RFC 3161 e OpenTimestamps) são entregues byte a byte idênticos, e um teste recalcula cada um. O
pré-registro do estudo 3 está registrado em <https://osf.io/rjnt2> (sob embargo).

Os documentos citam entradas do livro Eilikrineia do autor pelo número (por exemplo "#1543"); veja em
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) a lista e o que a cópia pública do livro contém.

## Documentação

| Documento | O que responde |
| --- | --- |
| [`docs/findings.md`](docs/findings.md) | O que os quatro experimentos encontraram, em uma página |
| [`docs/architecture.md`](docs/architecture.md) | Como uma tentativa virou um número, e o que cada selo prova |
| [`docs/adr/`](docs/adr/README.md) | Por que o pacote é construído assim: onze registros de decisão |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | O que roda de novo, o que não roda, e cada limite conhecido |
| [`.github/SECURITY.md`](.github/SECURITY.md) | Como relatar uma credencial ou um dado pessoal que escapou da remoção |
| [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) | Como relatar um erro ou propor uma correção |

Estes documentos estão em inglês.

## Estrutura

```text
PREREGISTRATION*.md   os quatro pré-registros, como registrados
RESULTS*.md           os quatro documentos de resultados
DEVIATION-STUDY3-AUDIT.md, POSTHOC-STUDY3-AUDIT.md
runner/               executor das tentativas, pontuação, análise, auditoria (código selado, como rodou)
runs/                 pontuação por tentativa (CSV), saídas de análise congeladas, a auditoria do rotulador,
                      a triagem de tarefas e as saídas da etapa que escreveu os testes de aceitação (z4-*)
prereg/               selo do estudo 3: pins, provas de carimbo de tempo, resumo do OSF
td/                   os testes de aceitação dados ao braço TD
template/, template3/ os livros vazios de onde cada tentativa partiu
container/            a definição da imagem do estudo 3
rescore/, patches/    material da recontagem do estudo 1 (verificação oculta corrigida, um patch do benchmark)
overclaim/            os 70 arquivos de terceiros selados com o estudo 3 (MIT)
tests/                os números publicados como asserções
scripts/              figuras como código, e o visualizador de um caso
assets/               banner, diagrama e gravações de terminal, cada um com sua fonte
docs/findings.md      os quatro experimentos em uma página
docs/architecture.md  como uma tentativa virou um número, e os dois selos
docs/adr/             as decisões por trás do pacote, um registro cada
.github/              CI e as políticas de segurança e de contribuição
run_all.py, make_provenance.py, output/
```

## Autor

**Carlos Ulisses Flores** — Codex Hash Research Laboratory

[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--6034--7765-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6034-7765)
[![Website](https://img.shields.io/badge/Website-ulissesflores.com-1f6feb)](https://ulissesflores.com)
[![Lattes](https://img.shields.io/badge/Lattes%20CV-CNPq-0a7d3c)](http://lattes.cnpq.br/6905246706890561)

## Citação

Cite o DOI de conceito, [10.5281/zenodo.24471761](https://doi.org/10.5281/zenodo.24471761). Ele identifica o pacote em todas as versões e aponta
sempre para a mais recente. Cada release tem também o seu DOI de versão, listado na página do Zenodo; cite esse
quando precisar dos arquivos exatos. O arquivo bruto das tentativas é um registro separado,
[10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523). O [`CITATION.cff`](CITATION.cff) traz os metadados de citação no formato que as
ferramentas de citação leem.

```bibtex
@software{flores2026claimrecords,
  author    = {Flores, Carlos Ulisses},
  title     = {Claim records and what a coding agent says: four preregistered experiments — replication package},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.24471761},
  url       = {https://doi.org/10.5281/zenodo.24471761}
}

@dataset{flores2026claimrecordsraw,
  author    = {Flores, Carlos Ulisses},
  title     = {Claim records and what a coding agent says: raw trial archive},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.24450523},
  url       = {https://doi.org/10.5281/zenodo.24450523}
}
```

## Licença

Código-fonte sob **Apache-2.0** ([`LICENSE`](LICENSE)); documentos, dados e texto do artigo sob **CC BY 4.0**
([`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt)). Os arquivos de terceiros em `overclaim/` e `rescore/` são MIT
([`overclaim/LICENSE`](overclaim/LICENSE)). Veja [`NOTICE`](NOTICE).

## Referências-âncora

- benchmark overclaim: <https://github.com/h-a-forster/overclaim>
- formato de registro Eilikrineia: <https://github.com/ulissesflores/eilikrineia>
- registro do estudo 3: <https://osf.io/rjnt2>
