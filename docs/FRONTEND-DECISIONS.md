# EduSub frontend: Unterrichtskonzepte und begründete Entscheidungen (HS26)

## Unterrichtsbezug

Basis: *07-Frontend-and-API-Integration-HS26*, besonders Folien 8–13 (HTML, CSS, JavaScript und Events), 48–55 (`try/catch/finally`, `fetch`, JSON und Network), 57–63 (Frontend-Alternativen und integrierter Workflow). Die Anhänge *07A-Static-to-Jinja-HS26* und *07B-Frontend-Alternatives-HS26* zeigen alternative Implementierungswege; sie sind optional.

| Gelerntes Konzept | EduSub-Umsetzung | Warum das sinnvoll ist |
| --- | --- | --- |
| HTML-Struktur und zugängliche Formulare | Semantische `<form>`, `<label>`, `<input>`, `<select>`, `<button>` und Tabellen in den React-Komponenten | Browser können die Eingaben verstehen; strukturierte Oberflächen sind bedienbarer. |
| CSS und responsive Layouts | `frontend/src/style.css` mit flexiblen Layouts und Media Queries | Desktop und Mobilgeräte benötigen unterschiedliche Anordnungen. |
| JavaScript-Ereignisse | `onSubmit`, `onClick`, `onChange` | Benutzereingaben lösen nachvollziehbare Aktionen aus. |
| Zustandsverwaltung | React `useState` für Formulare, Ladezustände, Listen und Meldungen | UI-Daten ändern sich durch HTTP-Antworten; React hält die Ansicht mit dem Zustand synchron. |
| API-Aufruf über HTTP/JSON | `frontend/src/api.js` nutzt `fetch`, `JSON.stringify`, HTTP-Methoden und Bearer-Token | Frontend und Backend bleiben getrennt; dieselbe FastAPI-API ist unabhängig mit Swagger testbar. |
| Fehlerbehandlung | `try/catch/finally`, sichtbare Alerts, deaktivierte Buttons während einer Aktion | Ungültige Eingaben und API-Fehler bleiben für Nutzende verständlich. |
| Erfolgsnachweis | `POST /requests/` bzw. `POST /requests/{id}/apply`, danach erneutes `GET` | Eine grüne Erfolgsmeldung allein beweist keine Speicherung; serverseitige Daten werden erneut gelesen. |
| Daten und Berechtigungen | Admin-Ansicht ruft Admin-API auf; Lehrpersonenansicht ruft nur lehrpersonenspezifische Endpunkte auf | Rollenabhängige UI ist benutzerfreundlich; die eigentliche Zugriffsprüfung bleibt zwingend im Backend. |
| Komponenten | Separate `TeacherDashboard.jsx` für den Lehrpersonen-Workflow | Verantwortlichkeiten bleiben begrenzt; die Sicht ist leichter weiterzuentwickeln und zu testen. |
| CRUD-Methoden | `RequestRow.jsx` sendet `PATCH` für Änderungen und `DELETE` für das Entfernen einer Anfrage | Die HTTP-Methode macht die beabsichtigte Operation sichtbar. `PATCH` verändert ausgewählte Felder, `DELETE` liefert bei Erfolg HTTP 204 ohne JSON-Antwort. |

## Warum React/Vite und nicht Jinja oder eine reine statische Seite?

- **Statische Seite:** Gut für frühe Skizzen, kann aber ohne API-Anbindung keine Stellvertretungen dauerhaft speichern.
- **Jinja2:** Laut Unterricht ausdrücklich zulässig; wäre sinnvoll für eine kleinere Anwendung mit klassischen Seiten- und Formularwechseln. Hier wären jedoch ein zweiter Darstellungsweg auf dem FastAPI-Server und ein Umbau der bereits funktionierenden React-Oberfläche nötig.
- **React mit Browser-API:** Wir benötigen wiederholtes Aktualisieren von Listen, Statuswechsel und unterschiedliche Rollenansichten. Die vorhandene React/Vite-Oberfläche kommuniziert bereits mit der dokumentierten REST API. Deshalb behalten wir diesen Weg bei. **React ist eine bewusste Projektentscheidung, keine Pflicht des Moduls.**
- **NiceGUI:** Das ursprüngliche EduSub aus Advanced Programming diente als fachliche Grundlage. Für dieses Modul wollen wir die Grenze zwischen eigenständigem Browser-Frontend, REST API, Services und Persistenz sichtbar machen.

