# Datasets from Twenge's *Generations*

The datasets Jean Twenge lists in *Generations* (2023), transcribed from the book's table of datasets, with where each stands in this project. They're a catalog of high-priority datasets: widely used, long-running, and mostly public.

The table below has 20 rows, from two screenshots of the book's table. The book's total is 39,198,141 respondents. Rows between the two screenshots, if there are any, are missing.

| Dataset | Ages | Agency | Years | People | Here | Likely terms (unverified unless marked) |
|---|---|---|---|---|---|---|
| Monitoring the Future | 12th graders | U. of Michigan; NIH | 1976–2021 | 692,817 | preliminary work; waiting on ICPSR about LLM use ([next_datasets.md](next_datasets.md)) | ICPSR: registration, no redistribution |
| Youth Risk Behavior Surveillance System and Adolescent Behavior and Experiences Survey | 9th–12th graders | CDC | 1991–2021 | 224,283 | **built**, `pdt-yrbss` (YRBSS only; Task 29) | verified: CDC, everything ships |
| Health Behaviour in School-Aged Children (international) | 13–15 | WHO | 2002–2018 | 650,504 | — | data by application |
| Millennium Cohort Study (UK) | 14 | University College London | 2000–2015 | 10,904 | — | UK Data Service: registration, no redistribution |
| Programme for International Student Assessment (international) | 15–16 | OECD | 2000–2018 | 1,049,784 | **in progress**, `pdt-pisa` (Task 45) | verified: OECD, everything ships |
| World Values Survey (international) | 15+ | World Values Survey Association | 1981–2020 | 28,809 | — | free download with registration; redistribution restricted |
| American Time Use Survey | 15+ | Bureau of Labor Statistics | 2003–2021 | 219,673 | — | federal, probably everything ships |
| Current Population Survey, Annual Social and Economic Supplement | 15+ | Census Bureau, BLS | 1947–2021 | ~7,000,000 | **built**, `pdt-cps-asec`, 2019–2025 (Task 32) | verified: everything ships |
| American Freshman Survey | incoming college students | UCLA | 1966–2019 | 10,551,020 | — | HERI: limited access |
| Panel Study of Income Dynamics | 18+ | U. of Michigan | 1968–2019 | 90,264 | — | registration, no redistribution |
| General Social Survey | 18+ | NORC, U. of Chicago | 1972–2021 | 68,846 | **built**, `pdt-gss` (Tasks 5, 21, 26) | verified |
| Behavior Risk Factor Surveillance System | 18+ | CDC | 1993–2021 | 9,550,207 | **built**, `pdt-brfss`, 2011–2023 (Task 30) | verified: CDC, everything ships |
| National Health Interview Survey | 18+ | CDC | 1997–2021 | 1,835,337 | — | federal (NCHS), probably everything ships |
| Gallup poll | 18+ | Gallup, Inc. | 2001–2022 | 22,842 | — | proprietary |
| Cooperative Election Study | 18+ | Harvard and YouGov | 2006–2021 | 531,755 | — | Harvard Dataverse, open download |
| Pew Research Center polls | 18+ | Pew Charitable Trusts | 2010–2018 | 17,021 | — | free with registration; redistribution restricted |
| CIVIQs poll | 18+ | CIVIQs | 2017–2022 | 345,605 | — | proprietary |
| Nationscape | 18+ | Democracy Fund | 2019–2021 | 413,790 | — | free by request |
| Voter Survey | 18+ | Democracy Fund | 2020 | 4,943 | — | free download |
| Household Pulse Survey | 18+ | Census Bureau | 2020–2022 | 3,339,697 | — | federal, probably everything ships |

The ANES isn't in the book's table, although `pdt-anes-cdf` exists here.

## What to do next

The best next datasets are federal or open, so nothing waits on permissions:
1. **National Health Interview Survey** (NCHS): annual since 1957, with documentation like the NSFG's.
2. **American Time Use Survey** (BLS): activity codes are a large shared code list, a good test of §4.5.
3. **Household Pulse Survey** (Census): weekly waves since 2020 with changing questionnaires, a test of availability and links.
4. **Cooperative Election Study** (Harvard Dataverse): a cumulative file plus yearly files, like the ANES.

The rest need registration, an application or a purchase. For those, the restricted path (metadata only, data fetched by hand) is the test.
