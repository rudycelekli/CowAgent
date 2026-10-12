import os
from channel.web.core import template

def test_distinct_file_edits_in_same_millisecond_have_distinct_versions(tmp_path, monkeypatch):
    static = tmp_path / 'static'
    (static / 'js').mkdir(parents=True)
    asset = static / 'js' / 'app.js'
    monkeypatch.setattr(template, '_STATIC_DIR', str(static))
    base_ns = 1_700_000_000_123_000_000
    asset.write_text('first')
    os.utime(asset, ns=(base_ns, base_ns))
    first = template.asset_version('js/app.js')
    asset.write_text('second')
    os.utime(asset, ns=(base_ns + 100_000, base_ns + 100_000))
    second = template.asset_version('js/app.js')
    assert first != second
    assert second == format(asset.stat().st_mtime_ns, 'x')

def test_unchanged_asset_keeps_same_version(tmp_path, monkeypatch):
    (tmp_path / 'js').mkdir()
    (tmp_path / 'js' / 'app.js').write_text('stable')
    monkeypatch.setattr(template, '_STATIC_DIR', str(tmp_path))
    assert template.asset_version('js/app.js') == template.asset_version('js/app.js')
