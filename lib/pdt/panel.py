"""A panel's answers placed in time (STANDARD.md §2.1 `panel`, §4.1 `questions[].reference_period`).

In a panel such as the NLSY97, a person's answer about a year, or at an age, may be in any of
several rounds: rounds change frequency, people miss rounds and come back, and many questions ask
about the time since the last interview (PublicDataToolkit Task 69). This module finds every
candidate and says where each came from. It never chooses among them; `pick` does that, by a
policy the caller names.

    p = Panel("~/pdt-nlsy97", month_zero=(1979, 12))     # NLSY: continuous month 1 = January 1980
    cands = p.answers("YSAQ-360C", 1001, year=2005)       # every round whose period overlaps 2005
    cands = p.answers("CV_MARSTAT_COLLAPSED", 1001, age=25)
    best = pick(cands, "most_overlap")                    # a named policy, kept with the result

Inputs, from the repo:
- dataset.yaml `panel`: the respondent `id`, the `interview_date` (one variable counting months on
  a fixed scale, such as NLS's continuous months), `age_at_interview` (whole years) and
  `noninterview` (a code or reason, such as NLS's RNI);
- `dimensions.wave.column`: the table's wave column (SURVEY_YEAR);
- each record's `questions[].reference_period` (and `months`) by wave.

The table is read column by column from the common-format file in data/processed/ (pdt.data),
only the columns a question needs, so memory stays small.

A candidate's period is in months on the interview_date's scale (inclusive):
    as_of_interview        (m, m)              the interview month
    since_last_interview   (p + 1, m)          p = the person's previous interview, in any earlier round
    past_months N          (m - N + 1, m)
    past_30_days           (m, m)              about a month: the interview month
    ever                   (None, m)           everything up to the interview
    calendar_year          the 12 months of the year before the wave (the wave must be a year)
    (none stated)          None                the wording gives no period
Calendar years need `month_zero` (the year and month of month 0 on that scale).
"""

from dataclasses import dataclass, field
from pathlib import Path

from .check import Repo
from .common_format import PROCESSED, file_name
from .universe import universe_at


@dataclass
class Answer:
    """One round's answer to a question for a person, placed in time."""
    name: str
    person: object
    wave: object                     # the round (survey year) it came from
    value: object                    # the publisher's value or code
    label: str = None                # the code's label, when it has one
    kind: str = "valid"              # valid, or the missing code's types joined (not_asked, inap, ...)
    interview_month: int = None
    age: int = None
    period: tuple = None             # (from_month, to_month), inclusive; from is None for "ever"
    period_kind: str = None          # the wording's reference_period, or None when it states none
    overlap_months: int = None       # with year=: months of the year the period covers
    distance_years: int = None       # with age=: age at this interview minus the age asked for
    how: str = ""                    # why this round is a candidate
    universe: str = None             # who was asked in this round


@dataclass
class NoAnswer:
    """Why a round, or the whole query, gives no answer."""
    name: str
    person: object
    wave: object
    reason: str


@dataclass
class Picked:
    """The result of a named policy, with every candidate it chose from."""
    policy: str
    answer: Answer = None
    candidates: list = field(default_factory=list)
    note: str = ""


