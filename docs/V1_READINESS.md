# V1 readiness — Archivio Personale AI

## Scopo v1

Archivio Personale AI v1 è un helper **local-first**, **review-only** e **safety-first** per l'inventario e la classificazione dry-run di un archivio di file personali su PC locale o HDD interno.

- **Local-first**: tutti gli script girano sul PC locale; nessun dato inviato all'esterno.
- **Review-only**: i report sono strumenti di revisione manuale; non costituiscono istruzioni operative automatiche.
- **Safety-first**: nessuna operazione di spostamento, rinomina, cancellazione o sovrascrittura.
- **Orientato a inventario, classificazione dry-run e report manuali**: la v1 produce solo output JSON e HTML per revisione umana.

## Principio base

La v1 aiuta a **capire e revisionare** l'archivio, non ad agire automaticamente sui file.

Nessuno script della v1 sposta, rinomina, cancella o sovrascrive file personali. Qualunque decisione operativa resta interamente all'utente.

## Pronto per v1

Componenti implementati e testati:

- [x] First-run check (`scripts/run_first_time_check.py`)
- [x] Validation runner (`scripts/run_validations.py`)
- [x] Synthetic demo (`scripts/run_synthetic_demo.py`)
- [x] Inventory read-only (`scripts/inventory_readonly.py`)
- [x] Inventory HTML report (`scripts/generate_inventory_report.py`)
- [x] Classification dry-run (`scripts/classify_inventory.py`)
- [x] Classification HTML report (`scripts/generate_classification_report.py`)
- [x] Action plan review-only (`scripts/generate_action_plan.py`)
- [x] Action plan HTML report (`scripts/generate_action_plan_report.py`)
- [x] Report validator (`scripts/validate_reports.py`)

## Non implementato e non autorizzato

Le seguenti operazioni non sono implementate nella v1 e non devono essere introdotte senza esplicita autorizzazione dell'utente:

- Move reali su file personali
- Rename reali su file personali
- Delete reali su file personali
- Overwrite di file sorgente
- Cloud o servizi esterni sui contenuti personali
- Google Drive API
- n8n runtime sui file personali
- MCP/filesystem agent sui file personali
- Apertura automatica di report o browser

## Comandi minimi di verifica v1

```powershell
# verifica prerequisiti locali
python .\scripts\run_first_time_check.py

# controlli essenziali (py_compile + validate_reports --help)
python .\scripts\run_validations.py --quick

# demo sintetica rapida (nessun file personale)
python .\scripts\run_synthetic_demo.py --quick
```

## Validazione completa locale

```powershell
# suite test completa
python -m unittest discover

# runner validazioni completo (include first-run check, unittest, demo)
python .\scripts\run_validations.py

# demo sintetica completa (tutte le 7 fasi su dati sintetici)
python .\scripts\run_synthetic_demo.py
```

## Uso su archivio reale

Quando si lavora sull'archivio reale:

- La cartella sorgente deve restare **fuori dal repository** (es. `C:\Archivio_Test`).
- Tutti gli output (`reports/inventory.json`, `reports/classifications.json`, ecc.) vanno in `reports/` e **non devono essere committati**.
- I report HTML sono strumenti di **revisione manuale**: devono essere aperti esplicitamente dall'utente, mai automaticamente.
- Nessuna azione automatica viene eseguita sui file personali.

## Flusso reale consigliato

Ordine operativo raccomandato per lavorare su un archivio reale:

1. **Inventario read-only**
   ```powershell
   python scripts/inventory_readonly.py --source "C:\Archivio_Test" --output reports/inventory.json
   ```
2. **Inventory HTML report**
   ```powershell
   python scripts/generate_inventory_report.py --input reports/inventory.json --output reports/inventory_report.html
   ```
3. **Classification dry-run**
   ```powershell
   python scripts/classify_inventory.py --input reports/inventory.json --output reports/classifications.json
   ```
4. **Classification HTML report**
   ```powershell
   python scripts/generate_classification_report.py --input reports/classifications.json --output reports/classification_report.html
   ```
