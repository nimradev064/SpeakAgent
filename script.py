# # # # # # # # # import os
# # # # # # # # # import subprocess
# # # # # # # # # from dotenv import load_dotenv
# # # # # # # # # from openai import OpenAI

# # # # # # # # # # 1) Load API key
# # # # # # # # # load_dotenv()
# # # # # # # # # api_key = os.getenv("OPENAI_API_KEY")
# # # # # # # # # if not api_key:
# # # # # # # # #     raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# # # # # # # # # client = OpenAI(api_key=api_key)

# # # # # # # # # # 2) Text + instructions (same as your code)
# # # # # # # # # input_text = """Hello, and welcome to your moment of mindfulness. I'm so glad you're here. Let's begin by closing your eyes and taking a deep, calming breath. Breathe in slowly through your nose, and exhale softly, releasing any tension.

# # # # # # # # # Imagine your thoughts as soft clouds drifting across the sky—observe them without attachment, letting your mind become clear and peaceful."""
# # # # # # # # # instructions_text = """Voice Affect: Soft, gentle, soothing; embody tranquility.

# # # # # # # # # Tone: Calm, reassuring, peaceful; convey genuine warmth and serenity.

# # # # # # # # # Pacing: Slow, deliberate, and unhurried; pause gently after instructions to allow the listener time to relax and follow along.

# # # # # # # # # Emotion: Deeply soothing and comforting; express genuine kindness and care.

# # # # # # # # # Pronunciation: Smooth, soft articulation, slightly elongating vowels to create a sense of ease.

# # # # # # # # # Pauses: Use thoughtful pauses, especially between breathing instructions and visualization guidance, enhancing relaxation and mindfulness."""

# # # # # # # # # # 3) Generate TTS MP3
# # # # # # # # # voice_mp3 = "voice.mp3"
# # # # # # # # # with client.audio.speech.with_streaming_response.create(
# # # # # # # # #     model="gpt-4o-mini-tts",
# # # # # # # # #     voice="sage",
# # # # # # # # #     input=input_text,
# # # # # # # # #     instructions=instructions_text,
# # # # # # # # #     response_format="mp3",
# # # # # # # # # ) as response:
# # # # # # # # #     response.stream_to_file(voice_mp3)

# # # # # # # # # print("✅ Voice saved:", voice_mp3)

# # # # # # # # # # 4) Fast mix with ffmpeg
# # # # # # # # # # -stream_loop -1 repeats the background as needed
# # # # # # # # # # [1:a]volume=0.15 lowers bg music ~ -16 dB
# # # # # # # # # # amix with duration=first trims output to vocal length (input 0)
# # # # # # # # # # -shortest ensures it stops at the shorter (the voice)
# # # # # # # # # bg_mp3 = "background1.mp3"
# # # # # # # # # out_mp3 = "mindfulness_with_music.mp3"

# # # # # # # # # cmd = [
# # # # # # # # #     "ffmpeg",
# # # # # # # # #     "-y",
# # # # # # # # #     "-i", voice_mp3,             # [0:a] voice
# # # # # # # # #     "-stream_loop", "-1",
# # # # # # # # #     "-i", bg_mp3,                # [1:a] background
# # # # # # # # #     "-filter_complex",
# # # # # # # # #     "[1:a]volume=0.15[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=0",
# # # # # # # # #     "-c:a", "mp3",
# # # # # # # # #     "-b:a", "128k",
# # # # # # # # #     "-ar", "44100",
# # # # # # # # #     "-shortest",
# # # # # # # # #     out_mp3,
# # # # # # # # # ]

# # # # # # # # # # Run ffmpeg and raise an error if it fails
# # # # # # # # # subprocess.run(cmd, check=True)
# # # # # # # # # print("🎶 Final mix saved:", out_mp3)


# # # # # # # # # Gradio App

# # # # # # # # import os
# # # # # # # # import tempfile
# # # # # # # # import subprocess
# # # # # # # # from dotenv import load_dotenv
# # # # # # # # from openai import OpenAI
# # # # # # # # import gradio as gr

# # # # # # # # # ----------------------------
# # # # # # # # # Setup
# # # # # # # # # ----------------------------
# # # # # # # # load_dotenv()
# # # # # # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # # # # if not API_KEY:
# # # # # # # #     raise ValueError("❌ OPENAI_API_KEY not found in .env file.")
# # # # # # # # client = OpenAI(api_key=API_KEY)

# # # # # # # # # Background settings
# # # # # # # # BG_FILE = "background1.mp3"   # must exist in same folder
# # # # # # # # TTS_MODEL = "gpt-4o-mini-tts"
# # # # # # # # TTS_VOICE = "sage"

# # # # # # # # # Optional default text
# # # # # # # # DEFAULT_TEXT = (
# # # # # # # #     "Hello, and welcome to your moment of mindfulness. "
# # # # # # # #     "Let's begin by closing your eyes and taking a deep, calming breath. "
# # # # # # # #     "Breathe in slowly through your nose, and exhale softly, releasing any tension.\n\n"
# # # # # # # #     "Imagine your thoughts as soft clouds drifting across the sky—observe them "
# # # # # # # #     "without attachment, letting your mind become clear and peaceful."
# # # # # # # # )

# # # # # # # # # ----------------------------
# # # # # # # # # Core: TTS + auto-mix
# # # # # # # # # ----------------------------
# # # # # # # # def generate_and_mix(user_text: str, bg_volume: float):
# # # # # # # #     if not user_text.strip():
# # # # # # # #         return None, None, "⚠️ Please enter text to speak.", None, None

# # # # # # # #     if not os.path.isfile(BG_FILE):
# # # # # # # #         return None, None, f"⚠️ Background file not found: {BG_FILE}", None, None

# # # # # # # #     tmpdir = tempfile.mkdtemp(prefix="mindful_tts_")
# # # # # # # #     voice_mp3 = os.path.join(tmpdir, "voice.mp3")
# # # # # # # #     final_mix_mp3 = os.path.join(tmpdir, "mindfulness_with_music.mp3")
# # # # # # # #     instructions_text = """Voice Affect: Soft, gentle, soothing; embody tranquility.Tone: Calm, reassuring, peaceful; convey genuine warmth and serenity.Pacing: Slow, deliberate, and unhurried; pause gently after instructions to allow the listener time to relax and follow along.
# # # # # # # #       Emotion: Deeply soothing and comforting; express genuine kindness and care.Pronunciation: Smooth, soft articulation, slightly elongating vowels to create a sense of ease.Pauses: Use thoughtful pauses, especially between breathing instructions and visualization guidance, enhancing relaxation and mindfulness."""
# # # # # # # #     # 1) Generate voice MP3
# # # # # # # #     try:
# # # # # # # #         with client.audio.speech.with_streaming_response.create(
# # # # # # # #             model=TTS_MODEL,
# # # # # # # #             voice=TTS_VOICE,
# # # # # # # #             input=user_text,
# # # # # # # #             instructions=instructions_text,
# # # # # # # #             response_format="mp3",
# # # # # # # #         ) as response:
# # # # # # # #             response.stream_to_file(voice_mp3)
# # # # # # # #     except Exception as e:
# # # # # # # #         return None, None, f"❌ TTS failed: {e}", None, None

# # # # # # # #     # 2) Auto-mix with background1.mp3
# # # # # # # #     try:
# # # # # # # #         cmd = [
# # # # # # # #             "ffmpeg",
# # # # # # # #             "-y",
# # # # # # # #             "-i", voice_mp3,             # [0:a] voice
# # # # # # # #             "-stream_loop", "-1",
# # # # # # # #             "-i", BG_FILE,               # [1:a] background
# # # # # # # #             "-filter_complex",
# # # # # # # #             f"[1:a]volume={bg_volume}[a1];"
# # # # # # # #             f"[0:a][a1]amix=inputs=2:duration=first:dropout_transition=0",
# # # # # # # #             "-c:a", "mp3",
# # # # # # # #             "-b:a", "128k",
# # # # # # # #             "-ar", "44100",
# # # # # # # #             "-shortest",
# # # # # # # #             final_mix_mp3,
# # # # # # # #         ]
# # # # # # # #         subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# # # # # # # #     except FileNotFoundError:
# # # # # # # #         return voice_mp3, None, "⚠️ ffmpeg not found. Install it and ensure it’s on your PATH.", voice_mp3, None
# # # # # # # #     except subprocess.CalledProcessError as e:
# # # # # # # #         return voice_mp3, None, f"❌ ffmpeg error:\n{e.stderr.decode('utf-8', errors='ignore')}", voice_mp3, None
# # # # # # # #     except Exception as e:
# # # # # # # #         return voice_mp3, None, f"❌ Mixing failed: {e}", voice_mp3, None

# # # # # # # #     return voice_mp3, final_mix_mp3, "🎶 Done! Voice + background mixed.", voice_mp3, final_mix_mp3

# # # # # # # # # ----------------------------
# # # # # # # # # Gradio UI
# # # # # # # # # ----------------------------
# # # # # # # # with gr.Blocks(title="Mindfulness TTS (Auto Background)") as demo:
# # # # # # # #     gr.Markdown("# Mindfulness TTS (Auto Background)")
# # # # # # # #     gr.Markdown(
# # # # # # # #         "Enter the text to speak. The app will generate speech and automatically mix "
# # # # # # # #         "it with `background1.mp3`. Adjust the background volume as needed."
# # # # # # # #     )