class Panel:
    def __init__(self, root, release=None, table=None, month_zero=None, data=None):
        """data: a frame of the table's columns as the publisher's values (tests, or a caller who has
        read them already); by default they are read from the common-format file."""
        self.root = Path(root).expanduser()
        self.repo = Repo.load(self.root)
        ds = self.repo.dataset
        self.spec = ds.get("panel") or {}
        if not self.spec.get("id") or not self.spec.get("interview_date"):
            raise ValueError("dataset.yaml has no panel id and interview_date (STANDARD.md §2.1)")
        self.release = release or ds["releases"][-1]["id"]
        self.wave_column = ((ds.get("dimensions") or {}).get("wave") or {}).get("column")
        tables = self.repo.tables[self.release]
        need = {self.spec["id"], self.spec["interview_date"][0], self.wave_column}
        self.table = table or next(t for t, recs in tables.items() if need <= {r["name"] for r in recs})
        self.records = {r["name"]: r for r in tables[self.table]}
        self.month_zero = month_zero
        self.path = self.root / PROCESSED / file_name(ds["id"], self.release, self.table)
        self.data = data
        timing = [self.spec["id"], self.wave_column, self.spec["interview_date"][0]]
        timing += [n for n in (self.spec.get("age_at_interview"), self.spec.get("noninterview")) if n]
        self.frame = self._columns(timing)
        self._by_person = {p: rows.sort_values(self.wave_column)
                           for p, rows in self.frame.groupby(self.spec["id"], sort=False)}

    # -------------------------------------------------------------- reading

    def _columns(self, names):
        """The publisher's values of these columns (codes included), read from the common-format file."""
        if self.data is not None:
            return self.data[[n for n in dict.fromkeys(names) if n in self.data]]
        import pyarrow.parquet as pq
        from . import data
        have = set(pq.read_schema(self.path).names)
        cols = [c for n in names for c in (n, n + data.CODE_SUFFIX) if c in have]
        table = data.read(self.path, columns=cols)
        return data.rebuild(table, {n: self.records[n] for n in names if n in self.records})

    def _question(self, name):
        if name not in self.records:
            raise KeyError(f"{name} isn't a variable of {self.release}/{self.table}")
        if not hasattr(self, "_cache"):
            self._cache = {}
        if name not in self._cache:
            col = self._columns([self.spec["id"], self.wave_column, name])
            self._cache[name] = {(p, w): v for p, w, v in zip(col[self.spec["id"]], col[self.wave_column], col[name])}
        return self._cache[name]

    # -------------------------------------------------------------- timing

    def _month(self, value):
        """A non-negative whole number (a month or an age), or None for a code or a blank."""
        try:
            v = int(value)
        except (TypeError, ValueError):
            return None
        return v if v >= 0 else None      # negative values are codes (NLS -5: no interview)

    def year_months(self, year):
        """The months of a calendar year on the interview_date scale."""
        if not self.month_zero:
            raise ValueError("a calendar year needs month_zero, the (year, month) of month 0 on the interview_date scale")
        y0, m0 = self.month_zero
        start = (int(year) - y0) * 12 + (1 - m0)
        return start, start + 11

    def _rounds(self, person):
        """[(wave, interview month or None, age or None, noninterview code)] for a person, in wave order."""
        rows = self._by_person.get(person)
        if rows is None:
            raise KeyError(f"no person {person!r}")
        out = []
        for _, r in rows.iterrows():
            age = self._month(r.get(self.spec["age_at_interview"])) if self.spec.get("age_at_interview") else None
            out.append((r[self.wave_column], self._month(r[self.spec["interview_date"][0]]), age,
                        r.get(self.spec.get("noninterview")) if self.spec.get("noninterview") else None))
        return out

    def _wording(self, rec, wave):
        plain = None
        for q in rec.get("questions") or []:
            if not q.get("waves"):
                plain = plain or q
            elif any(str(w) == str(wave) for w in q["waves"]):
                return q
        return plain or {}

    def _period(self, rec, wave, month, previous):
        q = self._wording(rec, wave)
        kind = q.get("reference_period")
        if month is None or kind is None:
            return None, kind
        if kind == "as_of_interview" or kind == "past_30_days":
            return (month, month), kind
        if kind == "since_last_interview":
            return ((previous + 1) if previous is not None else None, month), kind
        if kind == "past_months":
            return (month - q.get("months", 12) + 1, month), kind
        if kind == "ever":
            return (None, month), kind
        if kind == "calendar_year":
            return self.year_months(int(wave) - 1), kind
        return None, kind

    def _decode(self, rec, value):
        for v in rec.get("values") or []:
            if v["code"] == value:
                kind = "valid" if v.get("kind") == "valid" else ",".join(v.get("missing_types") or [v.get("kind")])
                return v.get("label"), kind
        return None, "valid"

    # -------------------------------------------------------------- queries

    def answers(self, name, person, *, year=None, age=None):
        """Every candidate round's answer for a question and a person, placed in time; never picks.

        year=Y: the rounds whose period overlaps year Y, with overlap_months.
        age=A: every interviewed round with the question, with distance_years from age A (0 first).
        Returns [Answer], or [NoAnswer] saying why there's none."""
        if (year is None) == (age is None):
            raise ValueError("give year= or age=")
        rec = self.records[name]
        values = self._question(name)
        asked = {w for sc in rec.get("source_columns") or [] for w in sc["waves"]}
        out, why = [], []
        previous = None
        span = self.year_months(year) if year is not None else None
        for wave, month, at_age, noninterview in self._rounds(person):
            this_previous, previous = previous, (month if month is not None else previous)
            if asked and wave not in asked:
                continue
            value = values.get((person, wave))
            if month is None:
                why.append(NoAnswer(name, person, wave, f"not interviewed (noninterview code {noninterview})"))
                continue
            label, kind = self._decode(rec, value)
            period, period_kind = self._period(rec, wave, month, this_previous)
            a = Answer(name=name, person=person, wave=wave, value=value, label=label, kind=kind,
                       interview_month=month, age=at_age, period=period, period_kind=period_kind,
                       universe=universe_at(rec.get("universe"), wave))
            if year is not None:
                if period is None:
                    why.append(NoAnswer(name, person, wave, "the wording states no reference period"))
                    continue
                lo = span[0] if period[0] is None else max(period[0], span[0])
                hi = min(period[1], span[1])
                if hi < lo:
                    continue
                a.overlap_months = hi - lo + 1
                a.how = f"{period_kind} period overlaps {year}"
            else:
                if at_age is None:
                    why.append(NoAnswer(name, person, wave, "no age at this interview"))
                    continue
                a.distance_years = at_age - age
                a.how = "interview at age " + str(at_age)
            out.append(a)
        if year is None:
            out.sort(key=lambda a: (abs(a.distance_years), a.distance_years))
        if out or why:
            return out or why
        if year is not None:
            return [NoAnswer(name, person, None, f"no round's period overlaps {year}")]
        return [NoAnswer(name, person, None, "no interview with this question")]


