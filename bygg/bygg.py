"""Bygger bestemmelsene fra paragrafer/, vedlegg/ og struktur.yml.

Bruk:  python bygg/bygg.py [utmappe] [--kilde URL]

utmappe   hvor siden skrives (standard: _site)
--kilde   lenke til repoet som vises øverst på siden («Kilde og
          endringsforslag»). Utelates den, vises ingen lenke.

Lager index.html og bestemmelser.json. Stopper med feilmelding hvis
struktur.yml og filene ikke stemmer overens, eller en henvisning ikke finnes.
"""
import argparse, html, json, pathlib, re, subprocess, sys
import yaml

ROT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(description="Bygger bestemmelsene")
ap.add_argument("utmappe", nargs="?", default=str(ROT / "_site"))
ap.add_argument("--kilde", help="URL til repoet, vises som lenke på siden")
ARGS = ap.parse_args()
UT = pathlib.Path(ARGS.utmappe)
STATUSER = {"vedtatt", "forslag"}
feil = []


def les(fil):
    tekst = fil.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", tekst, re.S)
    if not m:
        raise SystemExit(f"{fil}: mangler metadata (---) øverst")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def slug(t):
    t = t.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# ---------- struktur og nummerering ----------
struktur = yaml.safe_load((ROT / "struktur.yml").read_text(encoding="utf-8"))
mål = {}        # id -> {"tekst": "§ 5.4.3", "anker": ...}
paragrafer = []  # i rekkefølge
kapitler = []

for k, kap in enumerate(struktur["kapitler"], 1):
    mål[kap["id"]] = {"tekst": f"kapittel {k}", "anker": f"kap-{kap['id']}"}
    kapinfo = {"id": kap["id"], "nummer": str(k), "tittel": kap["tittel"], "deler": [], "paragrafer": []}
    kapitler.append(kapinfo)

    def legg_til(pid, nummer, del_id, liste):
        fil = ROT / "paragrafer" / f"{pid}.md"
        if not fil.exists():
            feil.append(f"struktur.yml viser til {pid}, men paragrafer/{pid}.md finnes ikke")
            return
        meta, kropp = les(fil)
        if pid in mål:
            feil.append(f"id {pid} er brukt to ganger")
        mål[pid] = {"tekst": f"§ {nummer}", "anker": pid}
        p = {"id": pid, "nummer": nummer, "tittel": meta.get("tittel", ""), "status": meta.get("status"),
             "vedtak": meta.get("vedtak") or [], "kapittel": kap["id"], "del": del_id, "kropp": kropp}
        if p["status"] not in STATUSER:
            feil.append(f"{pid}: status må være vedtatt eller forslag")
        if p["status"] == "vedtatt" and not p["vedtak"]:
            feil.append(f"{pid}: vedtatt paragraf mangler vedtaksreferanse")
        paragrafer.append(p)
        liste.append(p)

    for i, pid in enumerate(kap.get("paragrafer") or [], 1):
        legg_til(pid, f"{k}.{i}", None, kapinfo["paragrafer"])
    for d, dl in enumerate(kap.get("deler") or [], 1):
        nr = f"{k}.{d}"
        mål[dl["id"]] = {"tekst": f"§ {nr}", "anker": dl["id"]}
        delinfo = {"id": dl["id"], "nummer": nr, "tittel": dl["tittel"], "paragrafer": []}
        kapinfo["deler"].append(delinfo)
        for i, pid in enumerate(dl.get("paragrafer") or [], 1):
            legg_til(pid, f"{nr}.{i}", dl["id"], delinfo["paragrafer"])

vedlegg = []
for v, vid in enumerate(struktur.get("vedlegg") or [], 1):
    fil = ROT / f"{vid}.md"
    if not fil.exists():
        feil.append(f"struktur.yml viser til {vid}, men {vid}.md finnes ikke")
        continue
    meta, kropp = les(fil)
    mål[vid] = {"tekst": f"vedlegg {v}", "anker": vid}
    vedlegg.append({"id": vid, "nummer": str(v), **meta, "kropp": kropp})

# filer som ikke er med i strukturen
for fil in sorted((ROT / "paragrafer").rglob("*.md")):
    pid = fil.relative_to(ROT / "paragrafer").with_suffix("").as_posix()
    if pid not in mål:
        feil.append(f"paragrafer/{pid}.md er ikke med i struktur.yml")
