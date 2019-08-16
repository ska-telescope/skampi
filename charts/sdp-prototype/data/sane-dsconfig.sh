json2tango $*
RET=$?
if [ $RET == 2 ]; then
	exit 0
else
	exit $RET
fi