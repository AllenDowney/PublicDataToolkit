# Step 5. Record availability

**Goal:** each record says which waves, forms, samples, modes and phases have the variable, so structural queries ("every item on ballot A in 1988") can be answered exactly. `pdt search`'s `available` filter is only as good as this field.

**Standard:** §4.1 (`availability`), §2.1 (`dimensions`), §7 (completeness labels follow the field's origin).

## Do

1. **Take availability from the publisher** when it documents it:
   - gssrdoc's year-by-ballot table for the GSS;
   - the ANES codebook's Sources section (years);
   - a FARS manual period (years).

   An entry with only `wave` means everyone in that wave. An entry with `form` means only that form.
2. **Count it in the data** when the publisher doesn't document it. gssrdoc has no yearly counts for weights such as `wtssps`, so the build counted non-missing values per year and labeled the field `origin: data_file`. Put `n` on each entry when you have it.
3. **Record phase or mode** only when a source says so. The ANES CDF's pre/post phase is stated in one variable's notes ("This is a pre var.") and only implied elsewhere, so `phase` is nearly empty. Leave it empty rather than guess from labels (rule 4).
4. **Give the field its origin.** The completeness label of an `available` search depends on it: a `publisher`, `upstream_package` or `data_file` origin gives `complete`; a `rule` origin, such as ANES's `anes_phase`, gives `complete_by_rule`.

## Check against the data before moving on

This is C5 (warn). The build does it for now and lists every difference in its report.

- [ ] **Every wave in `availability` has non-missing values in the data, and every wave with values is in `availability`.** The ANES build found Sources that omit years with data: 2016 for VCF0878 and VCF0704, 1954 for VCF0104, VCF0128 and VCF0301, and 2012 for VCF0830. Each became a correction (step 6).
- [ ] **Counts match**, where the source gives them. A count that differs in one wave is how the GSS build found that gssrdoc documented an earlier release (`racopen` 2024: 462 vs 981).
- [ ] **Gaps are real.** The GSS has no 1986 data for `abany` but does have a 1986 wave. Make sure a skipped wave is a skipped wave, not a parser miss.
- [ ] **Forms add up.** For a ballot-split item, the forms recorded for a year should be the forms whose respondents have values in that year.

## Stop and ask a person

- When the publisher's availability and the data disagree in a way that isn't a simple omission (counts that differ in one wave, for example), say what you found and what the options are.
