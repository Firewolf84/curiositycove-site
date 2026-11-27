#!/usr/bin/env python3
"""Records the read-aloud voice for Curiosity Cove Learning (learn/).

Reads learn/voice/lines.json ({hash: sentence}) and makes learn/voice/<hash>.mp3 for every
sentence that doesn't have a recording yet, then writes learn/voice/index.json (the list the
app checks before playing a recording; anything missing is read by the device's own voice).
Old recordings no longer used are removed.

Voice: en-IE-EmilyNeural (the same Irish English voice as BOLT's Little Lab). Language-lesson lines
("af:…", "es:…", "fr:…", "zh:…", "pt:…") use a native voice: Adri (Afrikaans), Elvira (Spanish),
Denise (French), Xiaoxiao (Mandarin) and Raquel (Portuguese).
  * If the AZURE_SPEECH_KEY secret is set (with AZURE_SPEECH_REGION), it uses your Azure Speech account.
  * Otherwise it uses the free edge-tts package (the Microsoft Edge read-aloud service).
Recordings are squeezed to 32 kbps mono with ffmpeg (when available) to keep the site small.

There are thousands of lines, so each run stops after LEARN_VOICE_MINUTES (default 40) and the
next run carries on where it left off.

Run:  python3 tools/make_learn_voice.py      (needs internet; GitHub Actions runs it on every push and daily)
"""
import asyncio, json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from xml.sax.saxutils import escape

VOICE = "en-IE-EmilyNeural"
# Language lessons: lines written "af:Goeie môre" are read by a native speaker's voice for that language.
LANG_VOICES = {"af": ("af-ZA-AdriNeural", "af-ZA"), "es": ("es-ES-ElviraNeural", "es-ES"), "fr": ("fr-FR-DeniseNeural", "fr-FR"),
               "zh": ("zh-CN-XiaoxiaoNeural", "zh-CN"), "pt": ("pt-PT-RaquelNeural", "pt-PT")}
LANG_RATE = "-12%"   # a little slower, so learners can hear every sound


def voice_for(text):
    """Returns (text to say, voice, xml:lang, rate) for a line from lines.json."""
    if len(text) > 3 and text[2] == ":" and text[:2] in LANG_VOICES:
        v, lang = LANG_VOICES[text[:2]]
        return text[3:], v, lang, LANG_RATE
    return text, VOICE, "en-IE", RATE
RATE = "-3%"
PITCH = "+0Hz"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "learn", "voice")
BUDGET = float(os.environ.get("LEARN_VOICE_MINUTES", "40")) * 60
WORKERS = int(os.environ.get("LEARN_VOICE_WORKERS", "4"))
FFMPEG = shutil.which("ffmpeg")


def azure(text, path, key, region):
    text, voice, lang, rate = voice_for(text)
    ssml = (f'<speak version="1.0" xml:lang="{lang}"><voice name="{voice}">'
            f'<prosody rate="{rate}" pitch="{PITCH}">{escape(text)}</prosody></voice></speak>')
    req = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode(),
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3", "User-Agent": "curiositycove"})
    with urllib.request.urlopen(req, timeout=60) as r:
        open(path, "wb").write(r.read())


def squeeze(src, dst):
    if FFMPEG:
        r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "24000", "-b:a", "32k", dst])
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 500:
            return
    shutil.copyfile(src, dst)


async def record(text, path, key, region):
    tmp = tempfile.mktemp(suffix=".mp3")
    try:
        for attempt in range(3):  # the service sometimes drops a request; try again
            try:
                if key:
                    await asyncio.to_thread(azure, text, tmp, key, region)
                else:
                    import edge_tts
                    say, voice, _, rate = voice_for(text)
                    await edge_tts.Communicate(say, voice, rate=rate, pitch=PITCH).save(tmp)
                if os.path.getsize(tmp) < 1000:
                    raise RuntimeError("empty recording")
                break
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(3)
        await asyncio.to_thread(squeeze, tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


async def main():
    lines = json.load(open(os.path.join(ROOT, "lines.json"), encoding="utf-8"))
    key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION", "northeurope")
    todo = [(h, t) for h, t in lines.items()
            if not (os.path.exists(os.path.join(ROOT, h + ".mp3")) and os.path.getsize(os.path.join(ROOT, h + ".mp3")) > 500)]
    todo.sort(key=lambda x: voice_for(x[1])[1] == VOICE)  # language-lesson lines first
    start, stats, sem = time.time(), {"made": 0, "failed": 0, "skipped": 0}, asyncio.Semaphore(WORKERS)

    async def one(h, text):
        async with sem:
            if time.time() - start > BUDGET:
                stats["skipped"] += 1
                return
            path = os.path.join(ROOT, h + ".mp3")
            try:
                await record(text, path, key, region)
                stats["made"] += 1
            except Exception as e:
                stats["failed"] += 1
                print("could not record:", text, "-", e, file=sys.stderr)
                if os.path.exists(path):
                    os.remove(path)

    await asyncio.gather(*(one(h, t) for h, t in todo))
    for f in os.listdir(ROOT):  # tidy recordings that are no longer used
        if f.endswith(".mp3") and f[:-4] not in lines:
            os.remove(os.path.join(ROOT, f))
    have = {h: 1 for h in lines if os.path.exists(os.path.join(ROOT, h + ".mp3"))}
    json.dump(have, open(os.path.join(ROOT, "index.json"), "w"), separators=(",", ":"))
    print(f"recorded {stats['made']} new, {stats['failed']} failed, {stats['skipped']} left for the next run; "
          f"{len(have)}/{len(lines)} lines have a voice")


if __name__ == "__main__":
    asyncio.run(main())
