# 🎵 MaxMusic V2

A next-generation, high-performance Telegram Voice Chat & Video Streaming Bot built with modern Python, **Kurigram**, **PyTgCalls**, **MongoDB**, and **yt-dlp**.

---

## ✨ Features & Architecture Upgrades

- **40+ Modular Plugins**: Clean separation of playback, controls, queue, channel play, administrative tools, and sudo capabilities.
- **📡 Channel Play (`/channelplay` & `/cplay`)**: Link any public or private Telegram channel to your group and stream music/video directly into the channel's voice chat!
- **🎛 Full Interactive Callbacks**: Complete playback control via inline buttons (Play/Pause, Skip, Stop, Seek, Loop, Shuffle, Volume slider, Speed multiplier, Autoplay toggle, and Paginated Queue).
- **🔁 Advanced Loop & Autoplay**: Single-track repeat, full queue repeat, and continuous smart YouTube autoplay that finds and queues related tracks when the playlist ends.
- **⚡ Dual Client & Multi-Assistant**: Automatic load balancing across up to 3 Telegram user accounts (`SESSION1`, `SESSION2`, `SESSION3`).
- **🎨 Modern HD Thumbnail Generator**: 1280x720 dynamic Now-Playing cards rendered asynchronously using Pillow with gradient glow, sleek typography, and progress indicators.
- **🧹 Auto-Cleaning & Cache Optimization**: Automatic purging of downloaded streams and cached files to prevent filling up disk space.

---

## 📋 Requirements

The project uses the following dependencies:
```txt
aiofiles~=25.1.0
aiohttp~=3.13.3
kurigram>=2.2.17
pillow~=12.1.0
psutil~=7.2.1
pymongo>=4.16.0
pytgcrypto>=1.2.11
py-tgcalls~=2.2.10
py_yt
py-yt-search~=0.5.7
python-dotenv~=1.2.1
speedtest-cli
yt-dlp[default]>=2026.3.13
```

---

## 🚀 Quick Setup & Deployment

### 1. Configure Environment
Copy `sample.env` to `.env` and fill in your credentials:
```bash
cp sample.env .env
nano .env
```

Required variables:
- `API_ID` & `API_HASH`: From [my.telegram.org](https://my.telegram.org)
- `BOT_TOKEN`: From [@BotFather](https://t.me/BotFather)
- `OWNER_ID`: Your Telegram numeric User ID
- `LOGGER_ID`: Numeric ID of your private logger group (bot must be admin)
- `MONGO_URL`: MongoDB Atlas connection URI
- `SESSION1`: Pyrogram/Kurigram v2 string session from [@StringFatherBot](https://t.me/StringFatherBot)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Bot
```bash
bash start.sh
# or
python3 -m maxmusic
```

### 🐳 Docker Deployment
```bash
docker build -t maxmusic-v2 .
docker run -d --name maxmusic --env-file .env maxmusic-v2
```

---

## 📖 Command Reference

### 🎵 Playback
| Command | Description |
| :--- | :--- |
| `/play [song/url]` | Stream audio in group VC |
| `/vplay [video/url]` | Stream 720p HD video in group VC |
| `/playforce [song]` | Force play track immediately |
| `/vplayforce [video]` | Force play video immediately |
| `/pause` | Pause stream |
| `/resume` | Resume playback |
| `/skip` or `/next` | Skip to next track in queue |
| `/stop` or `/end` | Stop stream and clear queue |
| `/seek [sec]` | Seek forward |
| `/seekback [sec]` | Rewind playback |
| `/loop [0/1/2]` | 0: Off, 1: Track, 2: Queue |
| `/shuffle` | Shuffle queue |
| `/queue` or `/q` | View interactive paginated queue |
| `/volume [1-200]` | Adjust voice chat volume |
| `/speed` | Adjust playback speed |
| `/autoplay [on/off]` | Toggle smart autoplay |

### 📡 Channel Play
| Command | Description |
| :--- | :--- |
| `/channelplay [id]` | Link group to a channel |
| `/cplay [song]` | Stream audio in linked channel VC |
| `/cvplay [video]` | Stream video in linked channel VC |
| `/cstop` | Stop channel stream |
| `/cskip` | Skip channel track |
| `/cpause` / `/cresume`| Pause / Resume channel stream |
| `/channelplay disable`| Unlink channel |

### 👑 Admin & DJ
| Command | Description |
| :--- | :--- |
| `/auth @user` | Authorize non-admin DJ |
| `/unauth @user` | Revoke DJ role |
| `/authusers` | List authorized DJs |
| `/settings` | Open interactive chat settings |
| `/cleanmode [on/off]` | Auto-delete command triggers |
| `/reload` | Refresh admin permissions cache |
| `/thumb` | Set custom Now Playing thumbnail |

### ⚡ Sudoers
| Command | Description |
| :--- | :--- |
| `/activevc` | List active voice chats |
| `/activevideo` | List active video streams |
| `/broadcast [text]` | Broadcast message across all chats |
| `/stats` | View CPU, RAM, disk and bot statistics |
| `/speedtest` | Test server internet connection |
| `/blacklistchat` | Block chat from bot |
| `/blacklistuser` | Block user from bot |
| `/gban @user` | Global ban user across all groups |
| `/maintenance` | Toggle maintenance mode |
| `/restart` | Restart bot process |
| `/update` | Pull latest Git updates |
