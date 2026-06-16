import os, asyncio, math, time, tempfile, uuid, re, subprocess, shutil
import gradio as gr
from dotenv import load_dotenv
from openai import AsyncOpenAI

# -------- .env --------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

# -------- Config --------
TEXT_MODEL = "gpt-4o-mini"
TTS_MODEL  = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
AUDIO_FMT  = "mp3"

TARGET_MINUTES = 10
SPEAKING_WPM   = 155
TOTAL_WORDS    = TARGET_MINUTES * SPEAKING_WPM
N_SECTIONS     = 10
WORDS_PER_SECTION  = math.ceil(TOTAL_WORDS / N_SECTIONS)

# TTS parallelization
CHARS_PER_CHUNK = 1200
MAX_CONCURRENCY = 6
TTS_TIMEOUT_SEC = 120
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

# --- NEW: background music config ---
BG_FILE = "background1.mp3"  # must exist in the same folder

DEFAULT_TOPIC = (
    "Guide a beginner through a calm mindfulness session focused on breath, "
    "body awareness, gentle visualization, and a positive closing. "
    "Style: warm, concrete, encouraging; short paragraphs; no timestamps, no SSML; "
    "avoid bullet points; keep it natural to read aloud."
)

OUTLINE = [
    "Opening welcome & set intention",
    "Posture & environment setup",
    "Initial breath awareness",
    "Counting the breath (light focus)",
    "Body scan (head to toes)",
    "Handling distractions kindly",
    "Gentle visualization (safe place)",
    "Gratitude micro-reflection",
    "Preparing to close (re-orient body)",
    "Closing message & next-steps",
]

SYSTEM = (
    "You are a skilled meditation scriptwriter. "
    "Write natural, human-sounding narration for voice-over. "
    "No timestamps, no SSML, no stage directions. "
    "Use short paragraphs and smooth transitions."
)

SECTION_PROMPT = """Topic: {topic}
Section: {heading}

Write this section as continuous narration, ~{words} words.
Keep tone consistent and do not repeat exact phrases from other sections.
Output ONLY narration text.
"""

client = AsyncOpenAI(api_key=API_KEY)

# -------- Text generation (parallel) --------
async def gen_section(idx: int, topic: str, heading: str):
    prompt = SECTION_PROMPT.format(topic=topic, heading=heading, words=WORDS_PER_SECTION)
    rsp = await client.chat.completions.create(
        model=TEXT_MODEL, temperature=0.7,
        messages=[{"role":"system","content":SYSTEM},
                  {"role":"user","content":prompt}],
    )
    return idx, rsp.choices[0].message.content.strip()

async def generate_script(topic: str) -> str:
    tasks = [gen_section(i, topic, OUTLINE[i]) for i in range(N_SECTIONS)]
    results = await asyncio.gather(*tasks)
    results.sort(key=lambda x: x[0])
    return "\n\n".join([s for _, s in results])

# -------- Helpers: chunking & ffmpeg concat/mix --------
_SENT_SPLIT = re.compile(r'(?<=[\.\!\?])\s+')

def sentence_chunks(text: str, max_chars: int = CHARS_PER_CHUNK):
    sents = _SENT_SPLIT.split(text.strip())
    buf, total = [], 0
    for s in sents:
        if not s: 
            continue
        if total + len(s) + 1 > max_chars and buf:
            yield " ".join(buf).strip()
            buf, total = [s], len(s)
        else:
            buf.append(s); total += len(s) + 1
    if buf:
        yield " ".join(buf).strip()

def concat_segments_ffmpeg(paths, out_path):
    if len(paths) == 1:
        shutil.copyfile(paths[0], out_path)
        return out_path
    lst = os.path.join(tempfile.gettempdir(), f"concat_{uuid.uuid4().hex}.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{p}'\n")
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", lst,
        "-c", "copy", out_path
    ]
    subprocess.check_call(cmd)
    os.remove(lst)
    return out_path

# --- NEW: background mixing helper ---
def mix_with_bgm(voice_path: str, bg_path: str, out_path: str, bg_volume: float = 0.15):
    if not shutil.which(FFMPEG):
        raise RuntimeError("ffmpeg not found on PATH")

    if not os.path.isfile(bg_path):
        raise FileNotFoundError(f"Background file not found: {bg_path}")

    # -stream_loop -1 repeats bg as needed; duration=first trims to voice length
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", voice_path,
        "-stream_loop", "-1", "-i", bg_path,
        "-filter_complex", f"[1:a]volume={bg_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=0",
        "-c:a", "mp3", "-b:a", "128k", "-ar", "44100",
        "-shortest",
        out_path,
    ]
    subprocess.check_call(cmd)
    return out_path

