# Imagem Cinematica, 2016
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


#Recursively applies a wildcard to the files and directories
#http://stackoverflow.com/questions/3774568/makefile-issue-smart-way-to-scan-directory-tree-for-c-files
rwildcard=$(wildcard $1$2) $(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2))

#The resources directory
RES_DIR := resources/res

#The directory that compiled resource files will be inserted
OUTPUT_RES_DIR := gui

#The directory that the ts files will be inserted
OUTPUT_TS_DIR := lang/ts

#The directory that the compiled ts files will be inserted
OUTPUT_QM_DIR := lang/qm

#The list of locales to generate .ts files
LOCALE_LIST := pt_BR

#Gather all .qrc files inside the res directory
RES_FILES  := $(wildcard $(RES_DIR)/*.qrc)
#Create a string containing all the compiled file names
COMPILED_RES_FILES := $(patsubst $(RES_DIR)/%.qrc,$(OUTPUT_RES_DIR)/%_rc.py,$(RES_FILES))

#Create a list with the ts files based on the locales
TS_FILES := $(patsubst %,$(OUTPUT_TS_DIR)/%.ts,$(LOCALE_LIST))

#Create a list with the qm files based on the locales
QM_FILES := $(patsubst %,$(OUTPUT_QM_DIR)/%.qm,$(LOCALE_LIST))

#Get all the .ui files inside the resource files
UI_FILES := $(call rwildcard,plugins,*.ui) $(call rwildcard,resources/ui,*.ui)

#Create a list with all the .ui files that will be outputed by the pyuic4
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
.PHONY:  qrc

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


################### Recipe for compiling the resources files ###################
qrc : $(COMPILED_RES_FILES)
	@echo "Resource files compiled!"

$(OUTPUT_RES_DIR)/%_rc.py: $(RES_DIR)/%.qrc
	@pyrcc4 $< -o $@

########## Recipe for creating the ts files, based on the project.pro ##########
ts :
	@echo "Generating .ts files..."
	@pylupdate4 -translate-function tr -noobsolete project.pro

####################### Recipe for compiling the qm files ######################
qm : $(QM_FILES)
	@echo "Linguist files (.qm) compiled!"

#Recipe for compiling the .ts files into .qm
$(OUTPUT_QM_DIR)/%.qm: $(OUTPUT_TS_DIR)/%.ts
	@cp $< $(OUTPUT_QM_DIR)
	@lrelease $(patsubst $(OUTPUT_QM_DIR)/%.qm,$(OUTPUT_QM_DIR)/%.ts,$@)
	@rm $(patsubst $(OUTPUT_QM_DIR)/%.qm,$(OUTPUT_QM_DIR)/%.ts,$@)

####################### Recipe for compiling the ui files ######################
uic : $(COMPILED_UI_FILES)
#Compile the ui files using the pyuic4 and output to the tmp dir
#These files are useful for extracting the retranslateUi function


tmp/%.py :
	@printf "Generating %s...\n" $@
	@mkdir -p $(dir $@)
	@pyuic4 $(patsubst tmp/%.py,%.ui,$@) -x -o $@
	
#pyuic4 $< -o $@




#TS FILES WILL NOT BE REMOVED SINCE IT CAN LEAD TO WORK LOSS
clean:
	@rm -rf $(COMPILED_RES_FILES) $(QM_FILES) tmp/* project.pro
