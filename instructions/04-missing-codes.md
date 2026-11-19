# Step 4. Type the missing codes

**Goal:** every code in every record is `valid`, `missing` with its `missing_types`, or `unresolved`, and each missing or unresolved code has an origin. Recoding by type (DK to one value, INAP to another) depends on this being right.

**Standard:** §4.2 (values and missing codes, the eleven types, the order of preference), §5.3 (a correction can classify a code).

## Do

Decide which codes are missing in this order (§4.2), and record the origin of each decision:

1. **The publisher marks them.** The ANES codebook has a "Missing" section, and NORC has reserved codes. `origin: publisher`. Keep the publisher's split even when a label looks wrong: ANES VCF0803 code 9, "DK; haven't thought much about it," is listed under Valid, so it's valid.
2. **The data file marks them.** Stata extended missing values (`.d`, `.i`, `.y`) are missing by construction. `origin: data_file`. The *type* then comes from the label, by a named rule (`gss_extended_missing_types`).
3. **A rule over labels,** only when neither of the above exists. The NSFG codebook lists "Refused 8", "Don't know 9" and "Inapplicable ." as ordinary rows, so the rule `nsfg_missing_from_labels` types them. FARS is similar (`fars_missing_from_labels`).
4. **A person or an agent** adds what the others miss. `origin: hand`, with the real author named (STANDARD.md §3).

When many codes share an origin, set it once in `provenance.codes` (§4.2). That made the GSS records 13% smaller.

**Choose types by what the code means in this dataset:**
- **FARS "Unknown" is `unknown`, not `dk`.** It's a census coded from police reports, and no respondent was asked anything.
- **GSS `.z` "see codebook" is `unspecified`:** the data says missing and gives no reason.
- **A label can carry several reasons:** ANES "NA; no Post IW; form III,IV (1972)". Split it at ";" and type each part. Parts the rule can't type ("don't recognize", "breakoff") go in the build report.
- **One code can have several types:** GSS `.m` "dk, na, iap" is `dk`, `no_answer` and `inap`.

## Check against the data before moving on

- [ ] **C4: every code that occurs in the data is in `values`.** The ANES build found `-1` in VCF0806 (245 cases), `-8` in VCF0218, `-4` in VCF0206, and code 2 in VCF0878 (1,130 cases), none of them in the codebook.
- [ ] **Undocumented codes are `unresolved`, never guessed.** A wrong type is worse than an open one, because recoding code trusts it (§4.2). A code becomes `missing` or `valid` only through a correction with evidence (step 6), as the ANES `-1` and `-8` codes did.
- [ ] **Codes that occur but whose label looks like a missing value** (a numeric code labeled "DK" in a variable whose publisher lists it as valid) stay as the publisher has them and appear in the report.
- [ ] **Which extended missing values occur, per variable.** gssrdoc lists the same twelve `NA(x)` codes for every variable. Read from the data which ones each variable actually uses: `.d`, `.i` and `.n` in most, `.s` in about two thirds, `.y` in a few.
- [ ] **Ranges allow for rounding.** The NSFG codebook prints the weight's range rounded ("1170.96-78770.13"). Compare with half a unit of the last printed digit.
- [ ] `pdt check` passes. Its report counts unresolved codes; each one is listed in `build/report.md` with what was checked.
- [ ] The report's table of missing types assigned looks plausible (the ANES: 66 `not_asked`, 34 `no_answer`, 23 `dk`, ...).

## Stop and ask a person

- When a code's meaning would change an analysis (a frequent undocumented code, like ANES VCF0878's 1,130 code-2 cases), report it and propose a correction. Don't classify it quietly.