# # # # # # # #     user_text = gr.Textbox(
# # # # # # # #         label="Your Script",
# # # # # # # #         value=DEFAULT_TEXT,
# # # # # # # #         lines=10,
# # # # # # # #         placeholder="Type what you want the voice to say..."
# # # # # # # #     )

# # # # # # # #     bg_vol = gr.Slider(
# # # # # # # #         minimum=0.0,
# # # # # # # #         maximum=1.0,
# # # # # # # #         value=0.15,
# # # # # # # #         step=0.01,
# # # # # # # #         label="Background Volume (0.0 - 1.0)"
# # # # # # # #     )

# # # # # # # #     run_btn = gr.Button("Generate")
# # # # # # # #     status_md = gr.Markdown()

# # # # # # # #     with gr.Row():
# # # # # # # #         voice_preview = gr.Audio(label="Voice (Dry)", interactive=False)
# # # # # # # #         mix_preview = gr.Audio(label="Final Mix", interactive=False)

# # # # # # # #     with gr.Row():
# # # # # # # #         voice_dl = gr.File(label="Download Voice MP3")
# # # # # # # #         mix_dl = gr.File(label="Download Mix MP3")

# # # # # # # #     run_btn.click(
# # # # # # # #         generate_and_mix,
# # # # # # # #         inputs=[user_text, bg_vol],
# # # # # # # #         outputs=[voice_preview, mix_preview, status_md, voice_dl, mix_dl],
# # # # # # # #         api_name="run"
# # # # # # # #     )

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     demo.launch(share=True)

# # # # # # # # Voice To Text Agent 

# # # # # # # # # mindfulness_tts_plain.py  (Text ➜ Text only)
# # # # # # # # import os
# # # # # # # # import tempfile
# # # # # # # # from dotenv import load_dotenv
# # # # # # # # from openai import OpenAI
# # # # # # # # import gradio as gr

# # # # # # # # # ----------------------------
# # # # # # # # # Setup
# # # # # # # # # ----------------------------
# # # # # # # # load_dotenv()
# # # # # # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # # # # if not API_KEY:
# # # # # # # #     raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# # # # # # # # client = OpenAI(api_key=API_KEY)

# # # # # # # # # Models
# # # # # # # # TEXT_MODEL = "gpt-4o-mini"       # text generation
# # # # # # # # TTS_MODEL  = "gpt-4o-mini-tts"   # text-to-speech
# # # # # # # # TTS_VOICE  = "sage"              # ← your requested voice

# # # # # # # # DEFAULT_TEXT = (
# # # # # # # #     "Hello, and welcome to your moment of mindfulness. "
# # # # # # # #     "Close your eyes and take a slow, deep breath in... and gently exhale. "
# # # # # # # #     "With each breath, allow your body to soften and your mind to rest."
# # # # # # # # )

# # # # # # # # INSTRUCTIONS_TEXT = (
# # # # # # # #     "Voice Affect: Soft, gentle, soothing; embody tranquility. "
# # # # # # # #     "Tone: Calm, reassuring, peaceful; convey genuine warmth and serenity. "
# # # # # # # #     "Pacing: Slow and unhurried with natural pauses. "
# # # # # # # #     "Emotion: Deeply soothing and comforting. "
# # # # # # # #     "Pronunciation: Smooth, soft articulation, slightly elongated vowels. "
# # # # # # # #     "Pauses: Thoughtful pauses between instructions for relaxation. "
# # # # # # # #     "Duration: Please expand the narration naturally so the final script reads "
# # # # # # # #     "as approximately {minutes} minutes of spoken content. Do NOT include any audio or SSML."
# # # # # # # # )

# # # # # # # # # ----------------------------
# # # # # # # # # Core: Text ➜ Text
# # # # # # # # # ----------------------------
# # # # # # # # def generate_script(user_text: str, target_minutes: int):
# # # # # # # #     """
# # # # # # # #     Returns:
# # # # # # # #       - echoed_text (str)
# # # # # # # #       - generated_text (str)
# # # # # # # #       - status_md (str)
# # # # # # # #     """
# # # # # # # #     user_text = (user_text or "").strip()
# # # # # # # #     if not user_text:
# # # # # # # #         return "", "", "⚠️ Please enter text to process."

# # # # # # # #     # Approximate words at ~140 wpm for pacing
# # # # # # # #     approx_words = max(60, int(target_minutes) * 140)
# # # # # # # #     sys_prompt = (
# # # # # # # #         "You are a mindfulness scriptwriter. "
# # # # # # # #         "Rewrite or extend the user's text into a calming, guided-meditation script. "
# # # # # # # #         "Follow the style guidelines strictly. "
# # # # # # # #         "Use simple, gentle language; add natural [pause] markers sparingly; "
# # # # # # # #         "organize with short paragraphs and line breaks. "
# # # # # # # #         f"Aim for ~{approx_words} words (≈{target_minutes} minutes). "
# # # # # # # #         "Do NOT add sound effects, SSML, or instructions about audio."
# # # # # # # #     )
# # # # # # # #     style_block = INSTRUCTIONS_TEXT.format(minutes=target_minutes)

# # # # # # # #     try:
# # # # # # # #         resp = client.chat.completions.create(
# # # # # # # #             model=TEXT_MODEL,
# # # # # # # #             messages=[
# # # # # # # #                 {"role": "system", "content": sys_prompt},
# # # # # # # #                 {"role": "user", "content": f"{style_block}\n\nUser draft:\n{user_text}"},
# # # # # # # #             ],
# # # # # # # #             temperature=0.7,
# # # # # # # #         )
# # # # # # # #         out_text = resp.choices[0].message.content.strip()
# # # # # # # #         return user_text, out_text, f"✅ Script generated for ~{target_minutes} minutes (~{approx_words} words)."
# # # # # # # #     except Exception as e:
# # # # # # # #         return user_text, "", f"❌ Generation failed: {e}"

# # # # # # # # # ----------------------------
# # # # # # # # # Core: Text ➜ Voice (TTS)
# # # # # # # # # ----------------------------
# # # # # # # # def text_to_voice(script_text: str):
# # # # # # # #     """
# # # # # # # #     Takes final script text and returns:
# # # # # # # #       - audio_preview (path or None for Gradio Audio)
# # # # # # # #       - audio_file (path or None for Gradio File)
# # # # # # # #       - status_md (append/replace)
# # # # # # # #     """
# # # # # # # #     script_text = (script_text or "").strip()
# # # # # # # #     if not script_text:
# # # # # # # #         return None, None, "⚠️ No script to convert to voice."

# # # # # # # #     try:
# # # # # # # #         tmpdir = tempfile.mkdtemp(prefix="mindful_tts_")
# # # # # # # #         voice_mp3 = os.path.join(tmpdir, "voice.mp3")

# # # # # # # #         # Stream MP3 to file
# # # # # # # #         with client.audio.speech.with_streaming_response.create(
# # # # # # # #             model=TTS_MODEL,
# # # # # # # #             voice=TTS_VOICE,
# # # # # # # #             input=script_text,
# # # # # # # #             response_format="mp3",
# # # # # # # #         ) as response:
# # # # # # # #             response.stream_to_file(voice_mp3)

# # # # # # # #         return voice_mp3, voice_mp3, "🎙️ Voice generated (sage) with no background."
# # # # # # # #     except Exception as e:
# # # # # # # #         return None, None, f"❌ TTS failed: {e}"

# # # # # # # # # ----------------------------
# # # # # # # # # Gradio wiring
# # # # # # # # # ----------------------------
# # # # # # # # def run_pipeline(user_text: str, target_minutes: int):
# # # # # # # #     # 1) Generate script
# # # # # # # #     echoed, generated, status = generate_script(user_text, target_minutes)

# # # # # # # #     # If script failed, return early
# # # # # # # #     if not generated:
# # # # # # # #         return echoed, generated, status, None, None

# # # # # # # #     # 2) Convert script to voice (sage)
# # # # # # # #     audio_preview, audio_file, tts_status = text_to_voice(generated)
# # # # # # # #     final_status = f"{status}\n{tts_status}"
# # # # # # # #     return echoed, generated, final_status, audio_preview, audio_file

# # # # # # # # with gr.Blocks(title="Mindfulness: Text → Text → Voice (sage)") as demo:
# # # # # # # #     gr.Markdown("# Mindfulness: Text → Text → Voice")
# # # # # # # #     gr.Markdown(
# # # # # # # #         "1) Expands/refines your text into a mindfulness script (no SSML).\n"
# # # # # # # #         "2) Converts that script to **voice** using **sage** (no background music)."
# # # # # # # #     )

# # # # # # # #     with gr.Row():
# # # # # # # #         user_text = gr.Textbox(
# # # # # # # #             label="Your Draft",
# # # # # # # #             value=DEFAULT_TEXT,
# # # # # # # #             lines=12,
# # # # # # # #             placeholder="Paste or write your mindfulness draft here..."
# # # # # # # #         )

# # # # # # # #     with gr.Row():
# # # # # # # #         target_minutes = gr.Number(
# # # # # # # #             label="Target Duration (minutes, approximate)",
# # # # # # # #             value=10,
# # # # # # # #             precision=0
# # # # # # # #         )

# # # # # # # #     run_btn = gr.Button("Generate Script + Voice")