# -------- TTS: parallel segments --------
async def tts_one_chunk(text: str, voice: str, fmt: str, sem: asyncio.Semaphore) -> str:
    out_path = os.path.join(tempfile.gettempdir(), f"seg_{uuid.uuid4().hex}.{fmt}")
    async with sem:
        try:
            async with client.audio.speech.with_streaming_response.create(
                model=TTS_MODEL, voice=voice, input=text, response_format=fmt
            ) as resp:
                await asyncio.wait_for(resp.stream_to_file(out_path), timeout=TTS_TIMEOUT_SEC)
        except Exception:
            resp = await asyncio.wait_for(
                client.audio.speech.create(model=TTS_MODEL, voice=voice, input=text, response_format=fmt),
                timeout=TTS_TIMEOUT_SEC
            )
            data = await resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise RuntimeError("Empty TTS segment.")
    return out_path

# -------- Gradio: progressive updates + final stitched/mixed MP3 --------
async def on_generate_streaming(topic_brief: str, voice_choice: str, bg_vol: float):
    """
    Generator yields tuples:
      (script_text, stats, dry_audio_path, mixed_audio_path)
    During segment generation, mixed_audio_path will be None.
    At the end, both dry and mixed are provided.
    """
    topic = (topic_brief or "").strip() or DEFAULT_TOPIC
    voice = (voice_choice or DEFAULT_VOICE)

    # Generate script
    t0 = time.perf_counter()
    script = await generate_script(topic)
    t_gen = time.perf_counter() - t0

    words = len(script.split())
    est_mins = words / SPEAKING_WPM

    # TTS segments in parallel with progressive yields
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    chunk_texts = list(sentence_chunks(script, CHARS_PER_CHUNK))
    tasks = [tts_one_chunk(txt, voice, AUDIO_FMT, sem) for txt in chunk_texts]

    seg_paths = []
    t1 = time.perf_counter()
    for fut in asyncio.as_completed(tasks):
        p = await fut
        seg_paths.append(p)
        stats_now = f"Words: {words} | Est: {est_mins:.1f} min | Script: {t_gen:.2f}s | Segments ready: {len(seg_paths)}/{len(chunk_texts)}"
        # No mix yet; stream latest dry segment so user can preview
        yield script, stats_now, p, None

    tts_time = time.perf_counter() - t1

    # Concatenate dry
    final_dry = os.path.join(tempfile.gettempdir(), f"speech_{uuid.uuid4().hex}.{AUDIO_FMT}")
    concat_segments_ffmpeg(seg_paths, final_dry)

    # Mix with background
    final_mix = os.path.join(tempfile.gettempdir(), f"speech_mix_{uuid.uuid4().hex}.{AUDIO_FMT}")
    try:
        mix_with_bgm(final_dry, BG_FILE, final_mix, bg_volume=float(bg_vol))
        mix_note = " | Mixed with background."
    except Exception as e:
        final_mix = None
        mix_note = f" | ⚠️ Mix failed: {e}"

    stats_final = f"Words: {words} | Est: {est_mins:.1f} min | Script: {t_gen:.2f}s | TTS(stitch): {tts_time:.2f}s{mix_note}"
    yield script, stats_final, final_dry, final_mix

# -------- UI --------
VOICES = ["alloy","ash","ballad","coral","echo","fable","onyx","nova","sage","shimmer","verse"]

with gr.Blocks(title="10-Minute Script → Fast MP3") as demo:
    gr.Markdown("# 10‑Minute Script ➜ Fast, Parallel TTS (with Background Mix)")
    with gr.Row():
        topic_in = gr.Textbox(label="Topic / Instructions", value=DEFAULT_TOPIC, lines=6)
        voice_in = gr.Dropdown(choices=VOICES, value=DEFAULT_VOICE, label="Voice")
        bg_vol_in = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=0.15, label="Background Volume")
    btn = gr.Button("Generate Script + Audio", variant="primary")

    script_out = gr.Textbox(label="Script", lines=22)
    meta_out = gr.Textbox(label="Stats (timings)", interactive=False)
    dry_out = gr.Audio(label="Voice (Dry)", type="filepath")
    mix_out = gr.Audio(label="Final Mix (with background)", type="filepath")

    # IMPORTANT: generator must return 4 outputs consistently
    btn.click(on_generate_streaming, inputs=[topic_in, voice_in, bg_vol_in],
              outputs=[script_out, meta_out, dry_out, mix_out])

if __name__ == "__main__":
    demo.launch()
