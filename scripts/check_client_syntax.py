"""Extract and syntax-check Meme Fighter's inline JavaScript with Node."""
from html.parser import HTMLParser
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collect = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.collect = not dict(attrs).get('src')

    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect = False

    def handle_data(self, data):
        if self.collect:
            self.chunks.append(data)

if __name__ == '__main__':
    source = Path(__file__).resolve().parents[1] / 'index.html'
    parser = Scripts()
    parser.feed(source.read_text(encoding='utf-8'))
    assert parser.chunks, 'No inline game JavaScript found'
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'game.js'
        path.write_text('\n'.join(parser.chunks), encoding='utf-8')
        check = run(['node', '--check', str(path)], check=False)
        raise SystemExit(check.returncode)
