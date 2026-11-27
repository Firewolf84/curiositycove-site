#!/usr/bin/env python3
"""Records BOLT's voice for BOLT's Little Lab (junior/).

Reads junior/voice/lines.json ({hash: sentence}) and makes junior/voice/<hash>.mp3
for every sentence that doesn't have a recording yet, then writes junior/voice/index.json
(the list the game checks before playing a recording). Old recordings no longer used are removed.

Voice: en-IE-EmilyNeural (Irish English, female).
  * If the AZURE_SPEECH_KEY secret is set (with AZURE_SPEECH_REGION, e.g. "northeurope"),
    it uses your own Azure Speech account (free tier: 500,000 characters a month).
  * Otherwise it uses the free edge-tts package (the Microsoft Edge read-aloud service).

Run:  python3 tools/make_voice.py            (needs internet; GitHub Actions runs it on every push)
"""
import asyncio, json, os, sys, urllib.request
from xml.sax.saxutils import escape

VOICE = "en-IE-EmilyNeural"
RATE = "-6%"      # a touch slower for 5-8 year olds
PITCH = "+4Hz"    # a little brighter
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "junior", "voice")


def azure(text, path, key, region):
    ssml = (f'<speak version="1.0" xml:lang="en-IE"><voice name="{VOICE}">'
            f'<prosody rate="{RATE}" pitch="{PITCH}">{escape(text)}</prosody></voice></speak>')
    req = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode(),
        headers={"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3", "User-Agent": "curiositycove"})
    with urllib.request.urlopen(req, timeout=60) as r:
        open(path, "wb").write(r.read())


async def edge(text, path):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(path)


def main():
    lines = json.load(open(os.path.join(ROOT, "lines.json"), encoding="utf-8"))
    key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION", "northeurope")
    made = failed = 0
    for h, text in lines.items():
        path = os.path.join(ROOT, h + ".mp3")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        try:
            if key: azure(text, path, key, region)
            else: asyncio.run(edge(text, path))
            if os.path.getsize(path) < 1000: raise RuntimeError("empty recording")
            made += 1
        except Exception as e:
            failed += 1
            print("could not record:", text, "-", e, file=sys.stderr)
            if os.path.exists(path): os.remove(path)
    for f in os.listdir(ROOT):  # tidy recordings that are no longer used
        if f.endswith(".mp3") and f[:-4] not in lines: os.remove(os.path.join(ROOT, f))
    have = {h: 1 for h in lines if os.path.exists(os.path.join(ROOT, h + ".mp3"))}
    json.dump(have, open(os.path.join(ROOT, "index.json"), "w"), separators=(",", ":"))
    print(f"recorded {made} new, {failed} failed, {len(have)}/{len(lines)} lines have a voice")


if __name__ == "__main__":
    main()