# # # # # # # #     status_md = gr.Markdown()

# # # # # # # #     with gr.Row():
# # # # # # # #         echoed_text = gr.Textbox(label="Original (Echoed)", interactive=False, lines=6)
# # # # # # # #     with gr.Row():
# # # # # # # #         generated_text = gr.Textbox(label="Generated Script", interactive=False, lines=18)
# # # # # # # #     with gr.Row():
# # # # # # # #         voice_preview = gr.Audio(label="Voice (sage)", interactive=False)
# # # # # # # #     with gr.Row():
# # # # # # # #         voice_dl = gr.File(label="Download Voice MP3")

# # # # # # # #     run_btn.click(
# # # # # # # #         run_pipeline,
# # # # # # # #         inputs=[user_text, target_minutes],
# # # # # # # #         outputs=[echoed_text, generated_text, status_md, voice_preview, voice_dl],
# # # # # # # #         api_name="run"
# # # # # # # #     )

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     demo.launch(share=True)

# # # # # # # # Testing 

# # # # # # # import os
# # # # # # # import tempfile
# # # # # # # import subprocess
# # # # # # # from dotenv import load_dotenv
# # # # # # # from openai import OpenAI
# # # # # # # import gradio as gr

# # # # # # # # ----------------------------
# # # # # # # # Setup
# # # # # # # # ----------------------------
# # # # # # # load_dotenv()
# # # # # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # # # if not API_KEY:
# # # # # # #     raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# # # # # # # client = OpenAI(api_key=API_KEY)

# # # # # # # TEXT_MODEL = "gpt-4o-mini"
# # # # # # # TTS_MODEL  = "gpt-4o-mini-tts"
# # # # # # # TTS_VOICE  = "sage"

# # # # # # # DEFAULT_TEXT = "Hello, welcome to your moment of mindfulness..."

# # # # # # # # ----------------------------
# # # # # # # # Helper: loop audio with ffmpeg
# # # # # # # # ----------------------------
# # # # # # # def extend_audio(input_mp3: str, target_seconds: int) -> str:
# # # # # # #     tmpdir = tempfile.mkdtemp(prefix="mindful_tts_")
# # # # # # #     extended_mp3 = os.path.join(tmpdir, f"voice_{target_seconds}s.mp3")
# # # # # # #     cmd = [
# # # # # # #         "ffmpeg", "-y",
# # # # # # #         "-stream_loop", "-1",   # repeat indefinitely
# # # # # # #         "-i", input_mp3,
# # # # # # #         "-t", str(target_seconds),
# # # # # # #         "-c:a", "mp3",
# # # # # # #         "-b:a", "128k",
# # # # # # #         extended_mp3,
# # # # # # #     ]
# # # # # # #     subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# # # # # # #     return extended_mp3

# # # # # # # # ----------------------------
# # # # # # # # Core: Generate script + voice
# # # # # # # # ----------------------------
# # # # # # # def run_pipeline(user_text: str, target_minutes: int):
# # # # # # #     user_text = (user_text or DEFAULT_TEXT).strip()

# # # # # # #     # 1) Generate a *short* mindfulness script (about 30s of speech)
# # # # # # #     sys_prompt = (
# # # # # # #         "You are a mindfulness guide. Create a short 20–30 second calming script. "
# # # # # # #         "It should sound loopable/repetitive (breathing instructions, gentle guidance). "
# # # # # # #         "Do NOT mention duration or audio. Keep it timeless so it can be looped."
# # # # # # #     )
# # # # # # #     resp = client.chat.completions.create(
# # # # # # #         model=TEXT_MODEL,
# # # # # # #         messages=[
# # # # # # #             {"role": "system", "content": sys_prompt},
# # # # # # #             {"role": "user", "content": f"Draft:\n{user_text}"},
# # # # # # #         ],
# # # # # # #         temperature=0.7,
# # # # # # #     )
# # # # # # #     script_text = resp.choices[0].message.content.strip()

# # # # # # #     # 2) Generate short TTS (fast)
# # # # # # #     tmpdir = tempfile.mkdtemp(prefix="mindful_tts_")
# # # # # # #     base_mp3 = os.path.join(tmpdir, "base.mp3")
# # # # # # #     with client.audio.speech.with_streaming_response.create(
# # # # # # #         model=TTS_MODEL,
# # # # # # #         voice=TTS_VOICE,
# # # # # # #         input=script_text,
# # # # # # #         response_format="mp3",
# # # # # # #     ) as response:
# # # # # # #         response.stream_to_file(base_mp3)

# # # # # # #     # 3) Extend to target duration (≈10 min)
# # # # # # #     target_seconds = max(60, int(target_minutes) * 60)
# # # # # # #     extended_mp3 = extend_audio(base_mp3, target_seconds)

# # # # # # #     return user_text, script_text, f"✅ Done! Generated ~{target_minutes} min voice in seconds.", extended_mp3, extended_mp3

# # # # # # # # ----------------------------
# # # # # # # # Gradio UI
# # # # # # # # ----------------------------
# # # # # # # with gr.Blocks(title="Mindfulness: Fast 10-min Voice (sage)") as demo:
# # # # # # #     gr.Markdown("# Mindfulness: Fast 10-min Voice (sage)")
# # # # # # #     gr.Markdown(
# # # # # # #         "Generates a short mindfulness script (~30s), converts it to voice with **sage**, "
# # # # # # #         "then loops it to exactly the target duration (e.g., 10 minutes). "
# # # # # # #         "⚡ Fast: ~10s even for long output."
# # # # # # #     )

# # # # # # #     with gr.Row():
# # # # # # #         user_text = gr.Textbox(label="Your Draft", value=DEFAULT_TEXT, lines=6)
# # # # # # #     with gr.Row():
# # # # # # #         target_minutes = gr.Number(label="Target Duration (minutes)", value=10, precision=0)

# # # # # # #     run_btn = gr.Button("Generate Fast Voice")

# # # # # # #     status_md = gr.Markdown()
# # # # # # #     echoed_text = gr.Textbox(label="Original (Echoed)", interactive=False, lines=4)
# # # # # # #     generated_text = gr.Textbox(label="Generated Script (~30s)", interactive=False, lines=10)
# # # # # # #     voice_preview = gr.Audio(label="Voice (sage)", interactive=False)
# # # # # # #     voice_dl = gr.File(label="Download Voice MP3")

# # # # # # #     run_btn.click(
# # # # # # #         run_pipeline,
# # # # # # #         inputs=[user_text, target_minutes],
# # # # # # #         outputs=[echoed_text, generated_text, status_md, voice_preview, voice_dl],
# # # # # # #         api_name="run"
# # # # # # #     )

# # # # # # # if __name__ == "__main__":
# # # # # # #     demo.launch(share=True)


# # # # # # # mindfulness_tts_10min.py
# # # # # # import os
# # # # # # import tempfile
# # # # # # from dotenv import load_dotenv
# # # # # # from openai import OpenAI
# # # # # # import gradio as gr
# # # # # # from pydub import AudioSegment   # pip install pydub

# # # # # # # ----------------------------
# # # # # # # Setup
# # # # # # # ----------------------------
# # # # # # load_dotenv()
# # # # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # # if not API_KEY:
# # # # # #     raise ValueError("❌ OPENAI_API_KEY not found in .env file.")

# # # # # # client = OpenAI(api_key=API_KEY)

# # # # # # # Models
# # # # # # TEXT_MODEL = "gpt-4o-mini"
# # # # # # TTS_MODEL  = "gpt-4o-mini-tts"
# # # # # # TTS_VOICE  = "sage"

# # # # # # DEFAULT_TEXT = (
# # # # # #     "Welcome to this extended mindfulness meditation. "
# # # # # #     "You are invited to rest your attention on the gentle flow of breath, "
# # # # # #     "allowing body and mind to gradually soften. Over these next minutes, "
# # # # # #     "we will travel through breath awareness, body scan, and open presence."
# # # # # # )

# # # # # # INSTRUCTIONS_TEXT = (
# # # # # #     "Style: Soft, gentle, soothing; calm and reassuring.\n"
# # # # # #     "Do NOT include pause markers, SSML, or stage directions.\n"
# # # # # #     "Continuity: Write as one continuous narration suitable for TTS.\n"
# # # # # #     "Expand naturally to reach at least {minutes} minutes of spoken content."
# # # # # # )

# # # # # # # ----------------------------
# # # # # # # Core: Text → Text
# # # # # # # ----------------------------
# # # # # # def generate_script(user_text: str, target_minutes: int):
# # # # # #     user_text = (user_text or "").strip()
# # # # # #     if not user_text:
# # # # # #         return "", "", "⚠️ Please enter text."

# # # # # #     # TTS pace is ~150 words/min → need extra words for full duration
# # # # # #     pace_wpm = 150
# # # # # #     min_words = int(target_minutes * pace_wpm * 1.15)  # +15% buffer

# # # # # #     sys_prompt = (
# # # # # #         "You are a mindfulness scriptwriter. Rewrite or expand the user's text into a calm, guided "
# # # # # #         "meditation suitable for TTS as one continuous narration.\n\n"
# # # # # #         f"Target length: at least ~{min_words} words (≥{target_minutes} minutes at ~{pace_wpm} wpm).\n"
# # # # # #         "Avoid lists, bullet points, and repetition. Keep the flow gentle and coherent.\n"
# # # # # #         "Do NOT include any pause markers, ellipses, SSML tags, or stage directions."
# # # # # #     )
# # # # # #     style_block = INSTRUCTIONS_TEXT.format(minutes=target_minutes)

