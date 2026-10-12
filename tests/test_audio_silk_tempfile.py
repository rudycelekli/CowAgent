from pathlib import Path
from types import SimpleNamespace
import pytest
from voice import audio_convert as audio

@pytest.mark.parametrize('fail_decode', [False, True])
def test_conversion_preserves_existing_sibling_and_cleans_its_temp(tmp_path, monkeypatch, fail_decode):
    source = tmp_path / 'voice.silk'
    source.write_bytes(b'silk')
    sibling = tmp_path / 'voice.silk.wav'
    sibling.write_bytes(b'important-existing-audio')
    decoded = []
    monkeypatch.setattr(audio, '_pydub_available', True)
    def decode(src, destination):
        decoded.append(Path(destination))
        Path(destination).write_bytes(b'partial-wav')
        if fail_decode:
            raise RuntimeError('decode failed')
    monkeypatch.setattr(audio, 'sil_to_wav', decode)
    monkeypatch.setattr(audio, 'AudioSegment', SimpleNamespace(from_file=lambda path: SimpleNamespace(export=lambda target, format: Path(target).write_bytes(b'mp3'))))
    target = tmp_path / 'target.mp3'
    if fail_decode:
        with pytest.raises(RuntimeError, match='decode failed'):
            audio.any_to_mp3(str(source), str(target))
    else:
        audio.any_to_mp3(str(source), str(target))
        assert target.read_bytes() == b'mp3'
    assert sibling.read_bytes() == b'important-existing-audio'
    assert decoded[0] != sibling
    assert not decoded[0].exists()
    assert source.read_bytes() == b'silk'
