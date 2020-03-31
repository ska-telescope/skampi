CONFLUENCE_PWD="EnglandSignal08,"
CONFLUENCE_USER="g.leroux"
URL="https://confluence.skatelescope.org/rest/api/content/"
page_name="l_pi6_2"

expand="&expand=body.storage"
curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET "$URL?title=$page_name&spaceKey=SE$expand" |\
python -mjson.tool