# # # # # #     try:
# # # # # #         resp = client.chat.completions.create(
# # # # # #             model=TEXT_MODEL,
# # # # # #             messages=[
# # # # # #                 {"role": "system", "content": sys_prompt},
# # # # # #                 {"role": "user", "content": f"{style_block}\n\nUser draft:\n{user_text}"},
# # # # # #             ],
# # # # # #             temperature=0.7,
# # # # # #         )
# # # # # #         out_text = resp.choices[0].message.content.strip()
# # # # # #         wc = len(out_text.split())
# # # # # #         return user_text, out_text, f"✅ Script generated with {wc} words (target ≥{min_words})."
# # # # # #     except Exception as e:
# # # # # #         return user_text, "", f"❌ Generation failed: {e}"

# # # # # # # ----------------------------
# # # # # # # Core: Text → Voice (chunked merge)
# # # # # # # ----------------------------
# # # # # # def text_to_voice(script_text: str):
# # # # # #     if not script_text.strip():
# # # # # #         return None, None, "⚠️ No script."

# # # # # #     try:
# # # # # #         tmpdir = tempfile.mkdtemp(prefix="mindful_tts_")
# # # # # #         final_mp3 = os.path.join(tmpdir, "final_voice.mp3")

# # # # # #         # Split into safe chunks (~1000 words each)
# # # # # #         words = script_text.split()
# # # # # #         chunk_size = 1000
# # # # # #         chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

# # # # # #         audio_segments = []
# # # # # #         for idx, chunk in enumerate(chunks, 1):
# # # # # #             part_file = os.path.join(tmpdir, f"part_{idx}.mp3")
# # # # # #             with client.audio.speech.with_streaming_response.create(
# # # # # #                 model=TTS_MODEL,
# # # # # #                 voice=TTS_VOICE,
# # # # # #                 input=chunk,
# # # # # #                 response_format="mp3",
# # # # # #             ) as response:
# # # # # #                 response.stream_to_file(part_file)
# # # # # #             audio_segments.append(AudioSegment.from_mp3(part_file))

# # # # # #         # Concatenate all
# # # # # #         combined = sum(audio_segments[1:], audio_segments[0])
# # # # # #         combined.export(final_mp3, format="mp3")

# # # # # #         total_minutes = round(len(combined) / 60000, 2)
# # # # # #         return final_mp3, final_mp3, f"🎙️ Voice generated in {len(chunks)} parts → merged ({total_minutes} min)."
# # # # # #     except Exception as e:
# # # # # #         return None, None, f"❌ TTS failed: {e}"

# # # # # # # ----------------------------
# # # # # # # Pipeline
# # # # # # # ----------------------------
# # # # # # def run_pipeline(user_text: str, target_minutes: int):
# # # # # #     echoed, generated, status = generate_script(user_text, target_minutes)
# # # # # #     if not generated:
# # # # # #         return echoed, generated, status, None, None

# # # # # #     audio_preview, audio_file, tts_status = text_to_voice(generated)
# # # # # #     final_status = f"{status}\n{tts_status}"
# # # # # #     return echoed, generated, final_status, audio_preview, audio_file

# # # # # # with gr.Blocks(title="Mindfulness: Full 10-Minute Audio") as demo:
# # # # # #     gr.Markdown("# Mindfulness: 10+ Minute Script → Voice")
# # # # # #     gr.Markdown("Ensures narration lasts **at least 10 minutes** by generating extra words.")

# # # # # #     with gr.Row():
# # # # # #         user_text = gr.Textbox(label="Your Draft", value=DEFAULT_TEXT, lines=12)

# # # # # #     with gr.Row():
# # # # # #         target_minutes = gr.Number(label="Target Duration (min)", value=10, precision=0)

# # # # # #     run_btn = gr.Button("Generate Script + Voice")

# # # # # #     status_md = gr.Markdown()
# # # # # #     echoed_text = gr.Textbox(label="Original (Echoed)", interactive=False, lines=6)
# # # # # #     generated_text = gr.Textbox(label="Generated Script", interactive=False, lines=18)
# # # # # #     voice_preview = gr.Audio(label="Voice (sage)", interactive=False)
# # # # # #     voice_dl = gr.File(label="Download Voice MP3")

# # # # # #     run_btn.click(
# # # # # #         run_pipeline,
# # # # # #         inputs=[user_text, target_minutes],
# # # # # #         outputs=[echoed_text, generated_text, status_md, voice_preview, voice_dl],
# # # # # #         api_name="run"
# # # # # #     )

# # # # # # if __name__ == "__main__":
# # # # # #     demo.launch(share=True)



# # # # # """
# # # # # Gradio app: Generate a 10-minute mindfulness script (TEXT ONLY) + timing

# # # # # - No TTS, no audio, no SSML, no pause markers, no stage directions.
# # # # # - Ensures the final text is long enough for ≥10 minutes of narration.
# # # # # - Shows script in UI + downloadable .txt file.
# # # # # - Returns how many seconds the generation took.

# # # # # Requirements:
# # # # #   pip install gradio python-dotenv openai
# # # # #   (Set OPENAI_API_KEY in your .env or environment)
# # # # # """

# # # # # import os
# # # # # import time
# # # # # import tempfile
# # # # # from math import ceil
# # # # # from datetime import datetime
# # # # # from dotenv import load_dotenv
# # # # # from openai import OpenAI
# # # # # import gradio as gr

# # # # # # ----------------------------
# # # # # # Setup
# # # # # # ----------------------------
# # # # # load_dotenv()
# # # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # # if not API_KEY:
# # # # #     raise RuntimeError("❌ OPENAI_API_KEY not found in environment or .env")

# # # # # client = OpenAI(api_key=API_KEY)

# # # # # # Model for TEXT generation
# # # # # TEXT_MODEL = "gpt-4o-mini"

# # # # # # ----------------------------
# # # # # # Defaults & Config
# # # # # # ----------------------------
# # # # # DEFAULT_DRAFT = (
# # # # #     "Welcome to this extended mindfulness meditation. Over the next ten minutes, "
# # # # #     "you’ll settle into a gentle rhythm: arriving in the body, breathing with awareness, "
# # # # #     "scanning from head to toe, and resting in open presence."
# # # # # )

# # # # # TARGET_MINUTES_DEFAULT = 10
# # # # # PACE_WPM_DEFAULT = 140   # conservative speaking pace
# # # # # BUFFER_DEFAULT   = 1.20  # 20% extra words to safely exceed 10 minutes

# # # # # SYSTEM_PROMPT_TEMPLATE = """You are a mindfulness scriptwriter.
# # # # # Rewrite or expand the user's draft into a single, continuous guided meditation narration.

# # # # # Constraints:
# # # # # - Length: at least ~{min_words} words (sufficient for ≥{minutes} minutes at ~{pace_wpm} wpm).
# # # # # - Style: Soft, warm, steady, reassuring; natural human phrasing.
# # # # # - Flow: One continuous narration. No lists, no bullet points, no sections or headings.
# # # # # - Content: Gentle arrival, breath awareness, gradual body scan, and open presence.
# # # # # - DO NOT include any SSML, pause markers, ellipses (...), or stage directions.
# # # # # - Avoid repetition and filler; keep it coherent and grounded.
# # # # # - Keep language simple and soothing.

# # # # # End the piece with a calm closing that gently transitions back to the day.
# # # # # """

# # # # # CONTINUE_SYSTEM_PROMPT = """Continue the SAME narration seamlessly from where it stopped.
# # # # # Do NOT restart or summarize. Maintain the exact tone and constraints:
# # # # # - Continuous narration, no lists/headings, no SSML, no pause markers, no stage directions, no ellipses.
# # # # # - Keep it coherent, soothing, and grounded.
# # # # # - Add new, non-redundant content that flows naturally.
# # # # # """

# # # # # # ----------------------------
# # # # # # Core generation
# # # # # # ----------------------------
# # # # # def _min_words(minutes: int, pace_wpm: int, buffer: float) -> int:
# # # # #     return ceil(minutes * pace_wpm * buffer)

# # # # # def generate_10min_script(
# # # # #     user_draft: str,
# # # # #     minutes: int = TARGET_MINUTES_DEFAULT,
# # # # #     pace_wpm: int = PACE_WPM_DEFAULT,
# # # # #     buffer: float = BUFFER_DEFAULT,
# # # # #     max_continuations: int = 3
# # # # # ):
# # # # #     user_draft = (user_draft or "").strip()
# # # # #     if not user_draft:
# # # # #         return "", "⚠️ Please enter a draft."

# # # # #     target_words = _min_words(minutes, pace_wpm, buffer)

# # # # #     # First pass
# # # # #     sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(
# # # # #         min_words=target_words, minutes=minutes, pace_wpm=pace_wpm
# # # # #     )

# # # # #     try:
# # # # #         resp = client.chat.completions.create(
# # # # #             model=TEXT_MODEL,
# # # # #             messages=[
# # # # #                 {"role": "system", "content": sys_prompt},
# # # # #                 {"role": "user", "content": f"Draft:\n{user_draft}"},
# # # # #             ],
# # # # #             temperature=0.7,
# # # # #             presence_penalty=0.2,
# # # # #             frequency_penalty=0.2,
# # # # #             max_tokens=4096,
# # # # #         )
# # # # #         text = (resp.choices[0].message.content or "").strip()
# # # # #     except Exception as e:
# # # # #         return "", f"❌ Generation failed: {e}"

