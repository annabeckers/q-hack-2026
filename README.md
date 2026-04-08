# q-hack-2026

## Your developers are leaking secrets to AI — and nobody is watching.

Real-time secret detection. Malicious package scanning. Cost and compliance visibility.
Deployed on a Raspberry Pi you ship to any team — no cloud required, working in minutes.

> Full concept: [concept.md](concept.md) | Hero statement: [hero-statement.md](hero-statement.md) | Data model: [chat-history-data-model.md](chat-history-data-model.md)

---

## Dashboard Features

### 1. Auswertung von KI-Tool Nutzung
- Welche Tools werden wie oft genutzt (ChatComposer, CodeAssist, SummaryBot, …)?
- Nutzungsfrequenz pro Zeitraum (täglich, wöchentlich)
- Top-User (pseudonymisiert) und aktivste Abteilungen

### 2. Kosten
- Gesamtkosten pro Abteilung, Tool, Modell
- Kostenentwicklung über Zeit (Trend)
- Budget-Alerts bei Überschreitung definierter Schwellenwerte

### 3. Nutzung welcher Modelle
- Aufteilung: GPT-4o vs. Claude vs. Gemini vs. lokale Modelle
- Kosten-/Qualitäts-Verhältnis je Modell
- Empfehlung günstigerer Alternativen für einfache Use Cases
  → z. B. Scaleway AI: https://www.scaleway.com/en/ als DSGVO-konformer EU-Provider

### 4. Aggregiert über Firma oder Abteilung
- Drill-down: Firma → Abteilung → Team → User (hash)
- Vergleich Abteilungen untereinander (Kosten, Token, Modellwahl)
- Export als CSV/PDF für Management-Reporting

### 5. Abgleich mit Firmeninfos & Keyword-Regex-Matching
- Scan von Prompts und Logs auf sensible Firmeninhalte
- Regex-Pattern-Bibliothek: `aws_secret`, API-Keys, IBAN, interne Projekt-Namen, etc.
- Alarm bei Match — Eintrag wird im Dashboard rot markiert
- `secrets_scanner.py` — ready to use

### 6. LLM: Verwendung für triviale Fragen (Auswertung)
- Erkennung von Low-Value-Anfragen (kurze Antworten, einfache Patterns)
- Kosten-Effizienz-Score je Anfrage
- Empfehlung: einfache Fragen → günstigeres Modell oder lokales LLM

