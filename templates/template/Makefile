PYTHON ?= python
# A PublicDataToolkit checkout. Or `pip install -e $(PDT)` and run `pdt check`.
PDT ?= ../PublicDataToolkit
# The subject prefix of the DAAF skill name (make export-daaf): health, social, education, ...
DAAF_DOMAIN ?=

.PHONY: download build views check export-daaf

## Fetch the sources into data/raw. Read the publisher's terms first, then: make download ARGS=--accept-terms
download:
	PYTHONPATH=$(PDT)/lib $(PYTHON) scripts/download.py $(ARGS)

## Build metadata records from data/raw (build/build_records.py writes build/report.md)
build:
	$(PYTHON) build/build_records.py

## Generate agent/, docs/ and export/ from the records (pdt views).
## VIEWS_ARGS="--only site" builds docs/ alone, as the Pages workflow does.
views:
	PYTHONPATH=$(PDT)/lib $(PYTHON) -m pdt views . $(VIEWS_ARGS)

## Check the repo against the PublicDataToolkit standard (pdt check)
check:
	PYTHONPATH=$(PDT)/lib $(PYTHON) -m pdt check .

## On request: export/daaf/, this dataset as a DAAF data-source skill (pdt export daaf).
## DAAF_DOMAIN is the subject prefix of the skill's name, as in DAAF's education-data-source-ccd.
export-daaf:
	@test -n "$(DAAF_DOMAIN)" || { echo "Set DAAF_DOMAIN, e.g. make export-daaf DAAF_DOMAIN=health"; exit 1; }
	PYTHONPATH=$(PDT)/lib $(PYTHON) -m pdt export daaf . --domain $(DAAF_DOMAIN)