# ---------------------------------------------------------------- policies

POLICIES = ("exact", "nearest", "most_overlap", "latest")


def pick(candidates, policy):
    """Choose among answers() by a named policy; the result keeps the policy and the candidates.

    exact        age: an answer at that age (distance 0); year: a period inside the year (12 months
                 of overlap or the whole period). None if there's no such answer, or more than one.
    nearest      age: the smallest distance; a tie between before and after is reported, not broken.
    most_overlap year: the answer whose period covers most of the year; ties are reported.
    latest       the answer from the latest round among the candidates.
    Only valid answers are chosen; missing codes stay among the candidates."""
    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}")
    answers = [c for c in candidates if isinstance(c, Answer) and c.kind == "valid"]
    result = Picked(policy=policy, candidates=list(candidates))
    if not answers:
        result.note = "no valid answer among the candidates"
        return result
    if policy == "latest":
        result.answer = max(answers, key=lambda a: str(a.wave))
        return result
    if policy == "exact":
        fit = [a for a in answers if a.distance_years == 0 or
               (a.overlap_months is not None and a.period and a.period[0] is not None
                and (a.overlap_months >= 12 or a.overlap_months == a.period[1] - a.period[0] + 1))]
        if len(fit) == 1:
            result.answer = fit[0]
        else:
            result.note = f"{len(fit)} exact answers"
        return result
    if policy == "nearest":
        with_d = [a for a in answers if a.distance_years is not None]
        if not with_d:
            result.note = "nearest applies to age= queries"
            return result
        best = min(abs(a.distance_years) for a in with_d)
        tied = [a for a in with_d if abs(a.distance_years) == best]
        if len({a.value for a in tied}) > 1:
            result.note = f"{len(tied)} answers at distance {best} disagree"
            return result
        result.answer = tied[0]
        return result
    with_o = [a for a in answers if a.overlap_months is not None]
    if not with_o:
        result.note = "most_overlap applies to year= queries"
        return result
    best = max(a.overlap_months for a in with_o)
    tied = [a for a in with_o if a.overlap_months == best]
    if len({a.value for a in tied}) > 1:
        result.note = f"{len(tied)} answers with {best} months of overlap disagree"
        return result
    result.answer = tied[0]
    return result
