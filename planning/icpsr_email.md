# Draft email to ICPSR about Monitoring the Future

**To:** icpsr-help@umich.edu (ICPSR and NAHDAP help). **Cc:** mtfinformation@umich.edu (the MTF team's address for data questions). **Status:** draft for Allen to edit and send. Not sent.

Both addresses come from search results. The ICPSR site is behind a bot check, so the pages couldn't be opened to confirm them. Sources: the [NAHDAP help page](https://www.icpsr.umich.edu/sites/nahdap/help) and [an MTF study record](https://www.icpsr.umich.edu/web/NAHDAP/studies/39445/versions/V1/staff).

---

**Subject:** Using MTF 12th-grade documentation with an LLM, and publishing variable-level metadata

Hello,

I'm working on an open-source project, PublicDataToolkit (https://github.com/AllenDowney/PublicDataToolkit), that builds machine-readable metadata for public survey datasets: variable names, labels, question text, response codes with typed missing values, and the years and questionnaire forms in which each item was asked. We would like to include Monitoring the Future, starting with the public-use 12th-grade files (for example, study 39444, 2024), and the cross-time question index in the User Guide.

Before we go further, I have three questions about ICPSR's terms and your Policy on the Use of Large Language Models.

1. **LLM processing of documentation.** Our tools use a commercial LLM to help parse codebooks into structured records. We would send only documentation (the PDF codebooks and the User Guide), never respondent-level data. Does the LLM policy cover documentation as well as data? If it does, under what conditions, if any, may documentation be processed by an LLM?

2. **Publishing derived metadata.** Could we publish variable-level metadata derived from the MTF codebooks under an open license, with citation of the study and ICPSR? That would be names, labels, question text, code labels, and availability by year and form. Or should we publish only the code that builds this metadata from files each user downloads?

3. **Machine-readable metadata.** Is variable-level metadata for MTF (for example, DDI with variable descriptions) available through ICPSR's Metadata Export API? If so, we would rather build from that than from PDFs.

We won't redistribute MTF data files or documentation, and we would follow whatever conditions you set for the metadata.

Thank you,

Allen Downey
