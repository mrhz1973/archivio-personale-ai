# Archivio Personale AI

Strumento **local-first** e **safety-first** per inventario e classificazione **dry-run** di archivi personali.

## Stato operativo essenziale

- Fase corrente: inventario read-only + classificazione rule-based + report HTML in italiano.
- Modalità: review-only (nessuna azione automatica sul sorgente).
- Operazioni vietate: move, rename, delete, overwrite, riorganizzazione automatica.
- Nessun uso di API cloud per contenuti personali.

## Implementazione (operational guardrails)

- Un solo implementatore attivo alla volta: **Claude Code** (primario) oppure **Codex** (backup).
- Prima di cambiare implementatore: verificare workspace pulito/allineato.
- Ambiente locale utente: **Windows**; per operazioni locali usare **PowerShell**.

## Comandi e regole

- Comandi consentiti: `docs/COMMANDS.md`
- Regole di sicurezza: `docs/SAFETY_RULES.md`
- Flusso operativo: `docs/WORKFLOW.md`
- Regole LLM/implementatori (fonte compatta): `LLMS.md`

## Requisiti

- Python 3.8+ (solo standard library)