# # # # #     # Continue until target length or attempts exhausted
# # # # #     attempts = 0
# # # # #     while len(text.split()) < target_words and attempts < max_continuations:
# # # # #         remaining = target_words - len(text.split())
# # # # #         attempts += 1
# # # # #         try:
# # # # #             cont_resp = client.chat.completions.create(
# # # # #                 model=TEXT_MODEL,
# # # # #                 messages=[
# # # # #                     {"role": "system", "content": CONTINUE_SYSTEM_PROMPT},
# # # # #                     {"role": "user", "content": f"Continue seamlessly. Add at least ~{remaining} more words."},
# # # # #                     {"role": "assistant", "content": text[-1200:]},  # tail context for coherence
# # # # #                 ],
# # # # #                 temperature=0.7,
# # # # #                 presence_penalty=0.2,
# # # # #                 frequency_penalty=0.2,
# # # # #                 max_tokens=4096,
# # # # #             )
# # # # #             addition = (cont_resp.choices[0].message.content or "").strip()
# # # # #             if addition and addition not in text:
# # # # #                 text = f"{text}\n\n{addition}"
# # # # #             else:
# # # # #                 break
# # # # #         except Exception as e:
# # # # #             return text, f"⚠️ Partial success. Continuation failed: {e}"

# # # # #     wc = len(text.split())
# # # # #     status = (
# # # # #         f"✅ Generated {wc} words (target ≥{target_words}; "
# # # # #         f"{minutes} min @ ~{pace_wpm} wpm with {int((buffer-1)*100)}% buffer)."
# # # # #         if wc >= target_words
# # # # #         else f"⚠️ Generated {wc} words (< target {target_words}). Consider clicking again to extend."
# # # # #     )
# # # # #     return text, status

# # # # # def pipeline(user_text, minutes, pace_wpm, buffer):
# # # # #     minutes = int(minutes) if minutes else TARGET_MINUTES_DEFAULT
# # # # #     pace_wpm = int(pace_wpm) if pace_wpm else PACE_WPM_DEFAULT
# # # # #     buffer   = float(buffer) if buffer else BUFFER_DEFAULT

# # # # #     t0 = time.time()
# # # # #     script, status = generate_10min_script(
# # # # #         user_text,
# # # # #         minutes=minutes,
# # # # #         pace_wpm=pace_wpm,
# # # # #         buffer=buffer,
# # # # #         max_continuations=3,
# # # # #     )

# # # # #     # Save to a temp file for download
# # # # #     download_path = None
# # # # #     if script:
# # # # #         tmpdir = tempfile.mkdtemp(prefix="mindful_text_")
# # # # #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# # # # #         download_path = os.path.join(tmpdir, f"mindfulness_{minutes}min_{timestamp}.txt")
# # # # #         with open(download_path, "w", encoding="utf-8") as f:
# # # # #             f.write(script)

# # # # #     elapsed_sec = round(time.time() - t0, 2)
# # # # #     status = f"{status}\n⏱️ Generation time: {elapsed_sec} seconds."

# # # # #     return status, script, download_path, elapsed_sec

# # # # # # ----------------------------
# # # # # # Gradio UI
# # # # # # ----------------------------
# # # # # with gr.Blocks(title="Mindfulness: 10‑Minute Script (Text Only)") as demo:
# # # # #     gr.Markdown("# 🧘 10‑Minute Mindfulness Script (Text Only)")
# # # # #     gr.Markdown(
# # # # #         "Generates a single **continuous narration** suitable for TTS, but **no audio** is produced here. "
# # # # #         "No SSML, no pause markers, no stage directions."
# # # # #     )

# # # # #     with gr.Row():
# # # # #         draft = gr.Textbox(
# # # # #             label="Your Draft",
# # # # #             value=DEFAULT_DRAFT,
# # # # #             lines=10,
# # # # #             placeholder="Paste a seed idea or keep the default…",
# # # # #         )

# # # # #     with gr.Accordion("Advanced (optional)", open=False):
# # # # #         with gr.Row():
# # # # #             minutes   = gr.Number(label="Target minutes", value=10, precision=0)
# # # # #             pace_wpm  = gr.Number(label="Words per minute (estimate)", value=140, precision=0)
# # # # #             buffer    = gr.Slider(label="Length buffer (x)", minimum=1.00, maximum=1.40, step=0.05, value=1.20)

# # # # #     run_btn = gr.Button("Generate 10‑Minute Script")

# # # # #     status_md = gr.Markdown()
# # # # #     script_box = gr.Textbox(label="Generated Script", lines=26, interactive=False)
# # # # #     file_dl = gr.File(label="Download .txt")
# # # # #     gen_time = gr.Number(label="Generation time (seconds)", value=0, interactive=False, precision=2)

# # # # #     run_btn.click(
# # # # #         pipeline,
# # # # #         inputs=[draft, minutes, pace_wpm, buffer],
# # # # #         outputs=[status_md, script_box, file_dl, gen_time],
# # # # #         api_name="generate_script_10min_text_only_timed"
# # # # #     )

# # # # # if __name__ == "__main__":
# # # # #     demo.launch(share=True)


# # # # """
# # # # Gradio app: Generate a 10-minute mindfulness script (TEXT ONLY) + timing

# # # # - No TTS, no audio, no SSML, no pause markers, no stage directions.
# # # # - Ensures the final text is long enough for ≥10 minutes of narration.
# # # # - Shows script in UI + downloadable .txt file.
# # # # - Returns how many seconds the generation took.

# # # # Requirements:
# # # #   pip install gradio python-dotenv openai
# # # #   (Set OPENAI_API_KEY in your .env or environment)
# # # # """

# # # # import os
# # # # import time
# # # # import tempfile
# # # # from math import ceil
# # # # from datetime import datetime
# # # # from dotenv import load_dotenv
# # # # from openai import OpenAI
# # # # import gradio as gr

# # # # # ----------------------------
# # # # # Setup
# # # # # ----------------------------
# # # # load_dotenv()
# # # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # # if not API_KEY:
# # # #     raise RuntimeError("❌ OPENAI_API_KEY not found in environment or .env")

# # # # client = OpenAI(api_key=API_KEY)

# # # # # Model for TEXT generation
# # # # TEXT_MODEL = "gpt-4o-mini"

# # # # # ----------------------------
# # # # # Defaults & Config
# # # # # ----------------------------
# # # # DEFAULT_DRAFT = (
# # # #     "Welcome to this extended mindfulness meditation. Over the next ten minutes, "
# # # #     "you’ll settle into a gentle rhythm: arriving in the body, breathing with awareness, "
# # # #     "scanning from head to toe, and resting in open presence."
# # # # )

# # # # TARGET_MINUTES_DEFAULT = 10
# # # # PACE_WPM_DEFAULT = 140   # conservative speaking pace
# # # # BUFFER_DEFAULT   = 1.20  # 20% extra words to safely exceed 10 minutes

# # # # SYSTEM_PROMPT_TEMPLATE = """You are a mindfulness scriptwriter.
# # # # Rewrite or expand the user's draft into a single, continuous guided meditation narration.

# # # # Constraints:
# # # # - Length: at least ~{min_words} words (sufficient for ≥{minutes} minutes at ~{pace_wpm} wpm).
# # # # - Style: Soft, warm, steady, reassuring; natural human phrasing.
# # # # - Flow: One continuous narration. No lists, no bullet points, no sections or headings.
# # # # - Content: Gentle arrival, breath awareness, gradual body scan, and open presence.
# # # # - DO NOT include any SSML, pause markers, ellipses (...), or stage directions.
# # # # - Avoid repetition and filler; keep it coherent and grounded.
# # # # - Keep language simple and soothing.

# # # # End the piece with a calm closing that gently transitions back to the day.
# # # # """

# # # # CONTINUE_SYSTEM_PROMPT = """Continue the SAME narration seamlessly from where it stopped.
# # # # Do NOT restart or summarize. Maintain the exact tone and constraints:
# # # # - Continuous narration, no lists/headings, no SSML, no pause markers, no stage directions, no ellipses.
# # # # - Keep it coherent, soothing, and grounded.
# # # # - Add new, non-redundant content that flows naturally.
# # # # """

# # # # # ----------------------------
# # # # # Core generation
# # # # # ----------------------------
# # # # def _min_words(minutes: int, pace_wpm: int, buffer: float) -> int:
# # # #     return ceil(minutes * pace_wpm * buffer)

# # # # def generate_10min_script(
# # # #     user_draft: str,
# # # #     minutes: int = TARGET_MINUTES_DEFAULT,
# # # #     pace_wpm: int = PACE_WPM_DEFAULT,
# # # #     buffer: float = BUFFER_DEFAULT,
# # # #     max_continuations: int = 3
# # # # ):
# # # #     user_draft = (user_draft or "").strip()
# # # #     if not user_draft:
# # # #         return "", "⚠️ Please enter a draft."

# # # #     target_words = _min_words(minutes, pace_wpm, buffer)

# # # #     # First pass
# # # #     sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(
# # # #         min_words=target_words, minutes=minutes, pace_wpm=pace_wpm
# # # #     )

