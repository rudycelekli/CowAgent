import pytest
from voice import audio_convert as audio

@pytest.mark.parametrize('method, suffix', [('any_to_mp3', '.mp3'), ('any_to_wav', '.wav'), ('any_to_sil', '.silk'), ('any_to_amr', '.amr')])
def test_same_format_copy_needs_no_decoder(tmp_path, monkeypatch, method, suffix):
    monkeypatch.setattr(audio, '_pydub_available', False)
    source = tmp_path / ('source' + suffix)
    target = tmp_path / ('target' + suffix)
    source.write_bytes(b'already-encoded-audio')
    getattr(audio, method)(str(source), str(target))
    assert target.read_bytes() == source.read_bytes()

@pytest.mark.parametrize('method', ['any_to_mp3', 'any_to_wav', 'any_to_sil', 'any_to_amr'])
def test_conversion_still_requires_decoder(monkeypatch, method):
    monkeypatch.setattr(audio, '_pydub_available', False)
    with pytest.raises(ImportError, match='pydub'):
        getattr(audio, method)('source.ogg', 'target')
