#!/bin/sh

if test -z "`which epydoc`"; then
	echo "Please install epydoc: pip install epydoc"
	exit
fi

if test ! -f setup.cfg -o ! -d openbiblio; then
	echo "Please run this script from the root of your openbiblio directory"
	exit
fi

epydoc -v \
	-n OpenBiblio \
	--no-frames \
	--no-private \
	--inheritance=grouped \
	-o openbiblio/public/docs \
	openbiblio ordf
