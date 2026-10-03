# ☁️ SoundCloud Telegram Music Bot

A high-performance, modular Telegram Music Bot built with **Python**, **Pyrogram**, and **PyTgCalls**, specifically optimized for streaming music directly from **SoundCloud**.

Featuring an **awesome dynamic thumbnail card generator**, **interactive inline player controls**, **smart multi-chat queuing**, **loop modes**, and **service status messages**.

---

## ✨ Features

- ☁️ **SoundCloud Native Streaming**:
  - Stream any track, remix, DJ set, or indie release directly by name or URL.
  - Automatically fetches the highest quality 320kbps audio.
- 🎨 **Awesome ("OSM") Dynamic Thumbnails**:
  - Generates custom HD album cards on the fly using Pillow (`PIL`).
  - Features blurred backdrop, glowing borders, track progress indicators, badges, and metadata.
- 🎛️ **Full Interactive Callbacks**:
  - **Player Buttons**: ⏸ Pause, ▶️ Resume, ⏭ Skip, ⏹ Stop, 🔁 Loop, 📜 Queue, 🎚 Volume, 🔇 Mute / 🔊 Unmute, 🗑 Close.
  - **Volume Slider**: Quick presets (50%, 100%, 150%) and granular `-10%` / `+10%` adjustments.
  - **Queue Browser**: Interactive pagination through upcoming songs with a one-tap "Clear Queue" option.
  - **Interactive Help Center**: Categorized interactive menus for users and administrators.
- 💬 **Service & Status Messages**:
  - Auto-updating search and connecting notifications.
  - "Now Playing" and "Added to Queue" cards with durations, requester mentions, and hyperlinks.
- 🛡️ **Group Admin & Sudo Protection**:
  - Voice chat commands restricted to group admins and sudo operators (with permission bypass for the original track requester).
- 🧩 **Modular Plugin Architecture**:
  - Clean separation of core voice clients, plugins, utilities, and formatters.

---

## 📂 Project Structure

```
SoundCloudMusicBot/
├── config.py              # Configuration & Environment loader
├── main.py                # Main entry point (Bot + Assistant + PyTgCalls)
├── generate_session.py    # Helper to generate Assistant SESSION_STRING
├── requirements.txt       # Python dependencies
├── sample.env             # Environment template
├── README.md              # Documentation
├── core/
│   ├── bot.py             # Pyrogram Bot client
│   ├── assistant.py       # Assistant userbot client (for VC streaming)
│   └── call.py            # PyTgCalls voice stream manager
├── plugins/
│   ├── start.py           # /start, /ping, /help & interactive help callbacks
│   ├── play.py            # /play, /sc commands, SoundCloud scraper, queueing
│   ├── search.py          # /search interactive top-5 SoundCloud track picker
│   ├── song.py            # /song 320kbps MP3 downloader directly to Telegram
│   ├── lyrics.py          # /lyrics real-time song lyrics with auto-track detection
│   ├── playlist.py        # /playlist, /addplaylist personal cloud playlist manager
│   ├── history.py         # /history recently played tracks with 1-tap replay
│   ├── tts.py             # /tts text-to-speech announcer directly into voice chat
│   ├── shuffle.py         # /shuffle queue randomizer
│   ├── seek.py            # /seek fast-forward and stream jump
│   ├── speed.py           # /speed, /nightcore, /slowed rate presets
│   ├── radio.py           # /radio 24/7 live streams (Lofi, Synthwave, EDM, Rock)
│   ├── trending.py        # /trending SoundCloud top charts with direct play
│   ├── auth.py            # /auth, /unauth user permission delegation
│   ├── assistant.py       # /userbotjoin, /userbotleave assistant manager
│   ├── favorites.py       # /fav, /like, /favorites user liked songs collection
│   ├── filters.py         # /equalizer, /bassboost DSP audio frequency filters
│   ├── inline_mode.py     # Telegram inline search (@bot query) for any chat
│   ├── blacklist.py       # /blacklistchat, /blockuser abuse moderation
│   ├── activevc.py        # /activevc global live voice chats monitor & kill
│   ├── autoleave.py       # Auto-disconnects idle voice chats after 5 mins
│   ├── sleeptimer.py      # /sleeptimer auto-stop timer (15m, 30m, 60m)
│   ├── djmode.py          # /djmode restrict queue control to DJs/admins
│   ├── voteskip.py        # /voteskip democratic community skip voting
│   ├── genres.py          # /genres SoundCloud vibe explorer (Phonk, Deep House, etc.)
│   ├── playmode.py        # /playmode toggle direct play & artwork visuals
│   ├── maintenance.py     # /maintenance global upgrade maintenance mode
│   ├── speedtest.py       # /speedtest server network bandwidth benchmark
│   ├── channel_play.py    # /cplay stream to linked Telegram Channels
│   ├── export_queue.py    # /exportqueue export queue as .M3U playlist
│   ├── anti_flood.py      # Anti-flood command cooldown rate limiter
│   ├── shazam.py          # /shazam audio match from Telegram voice/audio
│   ├── record.py          # /vcrecord record live voice chat audio snippet
│   ├── controls.py        # Player callbacks (pause, resume, skip, stop, loop, vol, queue)
│   ├── admin.py           # Admin text commands (/pause, /resume, /skip, /stop, etc.)
│   ├── info.py            # /trackinfo and /id inspector
│   ├── clean.py           # /clean group message purger
│   ├── reboot.py          # /reboot bot process manager
│   ├── eval.py            # /eval, /sh owner debugging console
│   └── sudo.py            # Bot maintenance (/stats, /broadcast)
└── utils/
    ├── soundcloud.py      # yt-dlp powered SoundCloud metadata & audio scraper
    ├── thumbnail.py       # Dynamic HD music card generator (Pillow)
    ├── queue.py           # Per-chat queue & playback state manager
    ├── inline.py          # Interactive inline keyboard layouts
    ├── decorators.py     # Admin permission checks & callback error handling
    └── formatters.py      # Time formatting, progress bar, byte calculators
```