# # # #     try:
# # # #         resp = client.chat.completions.create(
# # # #             model=TEXT_MODEL,
# # # #             messages=[
# # # #                 {"role": "system", "content": sys_prompt},
# # # #                 {"role": "user", "content": f"Draft:\n{user_draft}"},
# # # #             ],
# # # #             temperature=0.7,
# # # #             presence_penalty=0.2,
# # # #             frequency_penalty=0.2,
# # # #             max_tokens=4096,
# # # #         )
# # # #         text = (resp.choices[0].message.content or "").strip()
# # # #     except Exception as e:
# # # #         return "", f"❌ Generation failed: {e}"

# # # #     # Continue until target length or attempts exhausted
# # # #     attempts = 0
# # # #     while len(text.split()) < target_words and attempts < max_continuations:
# # # #         remaining = target_words - len(text.split())
# # # #         attempts += 1
# # # #         try:
# # # #             cont_resp = client.chat.completions.create(
# # # #                 model=TEXT_MODEL,
# # # #                 messages=[
# # # #                     {"role": "system", "content": CONTINUE_SYSTEM_PROMPT},
# # # #                     {"role": "user", "content": f"Continue seamlessly. Add at least ~{remaining} more words."},
# # # #                     {"role": "assistant", "content": text[-1200:]},  # tail context for coherence
# # # #                 ],
# # # #                 temperature=0.7,
# # # #                 presence_penalty=0.2,
# # # #                 frequency_penalty=0.2,
# # # #                 max_tokens=4096,
# # # #             )
# # # #             addition = (cont_resp.choices[0].message.content or "").strip()
# # # #             if addition and addition not in text:
# # # #                 text = f"{text}\n\n{addition}"
# # # #             else:
# # # #                 break
# # # #         except Exception as e:
# # # #             return text, f"⚠️ Partial success. Continuation failed: {e}"

# # # #     wc = len(text.split())
# # # #     status = (
# # # #         f"✅ Generated {wc} words (target ≥{target_words}; "
# # # #         f"{minutes} min @ ~{pace_wpm} wpm with {int((buffer-1)*100)}% buffer)."
# # # #         if wc >= target_words
# # # #         else f"⚠️ Generated {wc} words (< target {target_words}). Consider clicking again to extend."
# # # #     )
# # # #     return text, status

# # # # def pipeline(user_text, minutes, pace_wpm, buffer):
# # # #     minutes = int(minutes) if minutes else TARGET_MINUTES_DEFAULT
# # # #     pace_wpm = int(pace_wpm) if pace_wpm else PACE_WPM_DEFAULT
# # # #     buffer   = float(buffer) if buffer else BUFFER_DEFAULT

# # # #     t0 = time.time()
# # # #     script, status = generate_10min_script(
# # # #         user_text,
# # # #         minutes=minutes,
# # # #         pace_wpm=pace_wpm,
# # # #         buffer=buffer,
# # # #         max_continuations=3,
# # # #     )

# # # #     # Save to a temp file for download
# # # #     download_path = None
# # # #     if script:
# # # #         tmpdir = tempfile.mkdtemp(prefix="mindful_text_")
# # # #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# # # #         download_path = os.path.join(tmpdir, f"mindfulness_{minutes}min_{timestamp}.txt")
# # # #         with open(download_path, "w", encoding="utf-8") as f:
# # # #             f.write(script)

# # # #     elapsed_sec = round(time.time() - t0, 2)
# # # #     status = f"{status}\n⏱️ Generation time: {elapsed_sec} seconds."

# # # #     return status, script, download_path, elapsed_sec

# # # # # ----------------------------
# # # # # Gradio UI
# # # # # ----------------------------
# # # # with gr.Blocks(title="Mindfulness: 10‑Minute Script (Text Only)") as demo:
# # # #     gr.Markdown("# 🧘 10‑Minute Mindfulness Script (Text Only)")
# # # #     gr.Markdown(
# # # #         "Generates a single **continuous narration** suitable for TTS, but **no audio** is produced here. "
# # # #         "No SSML, no pause markers, no stage directions."
# # # #     )

# # # #     with gr.Row():
# # # #         draft = gr.Textbox(
# # # #             label="Your Draft",
# # # #             value=DEFAULT_DRAFT,
# # # #             lines=10,
# # # #             placeholder="Paste a seed idea or keep the default…",
# # # #         )

# # # #     with gr.Accordion("Advanced (optional)", open=False):
# # # #         with gr.Row():
# # # #             minutes   = gr.Number(label="Target minutes", value=10, precision=0)
# # # #             pace_wpm  = gr.Number(label="Words per minute (estimate)", value=140, precision=0)
# # # #             buffer    = gr.Slider(label="Length buffer (x)", minimum=1.00, maximum=1.40, step=0.05, value=1.20)

# # # #     run_btn = gr.Button("Generate 10‑Minute Script")

# # # #     status_md = gr.Markdown()
# # # #     script_box = gr.Textbox(label="Generated Script", lines=26, interactive=False)
# # # #     file_dl = gr.File(label="Download .txt")
# # # #     gen_time = gr.Number(label="Generation time (seconds)", value=0, interactive=False, precision=2)

# # # #     run_btn.click(
# # # #         pipeline,
# # # #         inputs=[draft, minutes, pace_wpm, buffer],
# # # #         outputs=[status_md, script_box, file_dl, gen_time],
# # # #         api_name="generate_script_10min_text_only_timed"
# # # #     )

# # # # if __name__ == "__main__":
# # # #     demo.launch(share=True)



# # # # mindfulness_script_only.py
# # # import os, tempfile, time
# # # from dotenv import load_dotenv
# # # from openai import OpenAI
# # # import gradio as gr

# # # # ----------------------------
# # # # Setup
# # # # ----------------------------
# # # load_dotenv()
# # # API_KEY = os.getenv("OPENAI_API_KEY")
# # # if not API_KEY:
# # #     raise RuntimeError("❌ OPENAI_API_KEY not found in .env")

# # # client = OpenAI(api_key=API_KEY)

# # # TEXT_MODEL = "gpt-4o-mini"

# # # DEFAULT_DRAFT = (
# # #     "Guide me through a calm, grounding 10-minute mindfulness meditation "
# # #     "for beginners, centered on breathing, gentle body awareness, and soft visualization."
# # # )

# # # INSTRUCTIONS_TEXT = (
# # #     "Style: Soft, gentle, reassuring. Use simple, concrete language. "
# # #     "Pacing: Slow and unhurried (no explicit pause markers). "
# # #     "Tone: Warm, kind, non-judgmental. "
# # #     "Format: Short paragraphs and line breaks for readability; no bullet points. "
# # #     "Do NOT add SSML, sound effects, timestamps, or [pause] cues. "
# # #     "Goal: Produce a natural narration suitable to be read aloud for about {minutes} minutes."
# # # )

# # # def target_word_count(minutes: int = 10, wpm: int = 125) -> int:
# # #     return max(600, int(minutes * wpm))

# # # def generate_script(user_text: str, target_minutes: int = 10):
# # #     user_text = (user_text or "").strip() or DEFAULT_DRAFT
# # #     approx_words = target_word_count(target_minutes, wpm=125)

# # #     sys_prompt = (
# # #         "You are an expert mindfulness scriptwriter.\n"
# # #         f"Expand and refine the user's idea into a cohesive guided-meditation script.\n"
# # #         f"Target ≈{approx_words} words (≈{target_minutes} minutes at ~125 wpm).\n"
# # #         "Keep it realistic to read aloud in one take, with smooth transitions.\n"
# # #         "Avoid medical/clinical claims. Beginner-friendly.\n"
# # #         "Do NOT include SSML, timestamps, or [pause] markers."
# # #     )
# # #     style_block = INSTRUCTIONS_TEXT.format(minutes=target_minutes)

# # #     start = time.time()
# # #     resp = client.chat.completions.create(
# # #         model=TEXT_MODEL,
# # #         temperature=0.7,
# # #         messages=[
# # #             {"role": "system", "content": sys_prompt},
# # #             {"role": "user", "content": f"{style_block}\n\nUser brief:\n{user_text}"},
# # #         ],
# # #     )
# # #     elapsed = round(time.time() - start, 2)  # seconds

# # #     out_text = resp.choices[0].message.content.strip()

# # #     # Write script to a temporary file
# # #     tmpdir = tempfile.mkdtemp(prefix="mindful_script_")
# # #     txt_path = os.path.join(tmpdir, "script.txt")
# # #     with open(txt_path, "w", encoding="utf-8") as f:
# # #         f.write(out_text)

# # #     status = (
# # #         f"✅ Generated ~{target_minutes}-minute script "
# # #         f"(target ≈{approx_words} words).\n⏱️ Time taken: {elapsed} seconds"
# # #     )
# # #     return out_text, status, txt_path, elapsed


# # # # ----------------------------
# # # # Gradio UI
# # # # ----------------------------
# # # def run_pipeline(user_text: str, minutes: int):
# # #     script, status, file_path, elapsed = generate_script(user_text, minutes)
# # #     return script, status, file_path, elapsed

# # # with gr.Blocks(title="Mindfulness Script Generator (Text Only)") as demo:
# # #     gr.Markdown("# Mindfulness Script Generator (Text Only)")
# # #     gr.Markdown(
# # #         "Generates a calming, **~10-minute** meditation script.\n"
# # #         "- No audio, no SSML, no pause markers\n"
# # #         "- Shows how many seconds it took"
# # #     )

