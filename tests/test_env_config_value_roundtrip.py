from dotenv import dotenv_values
from agent.tools.env_config.env_config import EnvConfig


def make_tool(tmp_path):
    tool = EnvConfig()
    tool.env_dir = str(tmp_path)
    tool.env_path = str(tmp_path / '.env')
    return tool


def test_env_edit_preserves_existing_dotenv_syntax(tmp_path):
    tool = make_tool(tmp_path)
    (tmp_path / '.env').write_text('export COW_TEST_KEY="quoted test value" # comment\n')
    assert tool.execute({'action': 'set', 'key': 'COW_TEST_OTHER', 'value': 'new value'}).status == 'success'
    assert dotenv_values(tool.env_path)['COW_TEST_KEY'] == 'quoted test value'
    assert 'export COW_TEST_KEY' not in tool._read_env_file()
    assert tool._read_env_file()['COW_TEST_KEY'] == 'quoted test value'


def test_env_set_value_roundtrips_spaces_comments_and_quotes(tmp_path, monkeypatch):
    tool = make_tool(tmp_path)
    values = ['  padded  ', 'literal # hash', '"double" and \'single\'', 'a\\b']
    for value in values:
        monkeypatch.delenv('COW_TEST_ROUNDTRIP', raising=False)
        result = tool.execute({'action': 'set', 'key': 'COW_TEST_ROUNDTRIP', 'value': value})
        assert result.status == 'success'
        assert dotenv_values(tool.env_path)['COW_TEST_ROUNDTRIP'] == value
        assert tool._read_env_file()['COW_TEST_ROUNDTRIP'] == value