---

## 🛠️ Requirements & Setup

### 1. System Requirements
- **Python 3.9+**
- **FFmpeg** installed on the server:
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```

### 2. Installation

1. **Clone or navigate to the directory**:
   ```bash
   cd SoundCloudMusicBot
   ```

2. **Create a Python virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configuration

1. Copy `sample.env` to `.env`:
   ```bash
   cp sample.env .env
   ```
2. Edit `.env` with your credentials:
   - `API_ID` & `API_HASH`: Get from [my.telegram.org](https://my.telegram.org).
   - `BOT_TOKEN`: Create a bot via [@BotFather](https://t.me/BotFather).
   - `OWNER_ID`: Your Telegram numeric User ID (from [@userinfobot](https://t.me/userinfobot)).
   - `SESSION_STRING`: Assistant account string session (needed for PyTgCalls to stream in voice chats).

3. **Generate Assistant `SESSION_STRING`**:
   Run the interactive script:
   ```bash
   python3 generate_session.py
   ```
   Log in with the phone number for your assistant Telegram account, copy the output string, and paste it into `.env`.

---

## 🚀 Running the Bot

Start the bot with:
```bash
python3 main.py
```

To run continuously in the background on a server:
```bash
nohup python3 main.py > bot.log 2>&1 &
```
*(or use systemd / Docker / screen)*.

---

## 📖 Command Reference

| Command | Permission | Description |
| :--- | :--- | :--- |
| `/play <query or link>` | Everyone | Search SoundCloud or stream a direct track link |
| `/sc <query>` | Everyone | Shortcut for SoundCloud playback |
| `/search <query>` | Everyone | Interactive top-5 SoundCloud search with numbered button picker |
| `/song <query or link>` | Everyone | Download 320kbps MP3 audio file directly to Telegram |
| `/lyrics [song]` | Everyone | Real-time song lyrics (auto-detects current playing track) |
| `/playlist` | Everyone | View, play, or clear your saved SoundCloud tracks |
| `/addplaylist <track>` | Everyone | Save a track to your personal cloud playlist |
| `/delplaylist <num>` | Everyone | Remove a track from your playlist |
| `/history` or `/recent` | Everyone | View recently streamed tracks with 1-click replay buttons |
| `/tts <text>` | Everyone | Text-To-Speech: speak text directly into group voice chat |
| `/trackinfo` or `/now` | Everyone | Detailed bitrate, volume, and playback metadata |
| `/queue` | Everyone | View upcoming songs in the queue |
| `/ping` | Everyone | Check bot latency, CPU, RAM, and uptime |
| `/help` | Everyone | Open the interactive help center |
| `/pause` | Admin / Sudo | Pause the ongoing audio stream |
| `/resume` | Admin / Sudo | Resume paused audio |
| `/skip` | Admin / Sudo | Skip to next track in queue |
| `/stop` / `/end` | Admin / Sudo | Stop streaming, clear queue, and leave voice chat |
| `/loop [track/queue/off]` | Admin / Sudo | Toggle loop mode for track or entire queue |
| `/volume <1-200>` | Admin / Sudo | Set voice chat output volume |
| `/mute` | Admin / Sudo | Mute assistant in voice chat |
| `/unmute` | Admin / Sudo | Unmute assistant in voice chat |
| `/clean [count]` | Admin / Sudo | Purge recent bot messages to keep chat tidy |
| `/clearqueue` | Admin / Sudo | Clear pending queue without stopping current song |
| `/stats` | Sudo Only | View bot system load, memory, active VCs |
| `/broadcast` | Sudo Only | Broadcast replied message across chats |

---

## 🎛️ Inline Player Controls

When a track begins playing, the bot sends an HD album card with interactive buttons:
- ⏸ **Pause / ▶️ Resume**: Instantly toggle playback.
- ⏭ **Skip**: Move to the next queued SoundCloud track.
- ⏹ **Stop**: Terminate playback and disconnect the assistant.
- 🔁 **Loop**: Cycle through `Loop: Off` ➔ `Track Loop` ➔ `Queue Loop`.
- 📜 **Queue**: View paginated queue list with page navigation buttons.
- 🎚 **Volume**: Opens interactive volume controls (`-10%`, `+10%`, `50%`, `100%`, `150%`).
- 🔇 **Mute / 🔊 Unmute**: Mute or unmute stream output.
- ☁️ **SoundCloud Link**: One-click link to listen on SoundCloud website.
- 🗑 **Close**: Dismiss player message.
