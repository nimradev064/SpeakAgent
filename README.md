# 🎙️ SpeakAgent

> An AI-powered speak agent that generates full narration scripts and converts them to speech with optional background music mixing — all through a simple web UI.

---

## ✨ Features

- **AI Script Generation** — Produces a structured 10-section narration (~1,550 words) using GPT-4o-mini
- **Parallel TTS Processing** — Converts text to speech in up to 6 concurrent chunks for maximum speed
- **Background Music Mixing** — Blends voice audio with a background track via FFmpeg
- **Progressive Streaming UI** — Preview audio segments as they're generated, before the final mix is ready
- **11 Voice Options** — Choose from: `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`, `verse`
- **Dual Audio Output** — Downloads both a clean dry voice file and a fully mixed final version

---

## 🗂️ Project Structure

```
voiceagent/
├── script.py          # Main application (script generation + TTS + Gradio UI)
├── requirements.txt   # Python dependencies
├── background1.mp3    # Background music file (must be provided by user)
└── .env               # API key configuration (create this yourself)
```

---

## ⚙️ Prerequisites

Before running the project, make sure you have:

- **Python 3.9+**
- **FFmpeg** installed and available on your system PATH → [Download FFmpeg](https://ffmpeg.org/download.html)
- An **OpenAI API key** → [Get one here](https://platform.openai.com/api-keys)
- A background music file named `background1.mp3` placed in the project root

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nimradev064/SpeakAgent.git
cd voiceagent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Add Background Music

Place your background music file in the project root:

```
background1.mp3
```

> Any royalty-free MP3 will work. The file will be looped automatically to match the audio length.

### 5. Run the App

```bash
python script.py
```

Open the Gradio web UI in your browser at: **`http://localhost:7860`**

---

## 🖥️ How to Use

1. **Enter a topic** in the text box (or keep the default mindfulness session)
2. **Select a voice** from the dropdown
3. **Adjust background volume** using the slider (`0.0` = silent, `1.0` = full volume, default `0.15`)
4. Click **"Generate Script + Audio"**
5. Watch the script populate and audio segments stream in progressively
6. Download the **dry voice** or **final mixed audio** when complete

---

## 🔧 Configuration

Key settings can be adjusted at the top of `script.py`:

| Variable | Default | Description |
|---|---|---|
| `TEXT_MODEL` | `gpt-4o-mini` | OpenAI model for script generation |
| `TTS_MODEL` | `gpt-4o-mini-tts` | OpenAI TTS model |
| `TARGET_MINUTES` | `10` | Target audio duration in minutes |
| `SPEAKING_WPM` | `155` | Estimated speaking speed (words per minute) |
| `N_SECTIONS` | `10` | Number of script sections to generate |
| `MAX_CONCURRENCY` | `6` | Max parallel TTS requests |
| `CHARS_PER_CHUNK` | `1200` | Characters per TTS chunk |
| `DEFAULT_VOICE` | `alloy` | Default TTS voice |
| `BG_FILE` | `background1.mp3` | Background music filename |

---

## 🧠 How It Works

```
User Input (Topic)
       │
       ▼
GPT-4o-mini generates 10 script sections (in parallel)
       │
       ▼
Script is split into ~1200-character sentence chunks
       │
       ▼
OpenAI TTS converts each chunk to MP3 (up to 6 in parallel)
       │
       ▼
FFmpeg concatenates all segments into one audio file (dry)
       │
       ▼
FFmpeg mixes dry voice with background1.mp3 → Final Mix
       │
       ▼
Gradio UI streams preview segments + serves final downloads
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `openai` | GPT-4o text generation & TTS API |
| `gradio` | Web-based UI |
| `python-dotenv` | Load API key from `.env` |
| `ffmpeg` *(system)* | Audio concatenation and background mixing |

Install Python packages:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Notes & Troubleshooting

- **FFmpeg not found** — The app will still generate dry voice audio, but background mixing will be skipped. Install FFmpeg and ensure it's on your PATH.
- **Missing `background1.mp3`** — Same as above; the mix step will be skipped with a warning shown in the UI stats.
- **API costs** — Parallel TTS with 6 concurrent requests is fast but will consume more OpenAI tokens simultaneously. Monitor your usage at [platform.openai.com](https://platform.openai.com/usage).
- **Long generation times** — Script generation and TTS together typically take 30–90 seconds depending on topic complexity and API latency.

---

## 🎯 Default Demo Topic

The app ships with a guided **mindfulness meditation** session as its default topic:

> *"Guide a beginner through a calm mindfulness session focused on breath, body awareness, gentle visualization, and a positive closing."*

You can replace this with any topic — podcast script, educational content, bedtime story, training material, and more.

---

## 📄 License

This project is open source. Contributions and forks are welcome.

---
