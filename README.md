# Bestemmelser for Studenterhytta NTNUI

Kilden til Studenterhyttas bestemmelser. Den publiserte versjonen ligger på
<https://hyttelov.studenterhytta.org>.

## Slik er repoet bygd opp

| Hva | Hvor |
|---|---|
| Én fil per paragraf | `paragrafer/<del>/<navn>.md` |
| Rekkefølge og nummerering | `struktur.yml` |
| Vedlegg | `vedlegg/<navn>.md` |
| Endringer før repoet | `historikk.md` |
| Bygging av nettsiden | `bygg/` |

Paragrafnumrene står **ikke** i filene. De regnes ut fra rekkefølgen i
`struktur.yml`. For å flytte en paragraf flytter du linjen dens der.
Filnavnet endres ikke, så historikken til paragrafen følger med.

### En paragraffil

```markdown
---
tittel: Mandat
status: forslag            # vedtatt eller forslag
vedtak: []                 # f.eks. ["Hyttestyremøte 17, sak 4 (12.10.2026)"]
---
(1) Ansvarlig gjeng har mandat til å

- a) avgjøre bestillinger etter [[innledende/prioritering]],
- b) inngå leieavtaler etter utleiekontrakten.
```

- Ledd skrives `(1)`, `(2)` … med tom linje mellom.
- Bokstavpunkter skrives `- a)`, underpunkter rykkes inn to mellomrom: `  - 1)`.
- Henvisninger skrives `[[id]]` og blir til «§ 1.6», «kapittel 4» eller
  «vedlegg 2» når siden bygges. id-en er filstien uten `.md`
  (`innledende/prioritering`), navnet på en del (`festutleie`), et kapittel
  (`gjengene`) eller et vedlegg (`vedlegg/priser`).
- `*kursiv*`, `**fet**` og `[lenketekst](https://…)` kan brukes.

## Status: vedtatt og forslag

- `vedtatt` gjelder. En vedtatt paragraf skal ha minst én vedtaksreferanse.
- `forslag` er tekst fra utkastet som ikke er vedtatt ennå. Den vises på
  siden, merket, men gjelder ikke.

`forslag` brukes bare i overgangen. Målet er at alle paragrafer enten blir
vedtatt eller slettet. Deretter kommer alle nye forslag som pull requests.

## Slik foreslår du en endring

1. Åpne filen på GitHub og trykk blyanten (*Edit*). GitHub lager en egen
   gren for deg.
2. Gjør endringen og trykk *Propose changes*, deretter *Create pull request*.
3. Fyll ut malen: hva, begrunnelse, type og kilde.

Bygget sjekker forslaget automatisk: ukjente henvisninger, paragrafer som
mangler i `struktur.yml` og vedtatte paragrafer uten vedtaksreferanse
stopper bygget.

## Regler for fletting (§ 1.10)

- Bare den Hyttestyret har utnevnt etter § 1.10 sjette ledd, fletter inn i `main`.
- **Vedtak** flettes etter at Hyttestyret har fattet vedtaket. Vedtaksreferansen
  legges inn i `vedtak:` i paragrafen.
- **Teknisk endring** (opprydding uten endret betydning) kan flettes direkte.
- Alltid *Squash and merge*. Commit-meldingen avsluttes med

  ```
  Type: vedtak        (eller teknisk)
  Kilde: Hyttestyremøte 18, sak 3
  ```

  Endringsloggen på nettsiden lages fra disse linjene.

## Bygge lokalt

```sh
pip install pyyaml
python bygg/bygg.py          # skriver til _site/
```

`_site/bestemmelser.json` har alle paragrafer med nummer, status og tekst,
og kan leses av andre systemer (for eksempel Permen).
