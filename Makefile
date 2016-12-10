# Copyright (C) 2016  Bruno Abude Cardoso
#
# Imagem Cinemática is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Imagem Cinemática is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This makefile contains rules for generating the Qt Linguist translation files.
# The `translation` target will extract any translation info from the python
# file sources and from the .ui files and generate the .ts files for each one of
# the locales in the LOCALE_LIST.
#
# The `release` target will compile the .ts files into .qm files.
# The `pro` is an intermediary target that will generate a .pro file containing
# all the located .ui and .py files so the pylupdate4 can extract info from it.
#
# The `uic` target is just an utility that will compile all the .ui files
# located under resources/ui using the pyuic4 tool and output them to the 'tmp'
# dir. This is useful for extracting the retranslateUi function that is
# generated.
#
# The 'qrc' target will compile all .qrc files located under resources/res
# using pyrcc4 and output them to the 'gui' package.


# Recursively applies a wildcard to the files and directories
# http://stackoverflow.com/questions/3774568/makefile-issue-smart-way-to-scan-directory-tree-for-c-files
rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))
RES_DIR := resources/res
OUTPUT_RES_DIR := gui
OUTPUT_TS_DIR := lang/ts
OUTPUT_QM_DIR := lang/qm
LOCALE_LIST := pt_BR
RES_FILES  := $(wildcard $(RES_DIR)/*.qrc)
COMPILED_RES_FILES := $(patsubst $(RES_DIR)/%.qrc,$(OUTPUT_RES_DIR)/%_rc.py,$(RES_FILES))
TS_FILES := $(patsubst %,$(OUTPUT_TS_DIR)/%.ts,$(LOCALE_LIST))
QM_FILES := $(patsubst %,$(OUTPUT_QM_DIR)/%.qm,$(LOCALE_LIST))
UI_FILES := $(call rwildcard,plugins,*.ui) $(call rwildcard,resources/ui,*.ui)
COMPILED_UI_FILES := $(patsubst %.ui,tmp/%.py,$(UI_FILES))

# Fid all py files inside the given directories (gui, util, plugins)
PY_FILES := $(call rwildcard,gui,*.py) $(call rwildcard,util,*.py)\
$(call rwildcard,plugins,*.py) imagem_cinematica.py
PY_FILES := $(abspath $(PY_FILES))

.PHONY: all
.PHONY: clean
.PHONY: ts
.PHONY: qm
.PHONY: uic
.PHONY: pro
.PHONY: release
.PHONY: translation
.PHONY: qrc

all : qrc pro ts qm
translation : pro ts
release : qrc qm

pro :
	@echo "Generating project.pro file..."
	@rm -f project.pro
	@echo "SOURCES      = $(PY_FILES)" >> project.pro
	@echo "FORMS        = $(UI_FILES)" >> project.pro
	@echo "TRANSLATIONS = $(TS_FILES)" >> project.pro
	@echo "CODECFORTR   = utf-8"     >> project.pro


qrc : $(COMPILED_RES_FILES)
	@echo "Resource files compiled!"

$(OUTPUT_RES_DIR)/%_rc.py: $(RES_DIR)/%.qrc
	@pyrcc4 $< -o $@

ts :
	@echo "Generating .ts files..."
	@pylupdate4 -translate-function tr -noobsolete project.pro

qm : $(QM_FILES)
	@echo "Linguist files (.qm) compiled!"

$(OUTPUT_QM_DIR)/%.qm: $(OUTPUT_TS_DIR)/%.ts
	@cp $< $(OUTPUT_QM_DIR)
	@lrelease $(patsubst $(OUTPUT_QM_DIR)/%.qm,$(OUTPUT_QM_DIR)/%.ts,$@)
	@rm $(patsubst $(OUTPUT_QM_DIR)/%.qm,$(OUTPUT_QM_DIR)/%.ts,$@)

uic : $(COMPILED_UI_FILES)

tmp/%.py :
	@printf "Generating %s...\n" $@
	@mkdir -p $(dir $@)
	@pyuic4 $(patsubst tmp/%.py,%.ui,$@) -x -o $@


# TS FILES WILL NOT BE REMOVED SINCE IT CAN LEAD TO WORK LOSS
clean:
	@rm -rf $(COMPILED_RES_FILES) $(QM_FILES) tmp/* project.pro
