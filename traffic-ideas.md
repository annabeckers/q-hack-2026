Die kurze Antwort: **Es kommt stark darauf an, wie das VPN und das zugrundeliegende Netzwerk konfiguriert sind.**

Da Tools wie *Claude Code* (und generell fast alle modernen APIs) für die Kommunikation standardmäßig **HTTPS (TLS-Verschlüsselung)** nutzen, ist der eigentliche Inhalt der Datenpakete kryptografisch geschützt. Ob und wie viel jemand mitlesen kann, teilt sich in zwei typische Szenarien auf:

### Szenario 1: Standard-VPN (Ohne SSL-Inspection)
Wenn du ein typisches Consumer-VPN (wie NordVPN, Mullvad) oder ein normales Firmen-VPN nutzt, das den Verkehr einfach nur durch einen Tunnel leitet:

* **Was sichtbar ist:** Der VPN-Betreiber oder der Netzwerk-Admin sieht lediglich **Metadaten**. Er kann durch DNS-Requests oder die Ziel-IP sehen, *dass* dein Rechner mit den Servern von Anthropic (z. B. `api.anthropic.com`) kommuniziert. Außerdem sieht er den Zeitstempel und die Größe der Datenpakete.
* **Was NICHT sichtbar ist:** Die eigentlichen Inhalte. Deine Prompts, dein lokaler Code, deine API-Keys und die Antworten der KI bleiben durch die Ende-zu-Ende-Verschlüsselung verborgen. Für den Beobachter ist das nur unlesbarer Zeichensalat.

### Szenario 2: Firmen-Netzwerk mit "SSL Inspection" (Deep Packet Inspection)
Viele große Unternehmen setzen in ihren VPNs oder Firmennetzwerken Security-Proxies (z. B. Zscaler, Palo Alto Networks) ein, die HTTPS-Verkehr gezielt aufbrechen. Das funktioniert technisch wie ein gewollter "Man-in-the-Middle"-Angriff. Voraussetzung dafür ist, dass auf deinem Rechner (meist durch die IT-Abteilung) ein spezielles Firmen-Zertifikat (Root-CA) installiert wurde.

* **Was sichtbar ist:** **Alles.** Die Security-Appliance der Firma entschlüsselt den Verkehr, analysiert ihn auf Schadcode oder Datenabfluss (DLP) und verschlüsselt ihn dann wieder, bevor er ans Internet weitergeht. Das Unternehmen kann den kompletten Datenverkehr im Klartext mitlesen.

---

### Was kommt da typischerweise raus (bei SSL-Inspection)?

Wenn der Verkehr entschlüsselt wird, sieht der Beobachter die reinen HTTP-Requests an die Anthropic API. Bei einem CLI-Tool wie *Claude Code* sind das strukturierte JSON-Pakete. 

Das sieht im Log typischerweise so aus:

**1. Authentifizierung & Header**
Man sieht genau, mit welchem Account oder welchem API-Key die Anfrage gemacht wird:
```http
POST /v1/messages HTTP/1.1
Host: api.anthropic.com
x-api-key: sk-ant-api03-...[DEIN_ECHTER_API_KEY]...
```

**2. Der Request Payload (Was an die KI gesendet wird)**
Claude Code ist ein Agenten-Tool. Es sendet nicht nur das, was du ins Terminal tippst, sondern sammelt selbstständig Kontext aus deiner lokalen Umgebung. Der abgefangene Payload enthält unter anderem:
```json
{
  "model": "claude-3-7-sonnet-20250219",
  "system": "You are Claude, an AI programming assistant...",
  "messages": [
    {
      "role": "user",
      "content": "Finde den Bug in der Login-Komponente."
    },
    {
      "role": "user",
      "content": "Hier ist der Inhalt der Datei src/components/Login.tsx: \n\n [KOMPLETTER QUELLCODE DEINER DATEI]"
    },
    {
      "role": "user",
      "content": "Hier ist der letzte Fehler aus dem Terminal: \n\n [STACKTRACE]"
    }
  ]
}
```
*Wichtig hierbei:* Man sieht nicht nur deine Frage, sondern **deinen proprietären Source-Code**, Dateipfade, Systemumgebungsvariablen und Terminal-Outputs, die Claude Code automatisch als Kontext mit an die API schickt, um das Problem zu lösen.

**3. Die Response (Die Antwort der KI)**
Die Antwort kommt ebenfalls als Klartext-JSON zurück. Dort ist der von der KI generierte Code enthalten, inklusive der Werkzeugaufrufe (Tool Calls), mit denen Claude Code beispielsweise Befehle in deinem lokalen Terminal ausführt (z. B. `npm run build` oder das Ändern einer Datei).

### Fazit
Sitzt du an einem privaten Rechner ohne installierte Fremdzertifikate, sind deine Prompts und dein Code durch HTTPS sicher – auch im VPN. Arbeitest du jedoch auf einem von der Firma verwalteten Rechner, musst du davon ausgehen, dass die IT-Sicherheit theoretisch jeden Prompt, deinen API-Key und jeden Code-Schnipsel sehen kann, den Claude Code an die Server von Anthropic funkt.