# # #     with gr.Row():
# # #         draft = gr.Textbox(
# # #             label="Your Brief (optional)",
# # #             value=DEFAULT_DRAFT,
# # #             lines=8,
# # #             placeholder="Describe the focus (e.g., breath, body scan, nature imagery)...",
# # #         )
# # #         minutes = gr.Number(label="Target Minutes", value=10, precision=0)

# # #     run_btn = gr.Button("Generate Script")
# # #     status_md = gr.Markdown()
# # #     script_box = gr.Textbox(label="Generated Script", lines=22)
# # #     script_file = gr.File(label="Download .txt")
# # #     elapsed_box = gr.Number(label="Generation Time (seconds)", interactive=False)

# # #     run_btn.click(
# # #         run_pipeline,
# # #         inputs=[draft, minutes],
# # #         outputs=[script_box, status_md, script_file, elapsed_box],
# # #         api_name="run",
# # #     )

# # # if __name__ == "__main__":
# # #     demo.launch(share=True)



# # import os
# # import asyncio
# # import math
# # from dotenv import load_dotenv
# # from openai import AsyncOpenAI

# # # -------- Load API Key Securely from `.env` --------
# # load_dotenv()  # Loads variables from .env file into environment

# # api_key = os.getenv("OPENAI_API_KEY")
# # if not api_key:
# #     raise RuntimeError("OPENAI_API_KEY not found. Make sure .env contains the key and dotenv is installed.")

# # # ---------- Config ----------
# # MODEL = "gpt-4o-mini"
# # TARGET_MINUTES = 10
# # SPEAKING_WPM = 155
# # TOTAL_WORD_TARGET = TARGET_MINUTES * SPEAKING_WPM
# # N_SECTIONS = 10
# # WORDS_PER_SECTION = math.ceil(TOTAL_WORD_TARGET / N_SECTIONS)

# # TOPIC_BRIEF = (
# #     "Guide a beginner through a calm mindfulness session focused on breath, "
# #     "body awareness, gentle visualization, and a positive closing. "
# #     "Style: warm, concrete, encouraging; short paragraphs; no timestamps, no SSML; "
# #     "avoid bullet points; keep it natural to read aloud."
# # )

# # OUTLINE = [
# #     "Opening welcome & set intention",
# #     "Posture & environment setup",
# #     "Initial breath awareness",
# #     "Counting the breath (light focus)",
# #     "Body scan (head to toes)",
# #     "Handling distractions kindly",
# #     "Gentle visualization (safe place)",
# #     "Gratitude micro-reflection",
# #     "Preparing to close (re-orient body)",
# #     "Closing message & next-steps"
# # ]

# # # ---------- Async client ----------
# # client = AsyncOpenAI(api_key=api_key)

# # SYSTEM = (
# #     "You are a skilled meditation scriptwriter. "
# #     "Write natural, human-sounding narration for voice-over. "
# #     "No timestamps, no SSML, no stage directions. "
# #     "Use short paragraphs and smooth transitions."
# # )

# # SECTION_PROMPT_TEMPLATE = """Topic: {topic}
# # Section: {heading}

# # Write this section as continuous narration, 100% self-contained (no TODOs), 
# # aiming for ~{words} words. Keep consistent tone and avoid repeating the exact 
# # phrases from other sections (assume they will be stitched together). 
# # Do not include headings in the output—just the narration text."""

# # async def gen_section(idx: int, heading: str) -> tuple[int, str]:
# #     prompt = SECTION_PROMPT_TEMPLATE.format(
# #         topic=TOPIC_BRIEF, heading=heading, words=WORDS_PER_SECTION
# #     )
# #     rsp = await client.chat.completions.create(
# #         model=MODEL,
# #         temperature=0.7,
# #         messages=[
# #             {"role":"system", "content": SYSTEM},
# #             {"role":"user", "content": prompt}
# #         ]
# #     )
# #     text = rsp.choices[0].message.content.strip()
# #     return (idx, text)

# # async def generate_full_script():
# #     tasks = [gen_section(i, OUTLINE[i]) for i in range(N_SECTIONS)]
# #     results = await asyncio.gather(*tasks)
# #     results.sort(key=lambda x: x[0])
# #     sections = [s for _, s in results]
# #     script = "\n\n".join(sections)
# #     return script

# # def main():
# #     full_script = asyncio.run(generate_full_script())
# #     words = len(full_script.split())
# #     mins = words / SPEAKING_WPM
# #     print(f"≈{words} words (~{mins:.1f} minutes at {SPEAKING_WPM} wpm)\n")
# #     print(full_script)

# # if __name__ == "__main__":
# #     main()



# # Generate Content
# # import os, asyncio, math, time
# # import gradio as gr
# # from dotenv import load_dotenv
# # from openai import AsyncOpenAI

# # # ---------- .env ----------
# # load_dotenv()
# # API_KEY = os.getenv("OPENAI_API_KEY")
# # if not API_KEY:
# #     raise RuntimeError("OPENAI_API_KEY not found in .env")

# # # ---------- Config ----------
# # MODEL = "gpt-4o-mini"    # low latency
# # TARGET_MINUTES = 10
# # SPEAKING_WPM = 155       # ~150–160 wpm ≈ 10 min ~ 1500–1600 words
# # TOTAL_WORD_TARGET = TARGET_MINUTES * SPEAKING_WPM
# # N_SECTIONS = 10
# # WORDS_PER_SECTION = math.ceil(TOTAL_WORD_TARGET / N_SECTIONS)

# # DEFAULT_TOPIC = (
# #     "Guide a beginner through a calm mindfulness session focused on breath, "
# #     "body awareness, gentle visualization, and a positive closing. "
# #     "Style: warm, concrete, encouraging; short paragraphs; no timestamps, no SSML; "
# #     "avoid bullet points; keep it natural to read aloud."
# # )

# # OUTLINE = [
# #     "Opening welcome & set intention",
# #     "Posture & environment setup",
# #     "Initial breath awareness",
# #     "Counting the breath (light focus)",
# #     "Body scan (head to toes)",
# #     "Handling distractions kindly",
# #     "Gentle visualization (safe place)",
# #     "Gratitude micro‑reflection",
# #     "Preparing to close (re‑orient body)",
# #     "Closing message & next‑steps",
# # ]

# # # ---------- OpenAI async client ----------
# # client = AsyncOpenAI(api_key=API_KEY)

# # SYSTEM = (
# #     "You are a skilled meditation scriptwriter. "
# #     "Write natural, human-sounding narration for voice-over. "
# #     "No timestamps, no SSML, no stage directions. "
# #     "Use short paragraphs and smooth transitions."
# # )

# # SECTION_PROMPT_TEMPLATE = """Topic: {topic}
# # Section: {heading}

# # Write this section as continuous narration, 100% self-contained (no TODOs),
# # aiming for ~{words} words. Keep consistent tone and avoid repeating the exact
# # phrases from other sections (assume they will be stitched together).
# # Do not include headings in the output—just the narration text."""

# # async def gen_section(idx: int, topic_brief: str, heading: str) -> tuple[int, str]:
# #     prompt = SECTION_PROMPT_TEMPLATE.format(
# #         topic=topic_brief, heading=heading, words=WORDS_PER_SECTION
# #     )
# #     rsp = await client.chat.completions.create(
# #         model=MODEL,
# #         temperature=0.7,
# #         messages=[
# #             {"role": "system", "content": SYSTEM},
# #             {"role": "user", "content": prompt},
# #         ],
# #     )
# #     text = rsp.choices[0].message.content.strip()
# #     return (idx, text)

# # async def generate_full_script(topic_brief: str) -> str:
# #     tasks = [gen_section(i, topic_brief, OUTLINE[i]) for i in range(N_SECTIONS)]
# #     results = await asyncio.gather(*tasks)
# #     results.sort(key=lambda x: x[0])
# #     sections = [s for _, s in results]
# #     return "\n\n".join(sections)

# # # ---------- Gradio async handler ----------
# # async def on_generate(topic_brief):
# #     start = time.perf_counter()
# #     full_script = await generate_full_script(topic_brief.strip() or DEFAULT_TOPIC)
# #     elapsed = time.perf_counter() - start

# #     words = len(full_script.split())
# #     mins = words / SPEAKING_WPM
# #     meta = (
# #         f"Words: {words}  |  Est. minutes: {mins:.1f}  |  "
# #         f"Generation time: {elapsed:.2f} sec"
# #     )
# #     return full_script, meta

# # # ---------- UI ----------
# # with gr.Blocks(title="10‑Minute Script Generator") as demo:
# #     gr.Markdown("# 10‑Minute Script Generator (Parallel, Async)")

# #     with gr.Row():
# #         topic = gr.Textbox(
# #             label="Topic / Instructions",
# #             value=DEFAULT_TOPIC,
# #             lines=6,
# #             placeholder="Describe the script you want (tone, style, structure)...",
# #         )

# #     generate_btn = gr.Button("Generate Script", variant="primary")
# #     script_out = gr.Textbox(label="Script", lines=24)
# #     info_out = gr.Textbox(label="Stats (includes response time)", interactive=False)

# #     # Async event
# #     generate_btn.click(on_generate, inputs=[topic], outputs=[script_out, info_out])

