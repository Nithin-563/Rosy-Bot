from pathlib import Path
import re


def test_cog_slash_command_names_are_unique():
    seen = {}
    for path in Path("src/rosy/cogs").glob("*.py"):
        for name in re.findall(r'@app_commands\.command\(name="([^"]+)"', path.read_text()):
            seen.setdefault(name, []).append(str(path))
    duplicates = {name: files for name, files in seen.items() if len(files) > 1}
    assert duplicates == {}
