import logging
from io import BytesIO

import librosa
import numpy as np
import pydub


# @basic.try_except_wrapper
def calculate_voice_pitch(voice: BytesIO):
    """
    Calculate the average pitch (fundamental frequency) of a voice recording using RMVPE.

    Args:
        voice: BytesIO object containing audio data (supports wav, mp3, ogg formats)

    Returns:
        dict: Contains pitch statistics (mean, min, max, std)
    """

    try:
        import onnxruntime

        logging.info("started")

        # Convert audio to numpy array
        audio = pydub.AudioSegment.from_file(voice)
        audio = audio.set_channels(1)  # Convert to mono
        audio = audio.set_frame_rate(16000)  # Resample to 16kHz
        samples = np.array(audio.get_array_of_samples(), dtype=np.float64)
        samples = samples / samples.max()  # Normalize to [-1, 1]

        def get_frames(x, frame_size=2048, hop_size=160):
            # Frame the signal into overlapping frames
            num_frames = 1 + (len(x) - frame_size) // hop_size
            frames = np.zeros((num_frames, frame_size))
            for i in range(num_frames):
                frames[i] = x[i * hop_size : i * hop_size + frame_size]
            return frames

        def compute_dft(frames):
            # Compute DFT for each frame
            window = np.hanning(frames.shape[1])
            windowed = frames * window
            fft = np.fft.rfft(windowed)
            # Take only first 1024 frequency bins to match model's expected input
            return fft[:, :1024]

        def resize_spec(spec, target_length=128):
            # Resize spectrogram to match expected input size
            from scipy.interpolate import interp1d

            current_length = spec.shape[0]
            if current_length == target_length:
                return spec

            x_old = np.linspace(0, 1, current_length)
            x_new = np.linspace(0, 1, target_length)
            f = interp1d(x_old, spec, axis=0)
            return f(x_new)

        def resize_spec(spec, target_length=128):
            # Resize spectrogram to match expected input size
            from scipy.interpolate import interp1d

            current_length = spec.shape[0]
            if current_length == target_length:
                return spec

            x_old = np.linspace(0, 1, current_length)
            x_new = np.linspace(0, 1, target_length)
            f = interp1d(x_old, spec, axis=0)
            return f(x_new)

        logging.info("Calculating pitch")

        # Frame the audio
        frames = get_frames(samples)

        # Compute spectral features
        spec = np.abs(compute_dft(frames))

        # Resize to match model's expected input size
        spec = resize_spec(spec, target_length=128)

        # Add batch dimension and channel dimension
        spec = spec[np.newaxis, :, :]  # Shape becomes (1, 128, features)

        logging.info(f"Spec shape: {spec.shape}")

        # Load RMVPE ONNX model
        session = onnxruntime.InferenceSession("rmvpe.onnx")

        # Single inference instead of batching
        input_name = session.get_inputs()[0].name
        input_data = {input_name: spec.astype(np.float32)}

        # Run inference
        output = session.run(None, input_data)
        f0 = output[0]  # Assuming first output is pitch

        # Filter out unreliable predictions
        f0 = f0[f0 > 50.0]  # Remove very low frequencies
        f0 = f0[f0 < 800.0]  # Remove very high frequencies

        if len(f0) == 0:
            return {"mean": 0, "min": 0, "max": 0, "std": 0}

        return {
            "mean": float(np.mean(f0)),
            "min": float(np.min(f0)),
            "max": float(np.max(f0)),
            "std": float(np.std(f0)),
        }

    except Exception as e:
        import traceback

        traceback_str = "".join(traceback.format_tb(e.__traceback__))
        logging.error(f"Error calculating pitch: \n\n{traceback_str}\n\n{str(e)}")
        return {"mean": 0, "min": 0, "max": 0, "std": 0}


def calculate_pitch_shift(source_pitch: float, target_pitch: float) -> float:
    """
    Calculate the optimal pitch shift for RVC conversion.

    Args:
        source_pitch: The speaking pitch of the source voice
        target_pitch: The speaking pitch of the target voice model

    Returns:
        float: Recommended pitch shift value for RVC
    """
    if source_pitch == 0 or target_pitch == 0:
        return 0

    # Calculate semitone difference
    pitch_shift = 12 * np.log2(target_pitch / source_pitch)

    # Limit the shift to a reasonable range (-12 to +12 semitones)
    pitch_shift = np.clip(pitch_shift, -12, 12)

    return float(pitch_shift)


def get_duration(audio: BytesIO):
    y, sr = librosa.load(audio)
    duration_seconds = librosa.get_duration(y=y, sr=sr)
    return duration_seconds


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