### 7. ~~LLM: Private Nutzung erkennen~~ — DROPPED
> Removed: BetrVG §87(1) Nr. 6 makes individual-level usage classification a works council co-determination issue. Legal minefield in Germany. See [concept.md](concept.md#legal-considerations).

### 8. Zukünftige Gesetzgebung (EU AI Act & Co.)
- Tracking welche Modelle als "High Risk" eingestuft werden könnten
- Pflichtfelder für Compliance-Log (Audit-Trail, Zweck, Modell, Region)
- Vorbereitung auf Meldepflichten (Logging bereits strukturiert)

### 9. Slopsquatting-Scan
- KI-Systeme empfehlen gelegentlich nicht-existente oder manipulierte Library-Namen
- Scanner prüft KI-generierte `import`-Statements gegen PyPI / npm-Allowlist
- Warnung bei unbekannten oder verdächtigen Paketnamen
- `slopsquatting_scanner.py` — ready to use

### 10. Datenfluss zu Providern (Wer sieht was?)
- Welche Agents haben Zugriff auf welche Codebasen?
- Indexieren Agents die gesamte Codebase? (→ IP-Risiko)
- Mapping: Datentyp → Provider → Region → Datenschutzrisiko
- `provider_flow.py` — ready to use

### 11. Critical Prompts — Echtzeit-Flagging (KEY FEATURE)
**User Story:** *Hannes leakt zu oft Secrets — auch bei lokalen LLMs analysieren wir, was rausgeht.*
- KI-Agent scannt jeden ausgehenden Prompt in Echtzeit
- Erkennt: API Keys, AWS Secrets, Passwörter, interne IPs, PII
- Dashboard: rote Sidebar mit Ausrufezeichen-Icon bei Fund
- Automatische Benachrichtigung an Source: *"API Key geleakt — bitte sofort rotieren"*
- Gilt auch für lokale LLMs (Ollama, LM Studio) — Traffic-Analyse on-device
- Sofortiger Alert via Slack / E-Mail / Webhook

### 12. Raspberry Pi — Plug & Play Test Lab
**Deployment-Modell:** Unternehmen bekommen einen vorkonfigurierten Pi zugeschickt — als eigenständiges, isoliertes System zum Ausprobieren.
- **Playground-Modus:** Separates System, kein Eingriff in bestehende Infrastruktur — nichts geht kaputt
- **Server-Modus:** Alternativ als dauerhafter Service im bestehenden Netzwerk deploybar
- Service startet automatisch, analysiert lokale AI-Nutzungsdaten:
  - Geleakte Secrets, sensible Firmendaten, PII
  - Welche Daten zu welchen Providern fließen
  - Nutzungsmuster und Kosten-Schätzungen
- Lokales LLM auf dem Pi für On-Device-Klassifikation (lightweight Modelle)
- Live-Dashboard im Browser über lokales Netzwerk
- Generiert automatisch Recommendations: Risiken, Compliance-Lücken, Optimierungen
- Nach Testphase: Ergebnisse als Report → Grundlage für Upselling auf Full-Service

---

## Technischer Build-Plan (Schritt für Schritt)

### Schritt 0 — Mock-Daten erstellen
Direkt als `logs.jsonl` mit 20 Einträgen.
**Felder:** `id, user_id_hash, department_id, tool_name, model_name, usage_start, usage_end, token_count, cost, purpose, region`
→ Datei: `logs.jsonl`

### Schritt 1 — Anonymisierung echter Daten
Echte Chats/Logs vor Nutzung pseudonymisieren:
- PII-Felder hashen (`user_id`, `email` → stabiler Hash)
- Freitextfelder auf `[REDACTED]` setzen
- DSGVO-konformer Output
→ Skript: `step1_anonymize.py`

### Schritt 2 — Mock-Streaming mit Faker
Python-Worker generiert realistische Logs kontinuierlich:
- Zufällige Modelle, Tools, Abteilungen, Kosten
- One-shot oder kontinuierlicher Stream-Modus
→ Skript: `step2_mock_stream.py`

### Schritt 3 — Datenbank-Setup
PostgreSQL lokal via Docker:
- Tabelle `tools_usage` mit Indizes
- Aggregations-View `daily_department_summary`
→ `step3_schema.sql` + `docker-compose.yml`
```bash
docker compose up -d
```

### Schritt 4 — Ingest-Loop
Lese `logs.jsonl` Zeile für Zeile → UPSERT in PostgreSQL:
```bash
python step4_ingest.py
# → SELECT COUNT(*) FROM tools_usage; zeigt Anzahl Einträge
```
→ Skript: `step4_ingest.py`

### Schritt 5 — Compliance-Validator
Scan jedes Records auf PII, Schema-Fehler, Anomalien:
```bash
python step5_compliance_check.py
# Exit 0 = alles ok, Exit 1 = Issues gefunden
```
→ Skript: `step5_compliance_check.py`

### Schritt 6 — Secrets & Critical-Content Scanner
Echtzeit-Flagging geleakter Secrets in Prompts/Logs:
```bash
python secrets_scanner.py --file logs.jsonl
```
→ Skript: `secrets_scanner.py`

### Schritt 7 — Slopsquatting-Detektor
Prüft KI-empfohlene Library-Namen gegen bekannte Pakete:
```bash
python slopsquatting_scanner.py --file ai_suggestions.txt
```
→ Skript: `slopsquatting_scanner.py`

### Schritt 8 — Provider-Datenfluss-Analyse
Zeigt welche Daten zu welchem Provider fließen:
```bash
python provider_flow.py --file logs.jsonl
```
→ Skript: `provider_flow.py`

### Schritt 9 — Dashboard-Aggregator
Kosten- und Nutzungsauswertung per Abteilung/Modell:
```bash
python dashboard_aggregator.py --file logs.jsonl
```
→ Skript: `dashboard_aggregator.py`

---

## Schnellstart

```bash
# 1. Datenbank starten
docker compose up -d

# 2. Dependencies
pip install psycopg2-binary faker requests

# 3. Daten ingestieren
python step4_ingest.py

# 4. Compliance & Secrets prüfen
python step5_compliance_check.py
python secrets_scanner.py --file logs.jsonl

# 5. Dashboard-Auswertung
python dashboard_aggregator.py --file logs.jsonl

# 6. Streaming-Demo (live Events)
python step2_mock_stream.py --stream --interval 3
```

---

## Sicherheit & DSGVO

- Keine echten Nutzerdaten in `logs.jsonl` verwenden
- `user_id_hash` in UI maskiert anzeigen
- Audit-Logging nur auf Dummy-Events
- LLM-Prompts: nur anonymisierte Aggregate-Daten (kein PII)
- Secrets-Scanner läuft auch bei lokalen LLMs (Traffic bleibt on-device)
