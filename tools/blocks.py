"""The shared blocks, written from an App. Pure functions: no files, no network."""
from html import escape

from tools.blocks_text import CATALOGUE_URL, TEXT
from tools.registry import App

BADGE_FILE = "img/get-it-on-fdroid-{lang}.png"


def _other(app: App, lang: str) -> str:
    return "en" if lang == "da" else "da"


def _obtainium(app: App) -> str:
    return f"https://apps.obtainium.imranr.dev/redirect?r=obtainium://add/https://github.com/cocodedk/{app.repo}"


def install_html(app: App, lang: str) -> str:
    t = TEXT[lang]
    if app.fdroid_live:
        first = (f'<a class="fdroid" href="{app.fdroid_url}"><img src="{app.base}{BADGE_FILE.format(lang=lang)}" '
                 f'alt="{escape(t["badge_alt"])}" width="240" height="93"></a>')
    else:
        first = f'<p class="fdroid-soon">{escape(t["coming"])}</p>'
    items = [f"<li>{first}</li>", f'<li><a href="{app.apk_url}">{escape(t["apk"])}</a></li>']
    if app.obtainium:
        items.append(f'<li><a href="{escape(_obtainium(app))}">{escape(t["obtainium"])}</a></li>')
    return '<ul class="install" role="list">\n  ' + "\n  ".join(items) + "\n</ul>"


def install_md(app: App, lang: str) -> str:
    t = TEXT[lang]
    lines = []
    if app.fdroid_live:
        lines.append(f'[<img src="https://fdroid.gitlab.io/artwork/badge/get-it-on.png" alt="{t["badge_alt"]}" '
                     f'height="80">]({app.fdroid_url})')
    else:
        lines.append(f"- {t['coming']}")
    lines.append(f"- [{t['apk']}]({app.apk_url})")
    if app.obtainium:
        lines.append(f"- [{t['obtainium']}]({_obtainium(app)})")
    return "\n".join(lines)


def _bilingual(app: App) -> bool:
    """The site has both languages, so the language switch has somewhere to go."""
    return {"en", "da"} <= set(app.languages)


def nav_html(app: App, lang: str, current: str = "home") -> str:
    """The privacy link appears once apps.yml has a privacy URL, the language switch once the app has both
    languages: no link ever points at a page that does not exist yet."""
    t, other = TEXT[lang], _other(app, lang)
    home = app.href(lang)
    name = app.name_en if lang == "en" else app.name_da

    def link(key: str, attrs: str, label: str) -> str:
        page = ' aria-current="page"' if key == current else ""
        return f'  <a {attrs} data-nav="{key}"{page}>{label}</a>\n'

    icon = f'<img src="{app.base}img/icon.png" alt="" width="32" height="32">'
    privacy = link("privacy", f'href="{home}privacy/"', escape(t["privacy"])) if app.privacy else ""
    switch = (link("lang", f'href="{app.href(other)}" hreflang="{other}" lang="{other}"',
                   escape(TEXT[other]["lang_name"])) if _bilingual(app) else "")
    return (
        f'<link rel="stylesheet" href="{app.base}css/cocode-nav.css">\n'
        f'<a class="skip" href="#main">{escape(t["skip"])}</a>\n'
        f'<nav class="cocode-nav" aria-label="{escape(name)}">\n'
        + link("home", f'class="brand" href="{home}"', icon + escape(name))
        + link("how", f'href="{home}#how"', escape(t["how"]))
        + link("install", f'href="{home}#install"', escape(t["install"]))
        + privacy
        + switch
        + link("more", f'href="{CATALOGUE_URL}"', escape(t["more"]))
        + "</nav>"
    )


def footer_html(app: App, lang: str) -> str:
    t, home = TEXT[lang], app.href(lang)
    return (
        '<footer class="cocode-footer">\n'
        f'  <a href="https://github.com/cocodedk/{app.repo}">{escape(t["source"])}</a> ·\n'
        + (f'  <a href="{home}privacy/">{escape(t["privacy"])}</a> ·\n' if app.privacy else "")
        + f'  {escape(t["license"])}: {escape(app.license)} ·\n'
        f'  <a href="{CATALOGUE_URL}">{escape(t["made"])} (cocode.dk)</a>\n'
        "</footer>"
    )


def catalogue_link(app: App) -> str:
    return app.fdroid_url if app.fdroid_live else app.apk_url
