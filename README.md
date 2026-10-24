# Remix SMP Bot

Tutti i testi che vedono gli utenti su Discord sono in inglese; le scritte nella console restano in italiano.

Bot Discord per il server Minecraft **Remix SMP**, scritto in Python con `discord.py`.

| Comando | Chi lo vede | Cosa fa |
|---|---|---|
| `/status` | tutti | Mostra se il server è online, i giocatori, l'IP, la versione e il ping |
| `/kick`, `/ban` | chi può espellere o bannare | Espelle o banna un utente, con motivo facoltativo |
| `/timeout`, `/untimeout` | chi può silenziare | Silenzia un utente per N minuti, o toglie il timeout |
| `/clear` | chi può gestire i messaggi | Cancella gli ultimi 1–100 messaggi del canale |
| `/ticket-panel` | admin | Pubblica il pannello ticket con tre bottoni: 🛠️ Support, 🚨 Report a player, 🐛 Bug. Ogni bottone apre un modulo obbligatorio (nick, Java/Bedrock, domande) prima di creare il ticket |
| `/words add`, `/words remove`, `/words list` | chi può gestire il server | Filtro parole: i messaggi con parole vietate vengono cancellati e l'autore va in timeout (`FILTER_TIMEOUT_MINUTES`, predefinito 5). Lo staff con "Gestisci messaggi" non viene filtrato. Serve **Message Content Intent** attivo nel Developer Portal |
| `/dashboard-setup` | admin | Crea `📢・dashboard`, canale privato per proprietario e manager, con il pannello per far mandare al bot messaggi personalizzati in qualsiasi canale |

Lo stato del bot ("12/50 online on Remix SMP") si aggiorna da solo ogni 2 minuti.

Tutti i messaggi hanno la grafica del Remix SMP: logo, colori del brand e piè di pagina `Remix SMP • remixsmp.net`
(immagini in `assets/`, colori in `bot/brand.py`). I messaggi di moderazione mostrano la foto profilo dell'utente
e l'utente viene avvisato in privato. Nei ticket lo staff può premere **Claim**.
Al primo avvio il bot si imposta da solo il logo come foto profilo.

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

Server, IP, ruoli staff e "Apertura a breve" hanno già i valori del Remix SMP in `bot/config.py` (`DEFAULTS`):
sull'hosting basta impostare `DISCORD_TOKEN`. Le variabili qui sotto servono solo per sostituire quei valori.

Copia `.env.example` in un file chiamato `.env` e compila i campi:

- `DISCORD_TOKEN`: il token del bot (obbligatorio)
- `GUILD_ID`: l'ID del tuo server Discord, così i comandi compaiono subito
- `MC_ADDRESS`: l'IP del server Minecraft, ad esempio `play.remixsmp.it` o `1.2.3.4:25565`
- `STAFF_ROLE_ID`: i ruoli staff separati da virgola (es. `111,222,333`); vedono tutti i ticket e ricevono una menzione quando ne viene aperto uno
- `TICKET_CATEGORY_ID`: la categoria in cui creare i canali ticket (facoltativo)
- `TICKET_CATEGORY_NAME`: se non c'è l'ID, i ticket vanno nella prima categoria che contiene questa parola.
  Senza ID né nome, i ticket vanno nella stessa categoria del canale in cui c'è il pannello
- `MANAGER_ROLE_ID`: i ruoli che possono usare la dashboard dei messaggi, separati da virgola (il proprietario e gli amministratori possono sempre)
- `COMING_SOON`: metti `1` finché il server non è aperto. Il bot mostra "🚀 Opening soon!" invece di "offline". Il giorno del lancio cancellala.

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
