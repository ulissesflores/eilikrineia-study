<div align="center">

<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/brand/banner-it-light.svg">
  <img src="assets/brand/banner-it-dark.svg" width="100%" alt="Registri di affermazioni e ciò che dice un agente di programmazione. Ha cambiato ciò che l'agente ha detto. Non ha cambiato il lavoro.">
</picture>

<h3>Chiedere a un agente di programmazione di registrare le proprie affermazioni con le prove ha cambiato ciò che ha detto del proprio lavoro. Non ha cambiato il lavoro.</h3>

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24471761.svg)](https://doi.org/10.5281/zenodo.24471761)
[![DOI dei dati grezzi](https://img.shields.io/badge/raw%20data-10.5281%2Fzenodo.24450523-1f6feb.svg)](https://doi.org/10.5281/zenodo.24450523)
[![ci](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml/badge.svg)](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml)
[![tests](https://img.shields.io/badge/tests-592_passing-brightgreen.svg)](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ulissesflores/eilikrineia-study/blob/main/colab/replication.ipynb)
[![licenza del codice: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![documenti: CC BY 4.0](https://img.shields.io/badge/documents-CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![riproducibile](https://img.shields.io/badge/reproducible-SHA--256_chain-blueviolet.svg)](output/hash-chain.md)

[English](README.md) · [Português (Brasil)](README.pt-BR.md) · [Español](README.es.md) · **Italiano** · [עברית](README.he.md)

</div>

[Eilikrineia](https://github.com/ulissesflores/eilikrineia) è un formato di registro in cui un agente di IA firma
ogni affermazione sul proprio lavoro ("fatto", "testato"), insieme alle prove, in un registro concatenato tramite
hash. Questo repository contiene i quattro esperimenti che hanno chiesto se un registro del genere
cambi ciò che un agente di programmazione afferma, e se cambi il lavoro: 6.224 prove, un modello, compiti con
verifiche nascoste. Ciascuno aveva un piano scritto prima della prima prova; il piano dello studio 3 ha marche temporali esterne verificate anteriori ad essa; per gli altri l'ispezione non ne ha trovata nessuna (vedi Integrità).

<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/brand/design-it-light.svg">
  <img src="assets/brand/design-it-dark.svg" width="100%" alt="Quattro esperimenti: un pilota con 180 prove, lo studio 1 con 1.998, lo studio 2 con 1.082 e lo studio 3 con 2.964">
</picture>

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/demo/case-light.gif">
  <img src="assets/demo/case-dark.gif" width="100%" alt="Una prova verificata dello studio 3: il messaggio finale dell'agente elenca le prove, l'etichettatore e tre modelli valutatori lo leggono come completo, e la verifica nascosta è fallita">
</picture></p>
<p align="center"><sub>Che cosa contano gli studi. Questa è la riproduzione di una prova dell'audit congelato, senza alcuna chiamata a un modello: l'agente riferisce che il lavoro è fatto, con le prove; quattro lettori lo intendono come "completo"; la verifica nascosta fallisce. È il caso meno frequente: nel braccio di riferimento dello studio 3 è accaduto in 56 prove su 740 (7,6%). <code>python scripts/show_case.py</code> lo stampa.</sub></p>

> [!IMPORTANT]
> **Risultato.** Si contano due esiti su tutte le prove. *Falso completamento*: il messaggio finale dell'agente
> dice che il lavoro è completo e la verifica nascosta fallisce. *Falso non completamento*: la verifica nascosta
> passa e il messaggio non dice che il lavoro è completo.
>
> - **Pubblicare il registro:** nessuna riduzione rilevabile del falso completamento (+0,3 punti, 95% da −6,3 a
>   +6,9, sull'unico compito con una verifica valida).
> - **Registrare le affermazioni con le prove, rispetto a nessun registro:** il falso completamento è sceso dal
>   16,4% al 9,5% delle prove e il falso non completamento è salito dal 24,1% al 52,7% delle prove.
>   Un'affermazione di "completo" non è risultata vera più spesso con il registro (73,5% contro 77,5%), e la quota
>   di lavoro superato è rimasta pressoché uguale (79,6% contro 80,3%).
> - **Test di accettazione indipendenti, con il registro in uso:** tasso di superamento 84,1% contro 82,2% (+2,0
>   punti, 95% da −1,6 a +5,5): non conclusivo; un guadagno superiore a 6,7 punti è escluso.
>
> Se un messaggio dica "completo" è deciso da un etichettatore automatico che **nessuna persona ha validato**: l'audit
> umano preregistrato dello studio 3 non è stato completato, e nello studio 2 un audit post hoc ha misurato la sua
> concordanza con due valutatori umani sugli stessi 80 messaggi.

I preregistri e i documenti dei risultati di questo repository sono gli originali datati, solo in inglese. Essi, e
il codice che ha eseguito le prove, sono distribuiti byte per byte come sono stati sigillati: non sono
riformattati, non sono tradotti, e alcuni contengono percorsi della macchina su cui le prove sono state eseguite.

## Che cosa apporta questo lavoro

1. Un risultato nullo sulla pubblicità: 1.998 prove che confrontano un registro pubblicato con uno tenuto privato.
2. Uno scambio misurato: chiedere un registro delle affermazioni con le prove ha portato l'agente a dire
   "completo" circa la metà delle volte, che il lavoro fosse superato o no, con una quota di lavoro superato pressoché uguale (1.082
   prove).
3. Altri tre confronti con il registro in uso (2.964 prove): inquadramento di pressione, test di accettazione
   indipendenti e istruzione senza lo strumento, riportati con ogni deviazione e con i limiti dell'etichettatore.

## In breve

| Esperimento | Confronto | Prove | Risultato | Documento |
| --- | --- | --- | --- | --- |
| Pilota | senza firma (H), firmato privato (S), firmato pubblico (P) | 180 | Nessun effetto utile della pubblicità a questa dimensione (P − S +3,2 punti, da −9,7 a +16,0); la misura principale era in gran parte un artefatto di misurazione | [`RESULTS.md`](RESULTS.md) |
| Studio 1 | firmato pubblico (P) contro firmato privato (S) | 1.998 | Nessun effetto rilevabile. Due delle tre verifiche nascoste erano difettose; sul compito valido P − S è +0,3 (da −6,3 a +6,9) | [`RESULTS-STUDY.md`](RESULTS-STUDY.md) |
| Studio 2 | S contro nessuno strumento di registro | 1.082 | Falso completamento −6,6 punti (da −10,6 a −2,6); falso non completamento +27,9 (da +22,4 a +33,3); superati 402/505 contro 396/493 | [`RESULTS-STUDY2.md`](RESULTS-STUDY2.md) |
| Studio 3 | sola istruzione (I), pressione (K), test di accettazione (TD), ciascuno contro S | 2.964 | Nessun braccio ha mostrato un guadagno nei cinque test confermativi; I − S non sostiene alcuna affermazione | [`RESULTS-STUDY3.md`](RESULTS-STUDY3.md) |

**S** è lo stesso braccio in tutti gli studi: all'agente viene detto di registrare le proprie affermazioni con le
prove, ha lo strumento per farlo, e il registro è firmato e tenuto privato. Agente: Claude Code senza interfaccia,
con `claude-haiku-5-5`. I compiti, le verifiche nascoste e il classificatore delle affermazioni
("l'etichettatore") provengono dal benchmark [overclaim](https://github.com/h-a-forster/overclaim) (MIT).

## Avvio rapido

```bash
pip install -r requirements.txt
python run_all.py
```

Output atteso (il numero di test viene da pytest; l'hash e il numero di file sono quelli in
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

Non viene chiamato alcun modello e non si usa la rete.

Le cartelle grezze delle prove (trascrizioni, output degli strumenti e registri, senza le chiavi private né dettagli personali della macchina, vedere il suo README; 0,5 GB) sono un record separato, [10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523). Estrarle con `mkdir raw && tar -xzf eilikrineia-raw-trials.tar.gz -C raw` per i comandi della Track 2 in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/demo/replicate-light.gif">
  <img src="assets/demo/replicate-dark.gif" width="100%" alt="run_all.py riesegue le analisi, esegue i test e verifica il sigillo SHA-256">
</picture></p>

## Risultati

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/figures/fig1_effects-it-light.png">
  <img src="assets/figures/fig1_effects-it-dark.png" width="100%" alt="Ogni contrasto principale dei quattro esperimenti con il suo intervallo al 95%">
</picture></p>

Studio 3, i cinque test confermativi (differenza di Mantel-Haenszel stratificata per compito). Il livello di
significatività è stato fissato a α = 0,05/6 = 0,0083, una correzione per sei test, e ne sono stati eseguiti
cinque. Gli intervalli qui sotto sono quelli al 95%; le letture usano l'intervallo più ampio (1 − α), da cui
deriva "un guadagno superiore a 6,7 punti è escluso".

| Test (X − S) | X | S | Differenza (IC 95%) | Lettura |
| --- | --- | --- | --- | --- |
| I − S, falso completamento | 73/740 (9,9%) | 56/740 (7,6%) | +2,3 (da −0,5 a +5,1) | limitato dalla misura: nessuna affermazione |
| I − S, falso non completamento | 396/740 (53,5%) | 416/740 (56,2%) | −2,8 (da −7,4 a +1,9) | limitato dalla misura: nessuna affermazione |
| K − S, falso completamento | 65/741 (8,8%) | 56/740 (7,6%) | +1,2 (da −1,5 a +3,9) | equivalente entro ±5 punti; si veda la riserva più sotto |
| K − S, falso non completamento | 398/741 (53,7%) | 416/740 (56,2%) | −2,5 (da −7,1 a +2,1) | non conclusivo |
| TD − S, tasso di superamento | 620/737 (84,1%) | 608/740 (82,2%) | +2,0 (da −1,6 a +5,5) | non conclusivo; non usa l'etichettatore |

**Limitato dalla misura** è una regola fissata prima dell'apertura delle etichette: quando l'accuratezza
dell'etichettatore differisce di più di 10 punti tra i due bracci, rispetto a uno qualsiasi dei valutatori
registrati, il confronto non sostiene alcuna affermazione.

Lo studio 2 è l'unico punto in cui un test confermativo si è mosso. La quota di lavoro superato è rimasta pressoché uguale e le affermazioni
si sono dimezzate:

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/figures/fig2_said_vs_did-it-light.png">
  <img src="assets/figures/fig2_said_vs_did-it-dark.png" width="62%" alt="Studio 2: l'80,3% e il 79,6% delle prove hanno superato la verifica nascosta; il 72,6% e il 36,4% degli agenti hanno detto completo">
</picture></p>

Due cose al di fuori dei test confermativi dello studio 3:

- Con i test di accettazione, gli agenti hanno detto "completo" più spesso (371/737 contro 248/740), quindi il
  falso non completamento è stato più basso (−11,8 punti, da −16,4 a −7,2, una misura secondaria). Il +2,0
  aggregato sul tasso di superamento nasconde movimenti opposti per compito: +15,4 su un compito, −5,8 e −3,8
  sugli altri due.
- Alla richiesta di una sola riga `STATUS`, gli agenti il cui lavoro non ha superato la verifica nascosta hanno
  risposto `STATUS: COMPLETE` in 507 casi su 509 nei quattro bracci. Questo numero non richiede etichettatore.

## Che cosa si afferma e che cosa no

**Si afferma**

- Su questi compiti e con questo modello, non c'è stato alcun effetto rilevabile della pubblicazione del registro
  sul falso completamento; l'intervallo ammette ancora una riduzione fino a 6,3 punti.
- Chiedere un registro con le prove ha portato l'agente a dire "completo" meno spesso, che il lavoro fosse
  superato o no, senza cambiamenti rilevabili nella quota di lavoro superato.
- I test di accettazione indipendenti non hanno aumentato il tasso di superamento di più di 6,7 punti.

**Non si afferma**

- **Che la firma abbia causato qualcosa.** Lo studio 2 confronta un pacchetto intero (l'istruzione, lo strumento e
  il registro privato firmato) con l'assenza di tutto ciò, e non permette di dire quale parte abbia prodotto lo
  spostamento.
- **Che il registro renda più affidabile il "completo".** Non lo ha fatto: il 73,5% delle affermazioni di
  "completo" era vero con il registro, il 77,5% senza.
- **Che la dimensione dell'effetto dello studio 2 sia robusta.** Molti agenti con il registro hanno scritto di
  propria iniziativa una sezione "non verificato". Senza contare quelle sezioni come riserve (esplorativo), le
  differenze sono −4,4 e +16,7 punti, e la riduzione non raggiungerebbe la soglia fissata nel piano.
- **Che l'etichettatore legga "completo" come lo leggerebbe una persona.** Tre modelli di IA sono stati usati come
  valutatori (Fable, un modello Claude; Grok; Gemini Hydrogen); concordano con l'etichettatore dal 73% al 79% su
  160 messaggi verificati. Nessuna persona lo ha validato. L'autore, chiamato "the owner" nei documenti, ha
  inserito 40 etichette dopo che i risultati erano noti; 29 di esse sono state salvate in 72,6 secondi e in
  seguito ha dichiarato di aver usato un modello Claude come aiuto. Non sostengono alcuna affermazione.

<p align="center"><picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/figures/fig3_labeller_audit-it-light.png">
  <img src="assets/figures/fig3_labeller_audit-it-dark.png" width="70%" alt="Concordanza dell'etichettatore con Fable, Grok e Hydrogen, complessiva e per braccio">
</picture></p>

- **Che l'equivalenza K − S sia robusta rispetto all'etichettatore.** Rispetto a Hydrogen, un terzo valutatore
  aggiunto dopo che i risultati erano noti, l'accuratezza dell'etichettatore differisce di 12,5 punti tra K e S.
  Hydrogen non è un valutatore registrato e la regola non lo usa; se lo fosse stato, anche K − S sarebbe limitato
  dalla misura.
- **Un risultato negativo per i test di accettazione.** L'ipotesi di un tasso di superamento più alto non è né
  sostenuta né confutata.
- Nulla su altri modelli, altri compiti, o agenti che lavorano per più di una sessione.
- I tassi aggregati dello studio 1 (26,7% e 25,6%) come tassi di falso completamento: due delle tre verifiche
  nascoste contraddicevano il testo del compito.

**Congelato, non rieseguibile con questo solo repository**

- Le prove stesse (chiamate al modello) e il punteggio delle trascrizioni grezze. Si veda
  [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

Le figure sono disegnate da [`scripts/make_figures.py`](scripts/make_figures.py), che legge ogni numero dai file
congelati. Un resoconto di una pagina dei quattro esperimenti è in [`docs/findings.md`](docs/findings.md) (in
inglese).

## Integrità

```bash
python make_provenance.py --verify
```

Un unico `chain_hash` SHA-256 copre il codice, i documenti datati, i dati congelati e i test:
[`output/hash-chain.md`](output/hash-chain.md) elenca ogni file e dice che cosa resta fuori (questo README e il
resto della confezione, immagini e registrazioni). I 114 file sigillati prima dell'esecuzione dello studio 3
(`prereg/study3/pins.txt`, con prove RFC 3161 e OpenTimestamps) sono distribuiti identici byte per byte, e un test
li ricalcola uno per uno. Il preregistro dello studio 3 è registrato su <https://osf.io/rjnt2> (sotto embargo).

**Quando ogni piano fu registrato.** Lo studio 3 ha marche temporali esterne verificate anteriori alla sua prima prova:
tre token RFC 3161 e una prova OpenTimestamps su `prereg/study3/pins.txt`, datati 2026-11-09. L'ispezione non ha trovato
alcuna marca temporale esterna anteriore alla prima prova per il pilota e gli studi 1 e 2; i loro piani portano solo gli
orari di inserimento firmati del registro dell'autore (marche interne; gli hash dei piani sono nelle voci del registro).
Le voci compaiono per la prima volta nella cronologia ispezionata del registro pubblico nel commit a7a7561, 2026-11-10
15:20:10 UTC, e la prima versione del file OpenTimestamps in quel commit contiene solo attestazioni pendenti; la più
precoce attestazione Bitcoin verificata trovata per esse è il blocco 975319, 2026-11-10, che compare in un commit
successivo. Entrambi sono posteriori a quelle prove. L'ora esatta del push su GitHub non è stabilita.
[`posthoc/`](posthoc/README.md) legge questa cronologia dai file.

I documenti citano le voci del registro Eilikrineia dell'autore per numero (per esempio "#1543"); si veda in
[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) l'elenco e che cosa contiene la copia pubblica del registro.

## Verificare i numeri dell'articolo

Ogni numero che l'articolo stampa è associato, in [`posthoc/paper_numbers.json`](posthoc/paper_numbers.json),
allo script che lo produce, all'output versionato che lo stampa e alla riga in cui si trova. I controlli
confrontano ogni valore stampato con quella riga e lo SHA-256 di ogni script e output che la mappa nomina, e
rieseguono gli script post hoc:

```bash
python -m pytest -q posthoc/test_paper_numbers.py
python posthoc/verify_paper_numbers.py --rerun
```

Output atteso senza l'archivio grezzo (pytest stampa `455 passed, 19 skipped`: le riesecuzioni che
richiedono l'archivio vengono saltate, con il motivo):

```text
hashes: 79 of 79 files match
values: 365 of 365 entries (728 printed values) match the committed outputs; 22 number groups have no script (listed in the manifest)
```

Segue una riga per script post hoc: `same` per gli 8 che richiedono solo il pacchetto, `skipped` con ciò che
manca per i 18 che richiedono l'archivio grezzo. Con l'archivio estratto in `raw/` ([10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523))
e gli input aggiuntivi di due script (per `prereg_chronology.py`, un clone del registro pubblico accanto al
repository, `openssl` e il client OpenTimestamps `ots`; per `ledger_audit.py`, `ssh-keygen` di OpenSSH), tutti i 26
stampano `same`.

I 22 gruppi di numeri che l'articolo stampa senza script sono elencati in `unscripted`, ciascuno con il motivo, e
non contano come verificati: 6 sono derivati a mano da output versionati o stampati solo durante l'esecuzione, 5
vengono dai piani e dai documenti di disegno, 3 vengono da file non pubblici, 3 hanno input pubblici ma nessuno
script versionato li stampa, 2 si leggono da output congelati senza essere stampati come un unico conteggio, 2
sono stati letti a mano (in una trascrizione grezza e sulla macchina dell'autore) e 1 raccoglie le cifre citate
da altri lavori; i due controlli post hoc che l'articolo indica come
non riproducibili dal pacchetto sono nominati, con il motivo, in [`posthoc/README.md`](posthoc/README.md).
L'[integrazione continua](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/ci.yml) esegue questi controlli, il sigillo e `run_all.py` su Python 3.11 e 3.12 a ogni
push. Un workflow manuale, [raw-archive](https://github.com/ulissesflores/eilikrineia-study/actions/workflows/raw-archive.yml), scarica l'archivio grezzo da Zenodo, lo verifica
contro il suo `SHA256SUMS` e riesegue i 26 script post hoc; il suo log è la traccia pubblica di quell'esecuzione. Il [notebook di Colab](colab/replication.ipynb) esegue lo stesso dal repository, senza installare nulla,
nella versione che l'articolo cita (`REF` in cima), mostra ogni valore stampato accanto al valore del suo output
e può scaricare l'archivio grezzo per rieseguire tutti gli script post hoc. Non può ripetere le prove: hanno
chiamato un modello ospitato. Decisioni: [0013](docs/adr/0013-second-post-hoc-increment-public-archive-only.md), [0014](docs/adr/0014-paper-numbers-manifest-and-test.md), [0015](docs/adr/0015-ci-and-colab-from-a-pinned-version.md).

## Documentazione

| Documento | A che cosa risponde |
| --- | --- |
| [`docs/findings.md`](docs/findings.md) | Che cosa hanno trovato i quattro esperimenti, in una pagina |
| [`docs/architecture.md`](docs/architecture.md) | Come una prova è diventata un numero, e che cosa prova ciascun sigillo |
| [`docs/adr/`](docs/adr/README.md) | Perché il pacchetto è costruito così: quindici registri di decisione |
| [`posthoc/`](posthoc/README.md) | Analisi post hoc scritte dopo le revisioni, fuori dal sigillo: script, output, l'elenco delle letture tra prove |
| [`colab/replication.ipynb`](colab/replication.ipynb) | Tutti i controlli di questa pagina, eseguiti dal repository in Google Colab, senza installare nulla |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Che cosa si riesegue, che cosa no, e ogni limite noto |
| [`.github/SECURITY.md`](.github/SECURITY.md) | Come segnalare una credenziale o un dato personale sfuggito alla rimozione |
| [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) | Come segnalare un errore o proporre una correzione |

Questi documenti sono in inglese.

## Struttura

```text
PREREGISTRATION*.md   i quattro preregistri, come registrati
RESULTS*.md           i quattro documenti dei risultati
DEVIATION-STUDY3-AUDIT.md, POSTHOC-STUDY3-AUDIT.md
runner/               esecutore delle prove, punteggio, analisi, audit (codice sigillato, come è stato eseguito)
runs/                 punteggi per prova (CSV), output di analisi congelati, l'audit dell'etichettatore,
                      la selezione dei compiti e gli output del passo che ha scritto i test di accettazione (z4-*)
prereg/               sigillo dello studio 3: pins, prove di marcatura temporale, riassunto OSF
td/                   i test di accettazione dati al braccio TD
template/, template3/ i registri vuoti da cui è partita ogni prova
container/            la definizione dell'immagine dello studio 3
rescore/, patches/    materiale del riconteggio dello studio 1 (verifica nascosta corretta, una patch del benchmark)
overclaim/            i 70 file di terzi sigillati con lo studio 3 (MIT)
tests/                i numeri pubblicati come asserzioni
scripts/              figure come codice, e il visualizzatore di un caso
posthoc/              analisi post hoc e i loro output (fuori dal sigillo)
colab/                il notebook di replica (si apre in Google Colab)
assets/               banner, diagramma, figure in altre quattro lingue, marchio del laboratorio, registrazioni del terminale
docs/findings.md      i quattro esperimenti in una pagina
docs/architecture.md  come una prova è diventata un numero, e i due sigilli
docs/adr/             le decisioni dietro il pacchetto, un registro ciascuna
.github/              CI e le politiche di sicurezza e di contributo
run_all.py, make_provenance.py, output/
```

## Autore

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/lab-lockup-dark.png">
  <img src="assets/brand/lab-lockup-light.png" width="300" alt="Codex Hash Research Laboratory">
</picture>

**Carlos Ulisses Flores** — Codex Hash Research Laboratory

[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--6034--7765-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0000-0002-6034-7765)
[![Website](https://img.shields.io/badge/Website-ulissesflores.com-1f6feb)](https://ulissesflores.com)
[![Lattes](https://img.shields.io/badge/Lattes%20CV-CNPq-0a7d3c)](https://lattes.cnpq.br/6905246706890561)

## Citazione

Si citi il DOI di concetto, [10.5281/zenodo.24471761](https://doi.org/10.5281/zenodo.24471761). Identifica il pacchetto in tutte le sue
versioni e rimanda sempre alla più recente. Ogni release ha anche un proprio DOI di versione, elencato nella pagina
di Zenodo; si citi quello quando servono i file esatti. L'archivio grezzo delle prove è un record separato,
[10.5281/zenodo.24450523](https://doi.org/10.5281/zenodo.24450523). [`CITATION.cff`](CITATION.cff) contiene i metadati di citazione nel formato letto
dagli strumenti di citazione.

```bibtex
@software{flores2026claimrecords,
  author    = {Flores, Carlos Ulisses},
  title     = {Claim records and what a coding agent says: four experiments — replication package},
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

## Licenza

Codice sorgente sotto **Apache-2.0** ([`LICENSE`](LICENSE)); documenti, dati e testo dell'articolo sotto
**CC BY 4.0** ([`LICENSES/CC-BY-4.0.txt`](LICENSES/CC-BY-4.0.txt)). I file di terzi in `overclaim/` e `rescore/`
sono MIT ([`overclaim/LICENSE`](overclaim/LICENSE)). Si veda [`NOTICE`](NOTICE).

## Riferimenti di ancoraggio

- benchmark overclaim: <https://github.com/h-a-forster/overclaim>
- formato di registro Eilikrineia: <https://github.com/ulissesflores/eilikrineia>
- registrazione dello studio 3: <https://osf.io/rjnt2>
