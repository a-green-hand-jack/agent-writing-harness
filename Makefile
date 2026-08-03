.PHONY: pdf clean

pdf:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	cd paper && latexmk -C