5. **Action plan review-only**
   ```powershell
   python scripts/generate_action_plan.py --inventory reports/inventory.json --classifications reports/classifications.json --output reports/proposed_actions.json
   ```
   Il piano azioni è solo informativo: lo spazio recuperabile (`potential_reclaimable_human`) è puramente teorico e nessuna cancellazione è proposta.
6. **Action plan HTML report**
   ```powershell
   python scripts/generate_action_plan_report.py --input reports/proposed_actions.json --output reports/action_plan_report.html
   ```
7. **Validate reports**
   ```powershell
   python .\scripts\validate_reports.py
   ```

I report HTML generati devono essere aperti **manualmente** dall'utente. Nessun comando li apre automaticamente.

## Criteri di stop

Fermarsi immediatamente se compaiono:

- Richieste di move, rename o delete reali su file personali
- Richieste di uso di cloud, API esterne o token/secrets
- File personali aggiunti al repository
- Output generati (`reports/`) tracciati da Git e proposti per il commit
- Istruzioni che contraddicono `docs/SAFETY_RULES.md`

## Definizione di v1 pronta

Questa checklist è usata come **release-candidate checklist locale**: soddisfarla conferma che la pipeline locale è pronta per l'uso review-only. Non costituisce una garanzia di operazioni automatiche né un'approvazione implicita di passi che esulano dalla natura read-only/dry-run del progetto.

La v1 è pronta per uso locale review-only quando:

- [ ] Workspace Git pulito (`git status --short` vuoto)
- [ ] Suite test passata (`python -m unittest discover`)
- [ ] Demo sintetica passata (`python .\scripts\run_synthetic_demo.py --quick`)
- [ ] README.md e docs/COMMANDS.md coerenti con questa checklist
- [ ] Nessun report né file personale committato nel repository
- [ ] LLMS.md aggiornato con l'ultimo batch e commit hash

## Cosa controllare prima di lavorare su file reali

Prima di eseguire script sull'archivio reale, verificare che:

- Il repository sia pulito (`git status --short`)
- I comandi di validazione passino (`run_first_time_check.py`, `run_validations.py --quick`)
- La cartella sorgente sia fuori dal repository
- Gli output siano configurati in `reports/` (non nella sorgente)
- Nessun automatismo distruttivo sia attivo o pianificato

## Cosa controllare dopo la generazione dei report

Dopo aver generato i report, verificare che:

- I file HTML siano presenti in `reports/`
- I report siano in italiano (`lang="it"` verificabile con `validate_reports.py`)
- I report siano review-only (nessuna proposta di cancellazione automatica)
- Nessun report sia stato aperto automaticamente
- Nessuna proposta di cancellazione sia stata eseguita

## Commit e tracking

- Ogni batch di task deve avere un ID (`ARCH-XXXX..ARCH-YYYY`)
- `LLMS.md` deve riportare il commit hash finale di ogni batch chiuso
- I micro-fix di tracking (aggiornamento commit hash) sono ammessi e necessari
- Usare sempre staging selettivo: `git add <file>` per ogni file esplicitamente; **non usare `git add .`**

## Validation-only

Un task di sola verifica (es. controllare che un comportamento esista già) può non produrre commit se non modifica alcun file. L'esito corretto è: nessun nuovo commit, workspace pulito, comportamento verificato.

## Limiti intenzionali della v1

La v1 non include e non deve includere:

- Riordino automatico di file personali
- Integrazione con servizi cloud
- Classificazione AI cloud su contenuti di file personali
- Agente filesystem libero di operare senza approvazione esplicita

Questi limiti sono intenzionali e definiscono la natura review-only del progetto.

## Prossimi miglioramenti consentiti

I miglioramenti ammessi per iterazioni future, senza cambiare la natura review-only:

- Migliorare la copertura e la chiarezza dei test
- Migliorare la documentazione (README, COMMANDS, questa checklist)
- Migliorare la chiarezza e la leggibilità dei report HTML
- Migliorare le validazioni locali (struttura, wording, invarianti)

Qualunque miglioramento che introduca operazioni automatiche sui file personali o dipendenze esterne richiede esplicita approvazione dell'utente e aggiornamento di `docs/SAFETY_RULES.md`.