# # if __name__ == "__main__":
# #     # Tip: Gradio supports async handlers; see performance guide for concurrency options.
# #     # demo.launch(max_threads=80)  # for non-async fns; not needed here
# #     demo.launch()


# # Voice 

# import os, asyncio, math, time, tempfile, uuid, re, subprocess, shutil
# import gradio as gr
# from dotenv import load_dotenv
# from openai import AsyncOpenAI

# # -------- .env --------
# load_dotenv()
# API_KEY = os.getenv("OPENAI_API_KEY")
# if not API_KEY:
#     raise RuntimeError("OPENAI_API_KEY not found in .env")

# # -------- Config --------
# TEXT_MODEL = "gpt-4o-mini"
# TTS_MODEL  = "gpt-4o-mini-tts"
# DEFAULT_VOICE = "alloy"
# AUDIO_FMT  = "mp3"

# TARGET_MINUTES = 10
# SPEAKING_WPM   = 155
# TOTAL_WORDS    = TARGET_MINUTES * SPEAKING_WPM
# N_SECTIONS     = 10
# WORDS_PER_SECTION  = math.ceil(TOTAL_WORDS / N_SECTIONS)

# # TTS parallelization
# CHARS_PER_CHUNK = 1200          # keep well under input token limits
# MAX_CONCURRENCY = 6             # tune upward carefully (rate limits!)
# TTS_TIMEOUT_SEC = 120           # per chunk
# FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

# DEFAULT_TOPIC = (
#     "Guide a beginner through a calm mindfulness session focused on breath, "
#     "body awareness, gentle visualization, and a positive closing. "
#     "Style: warm, concrete, encouraging; short paragraphs; no timestamps, no SSML; "
#     "avoid bullet points; keep it natural to read aloud."
# )

# OUTLINE = [
#     "Opening welcome & set intention",
#     "Posture & environment setup",
#     "Initial breath awareness",
#     "Counting the breath (light focus)",
#     "Body scan (head to toes)",
#     "Handling distractions kindly",
#     "Gentle visualization (safe place)",
#     "Gratitude micro-reflection",
#     "Preparing to close (re-orient body)",
#     "Closing message & next-steps",
# ]

# SYSTEM = (
#     "You are a skilled meditation scriptwriter. "
#     "Write natural, human-sounding narration for voice-over. "
#     "No timestamps, no SSML, no stage directions. "
#     "Use short paragraphs and smooth transitions."
# )

# SECTION_PROMPT = """Topic: {topic}
# Section: {heading}

# Write this section as continuous narration, ~{words} words.
# Keep tone consistent and do not repeat exact phrases from other sections.
# Output ONLY narration text.
# """

# client = AsyncOpenAI(api_key=API_KEY)

# # -------- Text generation (parallel) --------
# async def gen_section(idx: int, topic: str, heading: str):
#     prompt = SECTION_PROMPT.format(topic=topic, heading=heading, words=WORDS_PER_SECTION)
#     rsp = await client.chat.completions.create(
#         model=TEXT_MODEL, temperature=0.7,
#         messages=[{"role":"system","content":SYSTEM},
#                   {"role":"user","content":prompt}],
#     )
#     return idx, rsp.choices[0].message.content.strip()

# async def generate_script(topic: str) -> str:
#     tasks = [gen_section(i, topic, OUTLINE[i]) for i in range(N_SECTIONS)]
#     results = await asyncio.gather(*tasks)
#     results.sort(key=lambda x: x[0])
#     return "\n\n".join([s for _, s in results])

# # -------- Helpers: chunking & ffmpeg concat --------
# _SENT_SPLIT = re.compile(r'(?<=[\.\!\?])\s+')

# def sentence_chunks(text: str, max_chars: int = CHARS_PER_CHUNK):
#     sents = _SENT_SPLIT.split(text.strip())
#     buf, total = [], 0
#     for s in sents:
#         if not s: continue
#         if total + len(s) + 1 > max_chars and buf:
#             yield " ".join(buf).strip()
#             buf, total = [s], len(s)
#         else:
#             buf.append(s); total += len(s) + 1
#     if buf:
#         yield " ".join(buf).strip()

# def concat_segments_ffmpeg(paths, out_path):
#     if len(paths) == 1:
#         shutil.copyfile(paths[0], out_path)
#         return out_path
#     # Build concat list file
#     lst = os.path.join(tempfile.gettempdir(), f"concat_{uuid.uuid4().hex}.txt")
#     with open(lst, "w", encoding="utf-8") as f:
#         for p in paths:
#             f.write(f"file '{p}'\n")
#     cmd = [
#         FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
#         "-f", "concat", "-safe", "0", "-i", lst,
#         "-c", "copy", out_path
#     ]
#     subprocess.check_call(cmd)
#     os.remove(lst)
#     return out_path

# # -------- TTS: parallel segments --------
# async def tts_one_chunk(text: str, voice: str, fmt: str, sem: asyncio.Semaphore) -> str:
#     out_path = os.path.join(tempfile.gettempdir(), f"seg_{uuid.uuid4().hex}.{fmt}")
#     async with sem:
#         try:
#             # Streaming API path (fast, reliable)
#             async with client.audio.speech.with_streaming_response.create(
#                 model=TTS_MODEL, voice=voice, input=text, response_format=fmt
#             ) as resp:
#                 await asyncio.wait_for(resp.stream_to_file(out_path), timeout=TTS_TIMEOUT_SEC)
#         except Exception:
#             # Fallback to non-streaming
#             resp = await asyncio.wait_for(
#                 client.audio.speech.create(model=TTS_MODEL, voice=voice, input=text, response_format=fmt),
#                 timeout=TTS_TIMEOUT_SEC
#             )
#             data = await resp.read()
#             with open(out_path, "wb") as f:
#                 f.write(data)
#     if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
#         raise RuntimeError("Empty TTS segment.")
#     return out_path

# async def tts_segments_parallel(full_text: str, voice: str, fmt: str) -> list[str]:
#     sem = asyncio.Semaphore(MAX_CONCURRENCY)
#     chunks = list(sentence_chunks(full_text, CHARS_PER_CHUNK))
#     tasks = [tts_one_chunk(chunks[i], voice, fmt, sem) for i in range(len(chunks))]
#     # Run with progress
#     results = await asyncio.gather(*tasks)
#     return results

# # -------- Gradio: progressive updates + final stitched MP3 --------
# async def on_generate_streaming(topic_brief: str, voice_choice: str):
#     """
#     Generator that yields progressively:
#       1) (script text, timing stats, latest_segment_path) repeatedly
#       2) At the end, the final stitched MP3 path replaces previous
#     """
#     topic = (topic_brief or "").strip() or DEFAULT_TOPIC
#     voice = (voice_choice or DEFAULT_VOICE)

#     t0 = time.perf_counter()
#     script = await generate_script(topic)
#     t_gen = time.perf_counter() - t0

#     words = len(script.split())
#     est_mins = words / SPEAKING_WPM

#     # Kick off parallel TTS
#     t1 = time.perf_counter()
#     seg_paths = []
#     for coro in asyncio.as_completed(
#         [tts_one_chunk(txt, voice, AUDIO_FMT, asyncio.Semaphore(MAX_CONCURRENCY))
#          for txt in sentence_chunks(script, CHARS_PER_CHUNK)]
#     ):
#         p = await coro
#         seg_paths.append(p)
#         # Yield the latest segment so the UI can "start playing now"
#         stats_now = f"Words: {words} | Est: {est_mins:.1f} min | Script: {t_gen:.2f}s | Segments ready: {len(seg_paths)}"
#         yield script, stats_now, p

#     tts_time = time.perf_counter() - t1

#     # Concatenate all segments (sorted by completion order is fine because we created in-order tasks; if you prefer strict order, map over original chunk indices)
#     final_path = os.path.join(tempfile.gettempdir(), f"speech_{uuid.uuid4().hex}.{AUDIO_FMT}")
#     concat_segments_ffmpeg(seg_paths, final_path)

#     stats_final = f"Words: {words} | Est: {est_mins:.1f} min | Script: {t_gen:.2f}s | TTS(stitch): {tts_time:.2f}s | Segments: {len(seg_paths)}"
#     yield script, stats_final, final_path

# # -------- UI --------
# VOICES = ["alloy","ash","ballad","coral","echo","fable","onyx","nova","sage","shimmer","verse"]

# with gr.Blocks(title="10-Minute Script → Fast MP3") as demo:
#     gr.Markdown("# 10‑Minute Script ➜ Fast, Parallel TTS (Progressive)")
#     with gr.Row():
#         topic_in = gr.Textbox(label="Topic / Instructions", value=DEFAULT_TOPIC, lines=6)
#         voice_in = gr.Dropdown(choices=VOICES, value=DEFAULT_VOICE, label="Voice")
#     btn = gr.Button("Generate Script + Audio", variant="primary")
#     script_out = gr.Textbox(label="Script", lines=22)
#     meta_out = gr.Textbox(label="Stats (timings)", interactive=False)
#     audio_out = gr.Audio(label="Audio", type="filepath")

#     # Important: use a generator function
#     btn.click(on_generate_streaming, inputs=[topic_in, voice_in],
#               outputs=[script_out, meta_out, audio_out])

# if __name__ == "__main__":
#     demo.launch()


# --- UPDATED SCRIPT (drop-in) ---

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
