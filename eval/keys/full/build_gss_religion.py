"""Build the religion answer key for the full GSS cumulative file (7224r3a).

Usage: python eval/keys/full/build_gss_religion.py [PDT_GSS [COMMIT]] [--undecided]

Reads pdt-gss's committed records for release 7224r3a (gssrdoc 0.9 text, Task 26) and its
subject groups, at COMMIT (default HEAD), so a key names the exact records it was built from.
Until Task 51 it read gssrdoc 0.8.2 (gssrdoc_full.json), which documents Release 2.

Method:
1. Candidates: every gssrdoc variable with the publisher subject Religion, Jews or Prayer In
   School; or in a religion module; or whose label or question matches KEYWORDS.
2. Each candidate was read by hand (name, label, and question text where the label was
   unclear) and sorted with the rule in README.md: HIT, NEUTRAL, or out.
3. A candidate with the publisher subject Religion that isn't a hit is neutral, never out, so
   the key covers the publisher's list.

The key can miss an on-topic variable that no candidate rule caught; the README says so.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent

KEYWORDS = re.compile(
    r"relig|church|\bgod\b|pray|bible|scriptur|clergy|clergymen|minister|priest|rabbi|faith|"
    r"spiritual|worship|denomin|\bjew|judais|cathol|protestant|muslim|islam|mosque|synagog|heaven|"
    r"hell\b|afterlife|life after death|evolution|fundamental|theolog|sacred|miracle|baptis|"
    r"born.again|devil|reincarn|meditat|jesus|christ|congregat|parish|mass\b|sabbath|kosher|buddh|"
    r"hindu|atheis|agnost|secular|sect\b|bar mitzvah|confirmation", re.I)
SUBJECTS = {"Religion", "Jews", "Prayer In School"}
MODULES = {"Religion", "ISSP Religion", "Religion and Culture", "Spirituality and Religion",
           "Clergy/Sex", "Religious Attendance and Identity", "Jewish Identity"}


def words(s):
    return s.split()


# Decisions: the first reader (Task 23) made these from gssrdoc 0.8.2. When the key moved to
# the 0.9 records (Task 51), the only new candidate among the 40 names 0.8.2 lacked was
# reltrad16 (religious tradition at age 16), added as a hit by Claude (PublicDataToolkit Task 51).
#
# The respondent's own affiliation or identity (now or when young), attendance or
# participation, practice, the importance of religion to them, and religious belief or experience.
HIT = {
    "affiliation and identity": words("""
        relig denom other othjew jew jewaj fund reliten relitena relitenv relitennv
        relig16 denom16 oth16 othjew16 jew16 jew16aj fund16 religkid denkid norelgsp norelgsp16
        relig_next denom_next jew_next other_next fund_next reltrad reltrad16 denom_7222 denom16_7322
        switched switch1 switch2 switch3 switnum switage1 switage2 switwhy1 switwhy2
        religid relid1 relid2 relid3 relidbst cathid charisma evangclx evangcly
        relidesc relidwe relidins relpersn sprtprsn relsprt feelrel"""),
    "attendance and participation": words("""
        attend attend12 attrelig numdays sunday monday tuesday wednesdy thursday friday saturday
        attreg attweek othrel othrel1 othrel2 othrel3 relactiv relactiv1 churhmem churhact
        memchurh actchurh grpchurh grprelig synmem lapsed churhsch sunsch16 join16 bmitzvah"""),
    "practice": words("""
        pray prayfreq privpray chnang7 meditate mditate1 grace16 saygrace readword relscrpt
        tvrelig mediarel relig30 wwwrelig relobjct vistholy perscrfc savesoul relhrs1 relhrs2"""),
    "importance": words("""
        impchurh impgod religimp relidimp gochurch believe follow obeytch rellife decbible
        decchurh relcmfrt relsprt1 relsprt2"""),
    "belief and experience": words("""
        bible bibley biblev biblenv bible1 biblauth god godchnge theism godmeans predeter lfegod
        postlife postlifev postlifenv postlf1 postlf2 postlf3 postlf4 postlf5 postlf6 postlf7 postlf8
        postlf9 postlf10 likediff mindbody restact palefull afterlif heaven hell devil miracles
        reincar nirvana ancestrs reltruth mywaygod sinsacri chrstsav evngelze popespks popespky
        neargod judge redeemer lover master mother creator father spouse friend king liberatr
        healer mapa mastersp judgeluv frndking crtrheal rdeemlib world3 world7
        grace reborn numrborn agerborn chngrbrn relexp relexper numrelex agerelex chngrel entity
        expchng1 expchng2 expchng3 whychng1 whychng2 whychng3 changed1 changed2 changed3
        relalt1 relalt2 relalt3 relalt4 relalt5 relalt6 relneg myfaith madatgod
        doubts1 doubts2 doubts3 doubts4 faith1 faith2 faith3 faith4
        cope1 cope2 cope3 cope4 cope5 cope6 godwatch forgive3 feelgod uniongod godlove beausprt
        joylifts godhelp godguide godlvdir godlvoth closrgod godclose"""),
}

# About religion, but not the respondent's own religiosity.
NEUTRAL = {
    "other people's religion": words("""
        sprel spden spother spothjew spjew spjewaj spfund sprel16 spden16 spoth16 spjew16 spfund16
        spjrel16 spjoth16 religsp densp spnorelgsp spden_7322 spattend
        corel coden coother cojew cofund conorelgsp coden_1222
        marelig maden maoth majew mafund parelig paden paoth pajew pafund majwoth pajwoth
        marelkid madenkid parelkid padenkid maattend paattend attendma attendpa
        kd1relig kd2relig kd3relig kd4relig kd5relig kd6relig kd7relig kd8relig
        kd1jwoth kd2jwoth kd3jwoth kd4jwoth kd5jwoth
        relig1 relig2 relig3 relig4 relig5
        frndcon1 frndcon2 frndcon3 frndcon4 frndcon5 frndrel1 frndrel2 frndrel3 frndrel4 frndrel5
        frndden1 frndden2 frndden3 frndden4 frndden5 frndoth1 frndoth2 frndoth3 frndoth4 frndoth5
        frndfnd1 frndfnd2 frndfnd3 frndfnd4 frndfnd5
        acqgoatt acqnoatt acqfmgo acqfmno acqnhgo acqnhno acqwkgo acqwkno acqvago acqvano acqattnd
        trtgoatt trtnoatt trtattnd meetings emchurch"""),
    "attitudes toward religious groups": words("""
        prottemp cathtemp jewtemp mslmtemp christns muslims hindus buddhsts jews atheists
        idols rosaries notthink othchrch implives contjew contmslm
        wlthjews workjews violjews intljews farejews patrjews livejews marjew influjew famjews
        fairjews usjews jewschng comjews knwjew jewsschl jewscom jewsrel jewswrk jewscls"""),
    "religion in public life and tolerance": words("""
        prayer prayery prayerx prayerv prayernv schlpray conclerg conclery conchurh
        polsgod clergvte religpub clerggov churhpow religcon religint religinf
        relgrpeq rspctrel relmarry relcand relext1 relext2 relext3 relmeet antirel oprelig
        spkath colath libath spkathy libathy spkracy spkmslm colmslm libmslm spkmslmy libmslmy
        ethspkok ethspkno fepriest feclergy relgrade relgeneq relgenbar govvsrel difrel relpast
        relrlvnt paxhappy makefrnd comfort rightpeo godusa govchrst amchrstn roleclrg chldmorl
        irrelart irreloff artgod relart godsells godsport"""),
    "religious giving, volunteering and congregations": words("""
        tithing givecong giverel volrelig monrelig hrsrelig givrelig totrelig valrelig volwkrel
        numcong conghlp1 conghlp2 conghrm1 conghrm2 termrel shoprel shopmove shopnum
        preach ferespct sympcoun wrkyoung worship churhgrp churchtx typchurh numchurh
        yrchurh1 yrchurh2 yrchurh3 yrchurh4 yrchurh5 yrchurh6
        mtchurh1 mtchurh2 mtchurh3 mtchurh4 mtchurh5 mtchurh6 racchurh
        cathsch chrissch denomsch relsch"""),
    "religion and science": words("""
        creation scitesty evolved1 screlig relinfsc relbstsc sciimp5 scientre engrel scifaith
        naturgod resnatur"""),
    "vignettes and moral views in religion modules": words("""
        godswill tlkclrgy sphealer ortlkclr orhealer mhdorel mhdoheal mhdopray mhgod mhhlprel
        punsin godright socright perright blkwhite rotapple permoral decoths decself goownway
        fatalism nihilism egomeans ownfate lesspain harmony alloflfe blessngs forgive1 forgive2
        carright cardo"""),
    "clergy sexual misconduct module": words("""
        harsexcl ownclerg numclerg openrel1 openrel2 openrel3 counsel1 counsel2 counsel3
        clrgmar1 clrgmar2 clrgmar3 clrgsex1 clrgsex2 clrgsex3 clrggen1 clrggen2 clrggen3
        ongorel1 ongorel2 ongorel3 hushrel1 hushrel2 hushrel3 toldexp1 toldexp2 toldexp3
        toldrel1 toldrel2 toldrel3 knwclsex clsclsex"""),
}


def git_show(repo, commit, path):
    return subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                          capture_output=True, text=True, check=True).stdout


def load(repo, commit):
    """7224r3a records as {variable, description, question, subjects, modules}."""
    subjects = {}
    for line in git_show(repo, commit, "metadata/groups.jsonl").splitlines():
        g = json.loads(line)
        if g["kind"] == "subject":
            for m in g["members"]:
                subjects.setdefault(m["name"], set()).add(g["label"])
    out = []
    for line in git_show(repo, commit, "metadata/releases/7224r3a/variables.jsonl").splitlines():
        r = json.loads(line)
        out.append({"variable": r["name"], "description": r.get("label") or r.get("description"),
                    "question": " ".join(q["text"] for q in r.get("questions", [])),
                    "subjects": subjects.get(r["name"], set()),
                    "modules": set(r.get("extensions", {}).get("gss", {}).get("modules", []))})
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    undecided = "--undecided" in sys.argv
    repo = Path(args[0]) if args else HERE.parents[3] / "pdt-gss"
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short",
                             args[1] if len(args) > 1 else "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    recs = load(repo, commit)
    hit = {n: c for c, ns in HIT.items() for n in ns}
    neutral = {n: c for c, ns in NEUTRAL.items() for n in ns}
    assert not set(hit) & set(neutral), set(hit) & set(neutral)
    names = {r["variable"] for r in recs}
    assert not (set(hit) | set(neutral)) - names, (set(hit) | set(neutral)) - names

    items, n_candidates, religion_subject = [], 0, 0
    for r in recs:
        name = r["variable"]
        subjects = r["subjects"]
        candidate = (subjects & SUBJECTS or r["modules"] & MODULES
                     or KEYWORDS.search(f"{r['description'] or ''} {r['question'] or ''}"))
        n_candidates += bool(candidate)
        religion_subject += "Religion" in subjects
        if name in hit:
            items.append({"dataset": "gss", "table": None, "name": name, "status": "hit",
                          "why": hit[name]})
        elif name in neutral:
            items.append({"dataset": "gss", "table": None, "name": name, "status": "neutral",
                          "why": neutral[name]})
        elif "Religion" in subjects:
            items.append({"dataset": "gss", "table": None, "name": name, "status": "neutral",
                          "why": "publisher subject Religion, not judged on-topic"})
        elif candidate and undecided:
            # Candidates left out; review these when the records change (--undecided).
            print("OUT?", name, "|", r["description"], "|", sorted(subjects), "|",
                  (r["question"] or "")[:160])
    key = {
        "question": "religion",
        "expected_label": "approximate",
        "scope": {"gss": {"release": "7224r3a", "variables": len(recs),
                          "source": f"pdt-gss {commit}: metadata/releases/7224r3a, groups.jsonl"}},
        "built_by": "eval/keys/full/build_gss_religion.py; hand decisions in its HIT and NEUTRAL lists",
        "candidates": n_candidates,
        "publisher_subject_religion": religion_subject,
        "items": items,
    }
    out = HERE / "gss_religion.yaml"
    out.write_text("# Religion key for the full GSS. Generated by build_gss_religion.py.\n"
                   + yaml.safe_dump(key, sort_keys=False, width=100))
    hits = sum(i["status"] == "hit" for i in items)
    print(f"{out.name}: {n_candidates} candidates, {hits} hits, {len(items) - hits} neutral")


if __name__ == "__main__":
    main()
