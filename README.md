# Remix SMP Bot

Bot Discord per il server Minecraft **Remix SMP**, scritto in Python con `discord.py`.

| Comando | Chi lo vede | Cosa fa |
|---|---|---|
| `/status` | tutti | Mostra se il server è online, i giocatori, l'IP, la versione e il ping |
| `/kick`, `/ban` | chi può espellere o bannare | Espelle o banna un utente, con motivo facoltativo |
| `/timeout`, `/untimeout` | chi può silenziare | Silenzia un utente per N minuti, o toglie il timeout |
| `/clear` | chi può gestire i messaggi | Cancella gli ultimi 1–100 messaggi del canale |
| `/ticket-panel` | admin | Pubblica il pannello con il bottone **Apri un ticket** |

Lo stato del bot ("12/50 online su Remix SMP") si aggiorna da solo ogni 2 minuti.

## 1. Crea il bot su Discord (si fa tutto da Safari)

1. Apri https://discord.com/developers/applications e premi **New Application**. Chiamala "Remix SMP".
2. Vai su **Bot** e premi **Reset Token**, poi copia il token. È la password del bot: non darla a nessuno.
3. Vai su **OAuth2 → URL Generator**:
   - in *Scopes* spunta `bot` e `applications.commands`;
   - in *Bot Permissions* spunta: View Channels, Send Messages, Embed Links, Read Message History,
     Manage Messages, Manage Channels, Manage Roles, Kick Members, Ban Members, Moderate Members.
4. Apri il link generato in fondo e scegli il tuo server.
5. In Discord vai su **Impostazioni server → Ruoli** e trascina il ruolo del bot **sopra** i ruoli dei giocatori.
   Senza questo passaggio il bot non può moderarli.

Per copiare gli ID (server, ruolo staff, categoria) attiva *Impostazioni → Avanzate → Modalità sviluppatore*,
poi tieni premuto sull'elemento e scegli **Copia ID**.

## 2. Configurazione

Copia `.env.example` in un file chiamato `.env` e compila i campi:

- `DISCORD_TOKEN`: il token del bot (obbligatorio)
- `GUILD_ID`: l'ID del tuo server Discord, così i comandi compaiono subito
- `MC_ADDRESS`: l'IP del server Minecraft, ad esempio `play.remixsmp.it` o `1.2.3.4:25565`
- `STAFF_ROLE_ID`: i ruoli staff separati da virgola (es. `111,222,333`); vedono tutti i ticket e ricevono una menzione quando ne viene aperto uno
- `TICKET_CATEGORY_ID`: la categoria in cui creare i canali ticket (facoltativo)

## 3. Mettilo online (hosting gratuito)

Funziona su qualsiasi hosting per bot che supporti Python 3.10 o superiore. Di solito i passaggi sono questi:

1. Crea un server di tipo **Python** (o "Discord bot Python").
2. Carica i file del repo dal file manager, oppure collega il repo GitHub se l'hosting lo permette.
   Non serve caricare le cartelle `tests/` e `.venv/`.
3. Carica il file `.env` con i tuoi valori. In alternativa, se il pannello ha una sezione "Variabili",
   inserisci lì gli stessi valori.
4. Come file di avvio imposta `main.py`. Le dipendenze si trovano in `requirements.txt`
   e quasi tutti i pannelli le installano da soli.
5. Premi **Start**. Nella console dovresti vedere `Online come Remix SMP#...`.

## 4. Primo utilizzo

1. In un canale, ad esempio `#supporto`, scrivi `/ticket-panel`.
2. Prova `/status`.
3. Se vuoi limitare chi usa i comandi, vai su *Impostazioni server → Integrazioni → Remix SMP*.

## Sviluppo

```
uv run pytest -q
uv run python main.py
```
