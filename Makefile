.PHONY: pdf clean

VARIANT ?= draft
SUPPORTED_VARIANTS := draft anonymous camera-ready arxiv
VARIANT_FILE := $(subst -,_,$(VARIANT))
PDF_NAME := $(if $(filter draft,$(VARIANT)),main,main-$(VARIANT))

pdf:
	@case " $(SUPPORTED_VARIANTS) " in *" $(VARIANT) "*) ;; *) echo "ERROR unsupported VARIANT=$(VARIANT); choose one of: $(SUPPORTED_VARIANTS)" >&2; exit 2 ;; esac
	@test -f "paper/variants/$(VARIANT_FILE).tex" || { echo "ERROR missing variant driver: paper/variants/$(VARIANT_FILE).tex" >&2; exit 2; }
	cd paper && latexmk -pdf -jobname="$(PDF_NAME)" -interaction=nonstopmode -halt-on-error "variants/$(VARIANT_FILE).tex"

clean:
	cd paper && latexmk -C variants/draft.tex variants/anonymous.tex variants/camera_ready.tex variants/arxiv.tex || true
	rm -f paper/main*.pdf paper/main*.aux paper/main*.bbl paper/main*.blg paper/main*.fdb_latexmk paper/main*.fls paper/main*.log paper/main*.out
