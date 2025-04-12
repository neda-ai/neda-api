import os
from io import BytesIO

import librosa
import numpy as np
import parselmouth
import soundfile
from pydub import AudioSegment
from fastapi_mongo_base.utils import texttools


def calculate_voice_pitch_parselmouth(audio: np.ndarray, sr: int) -> np.ndarray:
    sound = parselmouth.Sound(audio, sampling_frequency=sr)

    pitch_obj = sound.to_pitch(time_step=0.01)  # 100Hz frame rate like RMVPE

    pitch_values = pitch_obj.selected_array["frequency"]  # In Hz

    # Replace unvoiced frames (0 Hz) with NaN or interpolation
    pitch_values[pitch_values == 0] = np.nan
    return pitch_values


def clean_pitch_values(pitch_values: np.ndarray) -> np.ndarray:
    # Remove NaNs
    valid_pitch = pitch_values[~np.isnan(pitch_values)]

    if len(valid_pitch) == 0:
        return pitch_values  # all NaN, nothing to do

    # Compute quartiles
    q1 = np.percentile(valid_pitch, 25)
    q3 = np.percentile(valid_pitch, 75)

    # Midpoint between Q1 and Q3
    q_average = (q1 + q3) / 2

    mid_range_values = valid_pitch[(valid_pitch >= q1) & (valid_pitch <= q3)]

    return {
        "min": np.nanmin(pitch_values),
        "max": np.nanmax(pitch_values),
        "average": np.nanmean(pitch_values),
        "median": np.nanmedian(pitch_values),
        "q1": q1,
        "q3": q3,
        "q_average": q_average,
        "robust_average": np.nanmean(mid_range_values),
        "robust_median": np.nanmedian(mid_range_values),
    }


def calculate_voice_pitch_crepe(audio: np.ndarray, sr: int) -> np.ndarray:
    import crepe

    # crepe requires mono, float32, 16kHz
    if sr != 16000:
        raise ValueError("CREPE requires 16kHz audio. Resample first.")

    if audio.ndim > 1:
        audio = audio.mean(axis=1)  # convert to mono

    audio = audio.astype(np.float32)

    _, freqs, confidence, _ = crepe.predict(audio, sr, viterbi=True, step_size=10)

    # Optional: mask low-confidence
    freqs[confidence < 0.5] = np.nan
    return freqs


def get_voice_array(audio_bytes: BytesIO) -> np.ndarray:
    audio_bytes.seek(0)
    try:
        # Try to read directly with soundfile
        y, sr = soundfile.read(audio_bytes)
    except Exception as e:
        # If soundfile fails, try with pydub to convert to WAV format
        audio_bytes.seek(0)
        audio_segment = AudioSegment.from_file(audio_bytes)
        # Convert to WAV format in memory
        wav_io = BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        y, sr = soundfile.read(wav_io)

    if len(y.shape) > 1:
        y = np.mean(y, axis=1)

    y = y.astype(np.float32)

    # Resample to 16kHz for crepe
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        sr = 16000

    return y, sr


def get_voice_pitch_crepe(audio_bytes: BytesIO) -> np.ndarray:
    y, sr = get_voice_array(audio_bytes)
    pitch_values = calculate_voice_pitch_crepe(y, sr)
    return clean_pitch_values(pitch_values)


def get_voice_pitch_parselmouth(audio_bytes: BytesIO) -> np.ndarray:
    y, sr = get_voice_array(audio_bytes)
    pitch_values = calculate_voice_pitch_parselmouth(y, sr)
    return clean_pitch_values(pitch_values)


def calculate_pitch_shift(source_pitch: float, target_pitch: float) -> float:
    """
    Calculate the optimal pitch shift for RVC conversion.

    Args:
        source_pitch: The speaking pitch of the source voice
        target_pitch: The speaking pitch of the target voice model

    Returns:
        float: Recommended pitch shift value for RVC
    """
    if source_pitch == 0:
        return 0

    # Calculate semitone difference
    pitch_shift = 12 * np.log2(target_pitch / source_pitch)

    # Limit the shift to a reasonable range (-12 to +12 semitones)
    pitch_shift = np.clip(pitch_shift, -12, 12)

    return float(pitch_shift)


def calculate_pitch_shift_log(source_pitch: float, target_pitch_log: float) -> float:
    """
    Calculate the optimal pitch shift for RVC conversion.

    Args:
        source_pitch: The speaking pitch of the source voice
        target_pitch: The speaking pitch of the target voice model

    Returns:
        float: Recommended pitch shift value for RVC
    """
    if source_pitch == 0 or target_pitch_log == 0:
        return 0

    # Calculate semitone difference
    pitch_shift = 12 * (target_pitch_log - np.log2(source_pitch))

    # Limit the shift to a reasonable range (-12 to +12 semitones)
    pitch_shift = np.clip(pitch_shift, -12, 12)

    return float(pitch_shift)


def get_duration(audio: BytesIO):
    try:
        # First try with librosa
        y, sr = librosa.load(audio)
        duration_seconds = librosa.get_duration(y=y, sr=sr)
        return duration_seconds
    except Exception as e:
        # If librosa fails, try with pydub
        audio.seek(0)
        try:
            audio_segment = AudioSegment.from_file(audio)
            return len(audio_segment) / 1000.0  # Convert milliseconds to seconds
        except Exception as e2:
            # If both methods fail, log the error and return a default duration
            import logging

            logging.error(f"Failed to get audio duration: {e2}")
            return 60.0  # Default to 1 minute if we can't determine duration


def create_rvc_conversion(
    audio: str,
    model_url: str,
    pitch: float = 0,
    webhook_url: str = None,
):
    import replicate

    input = {
        "protect": 0.5,
        "rvc_model": "CUSTOM",  # to use custom = CUSTOM
        "index_rate": 0.5,
        "input_audio": audio,
        "pitch_change": pitch,
        "rms_mix_rate": 0.3,
        "filter_radius": 3,
        "custom_rvc_model_download_url": model_url,
        "output_format": "wav",
    }

    rep = replicate.predictions.create(
        version="d18e2e0a6a6d3af183cc09622cebba8555ec9a9e66983261fc64c8b1572b7dce",
        input=input,
        webhook=webhook_url,
        webhook_events_filter=["completed"],
    )

    return rep.id


def create_rvc_conversion_runpod(
    audio: str,
    model_url: str,
    pitch: float = 0,
    webhook_url: str = None,
):
    import httpx

    api_key = os.getenv("RUNPOD_API_KEY")
    runpod_id = os.getenv("RUNPOD_ID")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    base_url = f"https://api.runpod.ai/v2/{runpod_id}"

    data = {
        "input": {
            "protect": 0.5,
            "rvc_model": "CUSTOM",
            "index_rate": 0.5,
            "input_audio": audio,
            "pitch_change": pitch,
            "rms_mix_rate": 0.3,
            "filter_radius": 3,
            "output_format": "wav",
            "custom_rvc_model_download_url": model_url,
            "webhook_url": webhook_url,
        }
    }

    with httpx.Client(headers=headers) as client:
        response = client.post(f"{base_url}/run", json=data)
        return response.json().get("id")


def get_rvc_conversion_runpod_status(job_id: str):
    import httpx

    api_key = os.getenv("RUNPOD_API_KEY")
    runpod_id = os.getenv("RUNPOD_ID")

    base_url = f"https://api.runpod.ai/v2/{runpod_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    response = httpx.get(f"{base_url}/status/{job_id}")
    return response.json()
