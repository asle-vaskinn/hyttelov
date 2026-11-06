# Bestemmelser for Studenterhytta NTNUI

Kilden til Studenterhyttas bestemmelser.

- **Gjeldende bestemmelser:** <https://asle-vaskinn.github.io/hyttelov/>
- **Endringsforslag:** åpne [pull requests](../../pulls). Hvert forslag har en
  forhåndsvisning på `https://asle-vaskinn.github.io/hyttelov/pr/<nummer>/`,
  og menyen øverst på siden bytter mellom gjeldende versjon og forslagene.

## Prinsipp

- **`main` er det som gjelder.** Her ligger bare paragrafer Hyttestyret har vedtatt.
- **Alt annet er endringsforslag**, det vil si en pull request (PR). Det gjelder
  nye paragrafer, endringer og sletting.
- En PR flettes inn i `main` når Hyttestyret har vedtatt den, eller direkte når
  den er en teknisk endring (§ 1.10 fjerde ledd).

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

`struktur.yml` kan ha plass til paragrafer som ennå ikke er vedtatt. Plassen
teller med i nummereringen, men vises ikke. Slik beholder paragrafene numrene
sine når de vedtas senere. En vedtatt paragraf kan ikke vise til en plass uten
fil; bygget stopper da.

### En paragraffil

```markdown
---
tittel: Mandat
status: vedtatt            # vedtatt eller forslag
vedtak:                    # minst én referanse når status er vedtatt
- Hyttestyremøte 17, sak 4 (12.10.2026)
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

## Slik foreslår du en endring

1. Åpne filen på GitHub og trykk blyanten (*Edit*). GitHub lager en egen
   gren for deg. For en ny paragraf: *Add file* i riktig mappe, og legg id-en
   inn i `struktur.yml`.
2. Trykk *Propose changes*, deretter *Create pull request*, og fyll ut malen.
3. Forhåndsvisningen kommer på `…/hyttelov/pr/<nummer>/` etter et par minutter.
   Endrede paragrafer er markert, med ordvis forskjell mot gjeldende tekst.

Større utkast som ikke er klare for behandling, legges som *draft* PR.

Bygget sjekker hvert forslag: ukjente henvisninger, paragrafer som mangler i
`struktur.yml`, henvisninger til paragrafer som ikke er vedtatt, og vedtatte
paragrafer uten vedtaksreferanse stopper bygget.

## Regler for fletting (§ 1.10)

- Bare den Hyttestyret har utnevnt etter § 1.10 sjette ledd, fletter inn i `main`.
- **Vedtak:** flettes etter at Hyttestyret har fattet vedtaket. Paragrafene får
  `status: vedtatt` og vedtaksreferansen i `vedtak:`.
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
python bygg/bygg.py           # gjeldende versjon til _site/
bygg/bygg-alle.sh             # gjeldende versjon og alle åpne forslag (krever gh og jq)
```

`_site/bestemmelser.json` har alle paragrafer med nummer, status og tekst,
og kan leses av andre systemer (for eksempel Permen).
