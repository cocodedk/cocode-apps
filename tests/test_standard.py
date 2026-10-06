import re
from html.parser import HTMLParser
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STANDARD = ROOT / "standard"
PLACEHOLDER = "support.md"
FILES = {"about-page.md", "privacy.md", "install-block.md", "navigation.md", "readme.md",
         "store-listing.md", "release.md", "website.md", PLACEHOLDER}
HEADINGS = ("What must exist", "Where", "How the audit checks it", "Example")
STRINGS = {
    "about_check_updates": ("Check for updates", "Søg efter opdateringer"),
    "about_privacy_link": ("Read the privacy policy", "Læs privatlivspolitikken"),
    "about_website": ("Open the website", "Åbn hjemmesiden"),
    "about_source": ("See the source code on GitHub", "Se kildekoden på GitHub"),
    "about_report": ("Report a problem on GitHub", "Meld en fejl på GitHub"),
    "about_credits": ("Credits and licenses", "Tak og licenser"),
    "about_made_by": ("Made by Cocode (cocode.dk)", "Lavet af Cocode (cocode.dk)"),
}
PRIVACY_H2 = ["Summary", "What is collected", "Servers the app contacts", "Permissions",
              "What stays on the phone", "Third parties", "Your rights", "Contact", "Changes"]


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.main_ids = []
        self.h2 = []
        self._in_h2 = False

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1 += 1
        elif tag == "main":
            self.main_ids.append(dict(attrs).get("id"))
        elif tag == "h2":
            self._in_h2 = True
            self.h2.append("")

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_h2 = False

    def handle_data(self, data):
        if self._in_h2:
            self.h2[-1] += data


def test_standard_holds_exactly_the_nine_files():
    assert {p.name for p in STANDARD.iterdir()} == FILES


def test_each_area_file_has_the_four_headings():
    for name in FILES - {PLACEHOLDER}:
        text = (STANDARD / name).read_text("utf-8")
        found = re.findall(r"^## (.+?)\s*$", text, re.MULTILINE)
        for heading in HEADINGS:
            assert heading in found, f"{name} lacks '## {heading}'"


def test_about_strings_have_every_key_and_wording():
    text = (ROOT / "templates/about-strings.md").read_text("utf-8")
    for key, (english, danish) in STRINGS.items():
        row = next((line for line in text.splitlines() if f"| {key} |" in line), None)
        assert row, f"{key} missing"
        assert english in row and danish in row, f"{key} wording differs"


def test_about_strings_list_the_section_titles_in_order():
    text = (ROOT / "templates/about-strings.md").read_text("utf-8")
    line = next(x for x in text.splitlines() if x.startswith("The section titles"))
    titles = ["Name and version", "What the app does", "Privacy", "Links",
              "Credits and licenses", "Made by Cocode", "Support"]
    positions = [line.index(t) for t in titles]
    assert positions == sorted(positions)


def test_privacy_skeleton_structure():
    html = (ROOT / "templates/privacy-skeleton.html").read_text("utf-8")
    page = _Page()
    page.feed(html)
    assert page.h1 == 1
    assert page.main_ids == ["main"]
    assert page.h2 == PRIVACY_H2
    for block in ("nav", "footer"):
        assert f"<!-- cocode-apps:{block}:start -->" in html
        assert f"<!-- cocode-apps:{block}:end -->" in html


def test_skill_front_matter():
    text = (ROOT / "skill/SKILL.md").read_text("utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    assert match
    meta = yaml.safe_load(match.group(1))
    assert meta["name"] == "cocode-apps"
    assert str(meta["description"]).strip()


def test_nobody_names_the_blocklist_provider():
    for folder in ("standard", "templates", "skill"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in {".md", ".html", ".txt", ".yml"}:
                assert "spamhaus" not in path.read_text("utf-8").lower(), path
