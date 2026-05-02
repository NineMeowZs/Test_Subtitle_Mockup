"""transcriber.py – Whisper speech-to-text + SRT generation"""

import os
import sys

# ── ให้ Python หา ffmpeg เองผ่าน imageio-ffmpeg ────────────────────────────
try:
    import imageio_ffmpeg
    _ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass  # ถ้าหาไม่เจอก็ใช้ PATH ของระบบตามปกติ

import whisper
import textwrap
from subtitle_config import SubtitleStyle


def _extract_audio_numpy(video_path: str) -> "np.ndarray":
    """
    แยก audio จากวิดีโอโดยใช้ imageio_ffmpeg binary โดยตรง
    (ไม่ต้องการ ffmpeg ใน PATH)
    คืนค่า numpy float32 array ที่ sample rate 16000 Hz mono
    """
    import subprocess
    import numpy as np
    import imageio_ffmpeg

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y", "-i", video_path,
        "-vn",                   # ไม่เอาวิดีโอ
        "-acodec", "pcm_s16le",  # raw PCM 16-bit
        "-ar", "16000",          # 16 kHz
        "-ac", "1",              # mono
        "-f", "s16le",           # raw format
        "pipe:1",                # ส่งออก stdout
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {proc.stderr.decode(errors='ignore')[:300]}")

    audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return audio


def transcribe_video(video_path: str, model_size: str = "base", progress_cb=None) -> list[dict]:
    """
    ถอดเสียงจากวิดีโอด้วย Whisper
    แยก audio ผ่าน imageio_ffmpeg โดยตรง ไม่ต้องการ ffmpeg ใน PATH
    """
    if progress_cb:
        progress_cb("กำลังแยกเสียงจากวิดีโอ …")

    audio = _extract_audio_numpy(video_path)

    if os.path.isdir(model_size):
        if progress_cb:
            progress_cb("กำลังโหลดโมเดล Custom (Transformers) …")
        import torch
        from transformers import pipeline, AutoConfig, AutoTokenizer, AutoFeatureExtractor
        
        device = 0 if torch.cuda.is_available() else -1
        
        # Try to detect the base model name to load the processor correctly
        base_model = "openai/whisper-small"
        try:
            config = AutoConfig.from_pretrained(model_size)
            if hasattr(config, "encoder_layers"):
                if config.encoder_layers == 4: base_model = "openai/whisper-tiny"
                elif config.encoder_layers == 6: base_model = "openai/whisper-base"
                elif config.encoder_layers == 12: base_model = "openai/whisper-small"
                elif config.encoder_layers == 24: base_model = "openai/whisper-medium"
                elif config.encoder_layers == 32: base_model = "openai/whisper-large"
                
            # If _name_or_path exists and is not a local folder, use it
            if hasattr(config, "_name_or_path") and config._name_or_path:
                if not os.path.exists(config._name_or_path):
                    base_model = config._name_or_path
        except: pass

        try:
            tok = AutoTokenizer.from_pretrained(base_model)
            feat = AutoFeatureExtractor.from_pretrained(base_model)
            pipe = pipeline("automatic-speech-recognition", model=model_size, tokenizer=tok, feature_extractor=feat, device=device)
        except Exception as e:
            raise RuntimeError(f"ไม่สามารถโหลด Tokenizer ของ {base_model} ได้: {e}")
            
        if progress_cb:
            progress_cb("กำลังดำเนินการถอดเสียง (Custom Model) …")
            
        res = pipe(audio, chunk_length_s=30, return_timestamps=True)
        segments = []
        for chunk in res.get("chunks", []):
            start, end = chunk["timestamp"]
            if end is None:
                end = start + 2.0
            segments.append({
                "start": start,
                "end": end,
                "text": chunk["text"]
            })
    else:
        if progress_cb:
            progress_cb("กำลังโหลดโมเดล Whisper …")

        model = whisper.load_model(model_size)

        if progress_cb:
            progress_cb("กำลังดำเนินการถอดเสียง …")

        result = model.transcribe(
            audio,
            task="transcribe",
            language="th",
            no_speech_threshold=0.3,
            condition_on_previous_text=True,
            word_timestamps=True,
            initial_prompt="ภาษาไทย Thai language subtitle transcription",
        )
        segments = result.get("segments", [])

    if progress_cb:
        progress_cb(f"ถอดเสียงสำเร็จ! ได้ {len(segments)} ประโยค")

    return segments




def wrap_segment(text: str, max_chars: int, max_lines: int) -> str:
    """Word-wrap *text* to fit subtitle style constraints."""
    lines = textwrap.wrap(text.strip(), width=max_chars)
    lines = lines[:max_lines]
    return "\n".join(lines)


def segments_to_srt(segments: list[dict], style: SubtitleStyle) -> str:
    """Convert Whisper segments to SRT string with word-wrap applied."""
    def fmt_time(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    lines = []
    for i, seg in enumerate(segments, 1):
        text = wrap_segment(seg["text"], style.max_chars_per_line, style.max_lines)
        lines.append(str(i))
        lines.append(f"{fmt_time(seg['start'])} --> {fmt_time(seg['end'])}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def save_srt(segments: list[dict], style: SubtitleStyle, output_path: str):
    """Write SRT file to disk."""
    srt_content = segments_to_srt(segments, style)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    return output_path
