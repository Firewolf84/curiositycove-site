#!/usr/bin/env python3
"""Records BOLT's voice for BOLT's Little Lab (junior/).

Two games get a voice:
  junior/ (BOLT's Little Lab): every sentence is listed in junior/voice/lines.json.
  play/ (Robot Lab Breakout): play/voice/lines.json (BOLT's lines and the Robot Lab levels), plus the
      stories, instructions and hints of every level in play/worlds.json and every daily in daily.json.
For each game it makes voice/<hash>.mp3 for every sentence without a recording, then writes
voice/index.json (the list the game checks before playing a recording). Unused recordings are removed.

Voice: en-IE-EmilyNeural (Irish English, female).
  * If the AZURE_SPEECH_KEY secret is set (with AZURE_SPEECH_REGION, e.g. "northeurope"),
    it uses your own Azure Speech account (free tier: 500,000 characters a month).
  * Otherwise it uses the free edge-tts package (the Microsoft Edge read-aloud service).

Run:  python3 tools/make_voice.py            (needs internet; GitHub Actions runs it on every push)
"""
import asyncio, json, os, sys, time, urllib.request
from xml.sax.saxutils import escape

VOICE = "en-IE-EmilyNeural"
RATE = "-6%"      # a touch slower for 5-8 year olds
PITCH = "+4Hz"    # a little brighter
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def vhash(t):
    """FNV-1a over UTF-16 code units, the same as vhash() in the games."""
    t = t.strip(); h = 0x811c9dc5; b = t.encode("utf-16-le")
    for i in range(0, len(b), 2):
        h = ((h ^ (b[i] | b[i + 1] << 8)) * 16777619) & 0xffffffff
    return f"{h:08x}"


def level_lines(L):
    """What Robot Lab Breakout reads aloud for one level: story, lock instructions, hints."""
    out = [L.get("story", "")]
    for k in L.get("locks", []):
        out.append((k.get("d") or {}).get("intro", ""))
        out += k.get("hints", [])
    out += (L.get("final") or {}).get("hints", [])
    return [t.strip() for t in out if isinstance(t, str) and t.strip()]


def play_lines():
    lines = dict(json.load(open(os.path.join(SITE, "play", "voice", "lines.json"), encoding="utf-8")))
    try:
        for w in json.load(open(os.path.join(SITE, "play", "worlds.json"), encoding="utf-8"))["worlds"]:
            for L in w.get("levels", []):
                for t in level_lines(L): lines[vhash(t)] = t
    except FileNotFoundError: pass
    try:
        for L in json.load(open(os.path.join(SITE, "daily.json"), encoding="utf-8")):
            for t in level_lines(L): lines[vhash(t)] = t
    except FileNotFoundError: pass
    return lines


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


def record(ROOT, lines):
    key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION", "northeurope")
    made = failed = 0
    for h, text in lines.items():
        path = os.path.join(ROOT, h + ".mp3")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        try:
            for attempt in range(3):  # the service sometimes drops a request; try again
                try:
                    if key: azure(text, path, key, region)
                    else: asyncio.run(edge(text, path))
                    if os.path.getsize(path) < 1000: raise RuntimeError("empty recording")
                    break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(3)
            made += 1
        except Exception as e:
            failed += 1
            print("could not record:", text, "-", e, file=sys.stderr)
            if os.path.exists(path): os.remove(path)
    for f in os.listdir(ROOT):  # tidy recordings that are no longer used
        if f.endswith(".mp3") and f[:-4] not in lines: os.remove(os.path.join(ROOT, f))
    have = {h: 1 for h in lines if os.path.exists(os.path.join(ROOT, h + ".mp3"))}
    json.dump(have, open(os.path.join(ROOT, "index.json"), "w"), separators=(",", ":"))
    print(f"{os.path.basename(os.path.dirname(ROOT))}: recorded {made} new, {failed} failed, {len(have)}/{len(lines)} lines have a voice")


def main():
    record(os.path.join(SITE, "junior", "voice"), json.load(open(os.path.join(SITE, "junior", "voice", "lines.json"), encoding="utf-8")))
    record(os.path.join(SITE, "play", "voice"), play_lines())


if __name__ == "__main__":
    main()