for fil in sorted((ROT / "vedlegg").glob("*.md")):
    if f"vedlegg/{fil.stem}" not in mål:
        feil.append(f"vedlegg/{fil.name} er ikke med i struktur.yml")


# ---------- tekst -> HTML ----------
def inline(t, kilde):
    def ref(m):
        rid = m.group(1)
        if rid not in mål:
            feil.append(f"{kilde}: henvisningen [[{rid}]] finnes ikke")
            return html.escape(m.group(0))
        return f'<a href="#{mål[rid]["anker"]}">{mål[rid]["tekst"]}</a>'
    t = html.escape(t, quote=False).replace("&lt;br&gt;", "<br>")
    t = re.sub(r"\[\[([^\]]+)\]\]", ref, t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


def ren_tekst(t):
    """Kroppstekst med henvisninger skrevet ut, for JSON/søk."""
    return re.sub(r"\[\[([^\]]+)\]\]", lambda m: mål.get(m.group(1), {}).get("tekst", m.group(0)), t).strip()


def blokk_html(kropp, kilde, definisjoner=False):
    ut, linjer, i = [], kropp.splitlines(), 0
    while i < len(linjer):
        l = linjer[i]
        if not l.strip():
            i += 1
        elif l.lstrip().startswith("- "):
            items = []
            while i < len(linjer) and linjer[i].lstrip().startswith("- "):
                dybde = (len(linjer[i]) - len(linjer[i].lstrip())) // 2
                m = re.match(r"-\s+([0-9a-zæøå]+)\)\s+(.*)", linjer[i].strip())
                if not m:
                    feil.append(f"{kilde}: listepunkt må ha formen «- a) tekst»: {linjer[i].strip()}")
                    m = re.match(r"-\s+()(.*)", linjer[i].strip())
                items.append((dybde, m.group(1), m.group(2)))
                i += 1
            ut.append(liste_html(items, kilde, definisjoner))
        elif l.startswith("|"):
            rader = []
            while i < len(linjer) and linjer[i].startswith("|"):
                rader.append([c.strip() for c in linjer[i].strip().strip("|").split("|")])
                i += 1
            ut.append(tabell_html(rader, kilde))
        else:
            ut.append(f"<p>{inline(l.strip(), kilde)}</p>")
            i += 1
    return "\n".join(ut)


def liste_html(items, kilde, definisjoner):
    ut, stakk = [], []
    for dybde, bokstav, tekst in items:
        while len(stakk) > dybde + 1:
            ut.append("</li></ol>"); stakk.pop()
        if len(stakk) == dybde + 1:
            ut.append("</li>")
        else:
            ut.append(f'<ol class="litra{" nr" if dybde else ""}">'); stakk.append(dybde)
        attr = ""
        if definisjoner and dybde == 0:
            m = re.match(r"\*([^*:]+):\*", tekst)
            if m:
                attr = f' id="def-{slug(m.group(1))}"'
        ut.append(f'<li data-l="{bokstav}"{attr}>{inline(tekst, kilde)}')
    while stakk:
        ut.append("</li></ol>"); stakk.pop()
    return "".join(ut)


def tabell_html(rader, kilde):
    hode, kropp, just = rader[0], rader[1:], []
    if kropp and all(re.fullmatch(r":?-+:?", c) for c in kropp[0]):
        just = ["num" if c.endswith(":") else "" for c in kropp[0]]
        kropp = kropp[1:]
    def celle(tag, c, j):
        return f'<{tag}{f" class={chr(34)}{j}{chr(34)}" if j else ""}>{inline(c, kilde)}</{tag}>'
    th = "".join(celle("th", c, just[n] if n < len(just) else "") for n, c in enumerate(hode))
    tr = "".join("<tr>" + "".join(celle("td", c, just[n] if n < len(just) else "") for n, c in enumerate(r)) + "</tr>" for r in kropp)
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def paragraf_html(p):
    st = ' data-status="forslag"' if p["status"] == "forslag" else ""
    kropp = blokk_html(p["kropp"], p["id"], definisjoner=p["id"] == "innledende/definisjoner")
    ref = f'<p class="ref">Vedtak: {html.escape("; ".join(map(str, p["vedtak"])))}.</p>' if p["vedtak"] else ""
    return (f'<section class="par" id="{p["id"]}"{st}>\n<h3><span class="sign">§ {p["nummer"]}</span>'
            f'{html.escape(p["tittel"])}</h3>\n{kropp}\n{ref}</section>')


deler = []
for kap in kapitler:
    deler.append(f'<h2 id="kap-{kap["id"]}" data-nr="{kap["nummer"]}">Kapittel {kap["nummer"]}. {html.escape(kap["tittel"])}</h2>')
    deler += [paragraf_html(p) for p in kap["paragrafer"]]
    for dl in kap["deler"]:
        deler.append(f'<h4 class="gjeng" id="{dl["id"]}"><span class="sign">§ {dl["nummer"]}</span> {html.escape(dl["tittel"])}</h4>')
        deler += [paragraf_html(p) for p in dl["paragrafer"]]

if vedlegg:
    deler.append('<h2 id="vedlegg">Vedlegg</h2>\n<div class="vedlegg">')
    for v in vedlegg:
        st = ' data-status="forslag"' if v.get("status") == "forslag" else ""
        info = [f"Gjelder fra {v['gjelder_fra']}." if v.get("gjelder_fra") else "",
                f"Neste gjennomgang {v['neste_gjennomgang']}." if v.get("neste_gjennomgang") else "",
                v.get("merknad") or ""]
        info = " ".join(x for x in info if x)
        deler.append(f'<h3 id="{v["id"]}"{st}>Vedlegg {v["nummer"]}. {html.escape(v["tittel"])}</h3>'
                     + (f'<p class="note">{html.escape(info)}</p>' if info else "")
                     + blokk_html(v["kropp"], v["id"]))
    deler.append("</div>")


# ---------- endringslogg fra git ----------
def git_logg():
    fmt = "%ad%x1f%an%x1f%s%x1f%(trailers:key=Type,valueonly,separator=%x2C)%x1f%(trailers:key=Kilde,valueonly,separator=%x2C)%x1e"
    try:
        r = subprocess.run(["git", "log", f"--format={fmt}", "--date=format:%d.%m.%Y", "--",
                            "paragrafer", "vedlegg", "struktur.yml"],
                           cwd=ROT, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [p.strip("\n").split("\x1f") for p in r.stdout.split("\x1e") if p.strip()]


logg = git_logg()
rader = "".join("<tr>" + "".join(f"<td>{html.escape(c.strip()) or '–'}</td>" for c in r) + "</tr>" for r in logg)
deler.append('<h2 id="endringslogg">Endringslogg</h2>\n<div class="table-wrap"><table><thead><tr>'
             '<th>Dato</th><th>Endret av</th><th>Hva</th><th>Type</th><th>Kilde</th></tr></thead>'
             f'<tbody>{rader}</tbody></table></div>')
hist = (ROT / "historikk.md").read_text(encoding="utf-8") if (ROT / "historikk.md").exists() else ""
if hist:
    tittel, _, rest = hist.partition("\n")
    deler.append(f'<h3 class="hist">{html.escape(tittel.lstrip("# "))}</h3>' + blokk_html(rest, "historikk.md"))

if feil:
    print("Bygget stoppet:\n  " + "\n  ".join(dict.fromkeys(feil)), file=sys.stderr)
    sys.exit(1)

# ---------- skriv ut ----------
UT.mkdir(parents=True, exist_ok=True)
antall = {s: sum(p["status"] == s for p in paragrafer) for s in STATUSER}
undertittel = f"{antall['vedtatt']} vedtatte paragrafer · {antall['forslag']} forslag"
mal = (ROT / "bygg" / "mal.html").read_text(encoding="utf-8")
kilde = f' · <a href="{html.escape(ARGS.kilde)}">Kilde og endringsforslag</a>' if ARGS.kilde else ""
(UT / "index.html").write_text(mal.replace("{{UNDERTITTEL}}", undertittel).replace("{{KILDE}}", kilde)
                               .replace("{{INNHOLD}}", "\n\n".join(deler)), encoding="utf-8")
data = {"paragrafer": [{k: v for k, v in p.items() if k != "kropp"} | {"tekst": ren_tekst(p["kropp"])} for p in paragrafer],
        "vedlegg": [{k: v for k, v in x.items() if k != "kropp"} | {"tekst": ren_tekst(x["kropp"])} for x in vedlegg],
        "kapitler": [{"id": k["id"], "nummer": k["nummer"], "tittel": k["tittel"],
                      "deler": [{"id": d["id"], "nummer": d["nummer"], "tittel": d["tittel"]} for d in k["deler"]]}
                     for k in kapitler]}
(UT / "bestemmelser.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Bygget {len(paragrafer)} paragrafer ({undertittel}) og {len(vedlegg)} vedlegg til {UT}")
