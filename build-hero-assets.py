#!/usr/bin/env python3
"""Turn the Gemini intro video into a seamless looping hero clip.

Usage: python3 build-hero-assets.py intro.mp4 [out_dir]
- Detects the character against the white background and crops a centred 4:5 frame (head to toe).
- Whitens the backdrop so it blends into the page with mix-blend-mode: multiply.
- Cross-fades the last 0.5 s into the first 0.5 s (video with xfade, audio sample-accurately in numpy).
- Exports hero.mp4 (H.264 + AAC) and hero.webm (VP9 + Opus).
"""
import json, subprocess, sys, os
import numpy as np

src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else '.'
XF = 0.5; SR = 48000

def run(*a, **k): return subprocess.run(a, check=True, capture_output=True, **k)
info = json.loads(run('ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', src).stdout)
v = next(s for s in info['streams'] if s['codec_type'] == 'video')
W, H = int(v['width']), int(v['height'])
dur = min(float(info['format']['duration']), 10.0)
fps_n, fps_d = map(int, v['r_frame_rate'].split('/')); fps = fps_n / fps_d
has_audio = any(s['codec_type'] == 'audio' for s in info['streams'])
print(f'{W}x{H} {fps:.2f}fps {dur:.2f}s audio={has_audio}')

# 1. find the person: union of non-background pixels over sampled frames
xs0, xs1, ys0, ys1 = W, 0, H, 0
for t in np.linspace(0.3, dur - 0.3, 8):
    raw = run('ffmpeg', '-v', 'error', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-').stdout
    a = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(int)
    bg = np.median(np.concatenate([a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3)]), axis=0)
    m = np.abs(a - bg).sum(axis=2) > 60
    m[int(H * 0.97):] = False
    ys, xs = np.where(m)
    if len(xs):
        xs0, xs1 = min(xs0, np.percentile(xs, .5)), max(xs1, np.percentile(xs, 99.5))
        ys0, ys1 = min(ys0, np.percentile(ys, .2)), max(ys1, np.percentile(ys, 99.8))
cx = int((xs0 + xs1) / 2)
ch = min(H, int((ys1 - ys0) * 1.12)); ch -= ch % 2
cw = int(ch * 0.8); cw -= cw % 2
cy0 = max(0, min(H - ch, int(ys0 - (ch - (ys1 - ys0)) * 0.45)))
cx0 = max(0, min(W - cw, cx - cw // 2))
print('crop', cw, ch, cx0, cy0)
vf_base = f'crop={cw}:{ch}:{cx0}:{cy0},scale=768:960:flags=lanczos,colorlevels=rimax=0.90:gimax=0.90:bimax=0.90,format=yuv420p'

# 2. video loop: xfade tail into head
loopd = dur - XF
vfilter = (f"[0:v]trim=0:{dur},setpts=PTS-STARTPTS,{vf_base},split[a][b];"
           f"[a]trim=0:{XF},setpts=PTS-STARTPTS[head];"
           f"[b]trim={XF}:{dur},setpts=PTS-STARTPTS[body];"
           f"[body][head]xfade=transition=fade:duration={XF}:offset={dur - 2 * XF}[v]")
run('ffmpeg', '-y', '-v', 'error', '-i', src, '-filter_complex', vfilter, '-map', '[v]', '-an', '-r', f'{fps:.3f}', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '/tmp/loop_v.mp4')

# 3. audio loop: sample-accurate crossfade in numpy
if has_audio:
    pcm = np.frombuffer(run('ffmpeg', '-v', 'error', '-i', src, '-t', f'{dur}', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-').stdout, np.float32).reshape(-1, 2).copy()
    n = int(XF * SR); total = int(dur * SR); pcm = pcm[:total]
    head, body = pcm[:n], pcm[n:]
    ramp = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    body[-n:] = body[-n:] * (1 - ramp) + head * ramp
    loop_a = body[: int(loopd * SR)]
    loop_a.astype(np.float32).tofile('/tmp/loop_a.f32')

    def mux(args, outname):
        run('ffmpeg', '-y', '-v', 'error', '-i', '/tmp/loop_v.mp4', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '/tmp/loop_a.f32', '-map', '0:v', '-map', '1:a', '-shortest', *args, os.path.join(out, outname))
else:
    def mux(args, outname):
        run('ffmpeg', '-y', '-v', 'error', '-i', '/tmp/loop_v.mp4', '-map', '0:v', *[x for x in args if not x.startswith(('-c:a', '-b:a')) and x not in ('aac', 'libopus', '96k', '80k')], os.path.join(out, outname))

mux(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'slow', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart'], 'hero.mp4')
mux(['-c:v', 'libvpx-vp9', '-crf', '36', '-b:v', '0', '-row-mt', '1', '-c:a', 'libopus', '-b:a', '80k'], 'hero.webm')

# 4. poster frame
run('ffmpeg', '-y', '-v', 'error', '-ss', '0.2', '-i', os.path.join(out, 'hero.mp4'), '-frames:v', '1', '-q:v', '3', os.path.join(out, 'hero-poster.jpg'))
for f in ('hero.mp4', 'hero.webm', 'hero-poster.jpg'):
    print(f, os.path.getsize(os.path.join(out, f)) // 1024, 'KB')