## Architektur und konkreter Integrationsablauf

1. Der Browser öffnet die React-Anwendung auf Port 5173.
2. Bei `fetch('/api/v1/requests/open')` leitet Vite während der lokalen Entwicklung die Anfrage an FastAPI auf Port 8000 weiter (`frontend/vite.config.js`).
3. FastAPI prüft Bearer-Token und Lehrerrolle, danach liefern Service und Datenbank nur offene Anfragen.
4. React zeigt die Antwort als Liste und ermöglicht die Bewerbung per `POST /api/v1/requests/{id}/apply`.
5. Nach HTTP 201 lädt React offene Anfragen und eigene Bewerbungen erneut (`GET /api/v1/applications/my`).
6. Ein API-Fehler wird angezeigt; er gilt nicht als erfolgreiche Bewerbung. Zusätzlich prüft das Backend die Berechtigungen und Geschäftsregeln.

Die bestehende Administrator-Demo (Login → Anfrage erstellen → gespeicherte Anfrage lesen) ist **manuell bestätigt**. Die Lehrpersonen-Demo wurde inzwischen ebenfalls mit einem freigeschalteten Lehrpersonen-Account getestet.

**Statusnachtrag, 16 November 2026:** Die Lehrpersonen-Demo wurde manuell erfolgreich getestet (Login, offene Anfragen, Klassenfilter, Bewerbung und Status `pending`). Der Filter listet absichtlich nur Klassen mit aktuell offenen Anfragen; bereits besetzte Anfragen erscheinen nicht als bewerbbar. Die ergänzte React-Komponente `AdminApplications.jsx` verwendet `GET /applications/pending`, `GET /teachers/` und `PATCH /applications/{id}/approve|reject` und lädt nach der Entscheidung die gespeicherten Daten neu. Dieser Admin-Teil ist noch nicht manuell getestet.

## Nachweis im Browser (für Coaching und Abgabe)

1. Im Browser DevTools → Network öffnen.
2. Als genehmigte Lehrperson anmelden; `GET /api/v1/auth/me` und `GET /api/v1/requests/open` prüfen.
3. Eine offene Stellvertretung wählen und auf **Bewerben** klicken.
4. Im Network-Tab `POST /api/v1/requests/{id}/apply` (erwartet 201) und den anschliessenden `GET /api/v1/applications/my` prüfen.
5. Die eigene Bewerbung muss in der Oberfläche erscheinen; ein erneuter Klick auf denselben Auftrag darf keine zweite Bewerbung erzeugen.
6. Einen Negativfall demonstrieren, z. B. ein Versuch mit fehlender Genehmigung oder eine doppelte Bewerbung. **Erwartete** HTTP-Statuscodes erst nach dem tatsächlichen Test als **bestätigt** dokumentieren.

Keine echten Passwörter, JWTs oder persönlichen Lehrpersonen-Dokumente in Screenshots/Commits speichern.

## Grenzen und weitere Arbeit

### Administrator: Anfragen bearbeiten und löschen

Die Anfragen-Tabelle enthält für offene Anfragen eine Bearbeiten- und eine Löschen-Aktion. Beim Bearbeiten werden die gespeicherten Felder in ein HTML-Formular übernommen. `validateTimeRange` prüft beide Uhrzeiten vor dem Speichern; zusätzlich validiert FastAPI den Payload. `PATCH /api/v1/requests/{id}` aktualisiert die bestehende Anfrage, danach holt React die gesamte Liste erneut über `GET /requests/`. Beim Löschen fragt `window.confirm` nach und sendet `DELETE /api/v1/requests/{id}`; der API-Client behandelt HTTP 204 ohne JSON-Parsing.

**Entscheidung:** `PATCH` statt `PUT`, weil eine bestehende Ressource gezielt geändert wird. Ein Klick auf einen Button allein gibt keine Berechtigung: Das Backend verweigert Änderungen an nicht offenen Anfragen und das Löschen bei vorhandenen Bewerbungen (Konflikt, HTTP 409). Die Oberfläche blendet für besetzte Anfragen die Aktionen aus, zeigt aber auch Serverfehler sichtbar an. Während eines Requests sind die Buttons gesperrt. Die Komponente ist getrennt von `main.jsx`, damit Tabellenansicht, Formularzustand und HTTP-Aktionen gekapselt bleiben.

