.PHONY: pdf clean

VARIANT ?= draft
SUPPORTED_VARIANTS := draft anonymous camera-ready arxiv
VARIANT_FILE := $(subst -,_,$(VARIANT))
PDF_NAME := $(if $(filter draft,$(VARIANT)),main,main-$(VARIANT))
CLEAN_STEMS := main main-anonymous main-camera-ready main-arxiv
CLEAN_EXTENSIONS := pdf aux bbl bcf blg dvi fdb_latexmk fls lof log lot nav out ps run.xml snm synctex.gz toc vrb xdv
CLEAN_OUTPUTS := $(foreach stem,$(CLEAN_STEMS),$(foreach ext,$(CLEAN_EXTENSIONS),paper/$(stem).$(ext)))

pdf:
	@case " $(SUPPORTED_VARIANTS) " in *" $(VARIANT) "*) ;; *) echo "ERROR unsupported VARIANT=$(VARIANT); choose one of: $(SUPPORTED_VARIANTS)" >&2; exit 2 ;; esac
	@test -f "paper/variants/$(VARIANT_FILE).tex" || { echo "ERROR missing variant driver: paper/variants/$(VARIANT_FILE).tex" >&2; exit 2; }
	cd paper && latexmk -pdf -jobname="$(PDF_NAME)" -interaction=nonstopmode -halt-on-error "variants/$(VARIANT_FILE).tex"

clean:
	rm -f $(CLEAN_OUTPUTS)
