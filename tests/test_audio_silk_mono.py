from types import SimpleNamespace
from voice import audio_convert as audio

class Segment:
    frame_rate = 44100
    duration_seconds = 2
    def __init__(self, channels=2):
        self.channels = channels
    def set_sample_width(self, width):
        assert width == 2
        return self
    def set_frame_rate(self, rate):
        assert rate == 44100
        return self
    def set_channels(self, channels):
        return Segment(channels)
    @property
    def raw_data(self):
        return b'mono-pcm' if self.channels == 1 else b'interleaved-stereo-pcm'

def test_silk_encoder_receives_mono_pcm(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(audio, '_pydub_available', True)
    monkeypatch.setattr(audio, 'AudioSegment', SimpleNamespace(from_file=lambda path: Segment()))
    def encode(pcm, **kwargs):
        calls.append((pcm, kwargs))
        return b'silk'
    monkeypatch.setattr(audio, 'pysilk', SimpleNamespace(encode=encode), raising=False)
    destination = tmp_path / 'out.silk'
    assert audio.any_to_sil('stereo.wav', str(destination)) == 2000
    assert calls == [(b'mono-pcm', {'data_rate': 44100, 'sample_rate': 44100})]
    assert destination.read_bytes() == b'silk'
