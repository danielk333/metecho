CC=gcc
CFLAGS=-fPIC
LIBS=-lm

SOURCES=$(wildcard **/*.c)
OBJECTS=$(SOURCES:.c=.o)
EXT=$(shell python -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
OUTLIB=clibmet$(EXT)

all: $(OUTLIB)

%.o: %.c
	@echo "metecho installation -> Compiling source file $< ..."
	$(CC) -c $(CFLAGS) -o $@ $<

$(OUTLIB): $(OBJECTS)
	@echo "metecho installation -> Linking shared library $@ ..."
	$(CC) $(CFLAGS) -shared $(OBJECTS) $(LIBS) -o $@
	@mv $@ ../metecho/ -v
	@echo "metecho installation -> The shared library $< has been created successfully."

clean:
	@echo "metecho installation -> Removing object files *.o ..."
	@-rm -f *.o
	@echo "metecho installation -> Removing shared library *.so ..."
	@-rm -f *.so