**Nachweisstatus (16. November 2026):** Der gemeinsame Browserdurchlauf für vier Prüfungen wurde vom Team als bestanden bestätigt: offene Anfrage ändern, ungültigen Zeitraum ablehnen, offene Anfrage ohne Bewerbungen löschen und Aktionen für besetzte Anfragen ausblenden. Der gesonderte HTTP-409-Konfliktfall bei bestehenden Bewerbungen wurde noch **nicht** manuell geprüft. Frontend-Unit-Tests und Build waren bei der Implementierung ebenfalls erfolgreich (7 Tests).

**Teststrategie:** Die bestehenden Pydantic-/FastAPI-Tests prüfen Eingabevalidierung, Geschäftsregeln und Datenbankzustand schnell und isoliert; ein zusätzlicher Backend-Test sichert jetzt die Löschsperre bei vorhandener Bewerbung ab (HTTP 409, Daten bleiben erhalten). Playwright ergänzt als Browser-End-to-End-Test die realen Klicks und Statuswechsel über React, Vite-Proxy, FastAPI und SQLite. Der Playwright-Test verwendet fiktive Konten und eine temporäre Datenbank, um reproduzierbar zu sein. Seine erste Ausführung blieb wegen einer Chromium-Sandbox-Sperre in der Entwicklungsumgebung blockiert; eine erfolgreiche lokale Ausführung steht aus.

### Registrierung und Admin-Freigabe – neuer Baustein

Neu ergänzt wurden `frontend/src/RegisterForm.jsx` und `frontend/src/AdminTeacherApprovals.jsx`:

1. Ein HTML-Formular nimmt Name, E-Mail, Telefonnummer und Passwort auf. Der Browser prüft die Passwortbestätigung sowie die minimale Länge.
2. `FormData` überträgt die Eingaben als `multipart/form-data` an `POST /api/v1/auth/register`. Ein JSON-Body wäre falsch, da das vorhandene FastAPI-Interface `Form(...)` erwartet.
3. Das Backend speichert die neue Lehrperson mit `is_approved = false`; die Oberfläche zeigt **noch keine erfolgreiche Anmeldung** an.
4. `POST /api/v1/auth/login` verweigert nicht freigegebenen Lehrpersonen den Zugriff (HTTP 403, durch Backend-Test geprüft).
5. Der Administrator ruft `GET /api/v1/teachers/pending` auf, bestätigt die Freigabe und sendet `PATCH /api/v1/teachers/{id}/approve`.
6. Danach können genehmigte Lehrpersonen die bestehende React-Lehrpersonenansicht verwenden.

**Unterrichtsbezug:** HTML-Formulare, JavaScript-Ereignisse, `fetch`, FormData statt JSON je nach API-Vertrag, HTTP-Statuscodes, Fehlermeldungen, rollenbasierte Berechtigungen und Persistenz. React steuert die Anzeige; die Autorisierung bleibt verbindlich in FastAPI.

**Bewusste Einschränkung:** Dokument-Uploads und Fächerauswahl im öffentlichen Registrierungsformular sind noch nicht enthalten. Der bestehende Backend-Upload benötigt vor Nutzung mit echten persönlichen Unterlagen eine Sicherheitsprüfung (Dateizugriff, Validierung und Speicherung). Nur fiktive Testkonten verwenden.

- Frontend-Build und 7 bestehende Unit-Tests bestanden; Backend mit neuem Registrierungs-Freigabe-Test: **13 bestanden**. Der neue Browserablauf wurde anschliessend **von einem Teammitglied manuell bestätigt** (Registrierung, Admin-Freigabe und Anmeldung).

- Lehrpersonenregistrierung und -freigabe sind jetzt im React-Frontend umgesetzt, müssen aber noch im Browser getestet werden.
- Der Admin kann Bewerbungen bereits über Swagger genehmigen, aber noch nicht über die React-Oberfläche.
- Für komplexere UI ist eine weitere Aufteilung des derzeit grossen `main.jsx` in Komponenten sinnvoll.
- Automatisierte Browser-End-to-End-Tests, barrierearme Bedienung und Tests auf Mobilgeräten fehlen noch.
- Die Teambeiträge und Entscheidungen aus dem Coaching sind durch die tatsächlichen Teammitglieder zu ergänzen.
