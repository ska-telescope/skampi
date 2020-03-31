CONFLUENCE_PWD="EnglandSignal08,"
CONFLUENCE_USER="g.leroux"
URL="https://confluence.skatelescope.org/rest/api/content/"
page_name="l_pi6_2"

#echo "getting page from URL $URL?title=$page_name&spaceKey=SE&expand=body.storage"
#curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET "$URL?title=$page_name&spaceKey=SE&expand=version" |\
# python -mjson.tool
##get the page id
page_id=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET "$URL?title=$page_name&spaceKey=SE" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['id']")
#hget the page version
page_version=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET |\
 "$URL?title=$page_name&spaceKey=SE&expand=version" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['version']['number']")
echo "setting up for $page_id version $(($page_version + 1))"
#get the current content
current_content=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET |\
"$URL?title=$page_name&spaceKey=SE&expand=v" |\
python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['version']['number']"))
page_version=$(($page_version + 1))
echo "curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X PUT -H 'Content-Type: application/json' -d {'id':'$page_id','type':'page','title':'$page_name','space':{'key':'SE'},'body':{'storage':{'value':'<p>Tupdated page</p>','representation':'storage'}},'version':{'number':'$page_version'}} $URL$page_id | python -mjson.tool"
##data specification
data="{\"id\":\"$page_id\","
data="$data\"type\":\"page\","
data="$data\"title\":\"$page_name\","
data="$data\"space\":{\"key\":\"SE\"},"
data="$data\"body\":"
data="$data{   \"storage\":"
data="$data{       \"value\":"
data="$data                 \"<p>updated page</p>\""
data="$data,       \"representation\":\"storage\"}},"
data="$data\"version\":"
data="$data{   \"number\":\"$page_version\"}}"
#################################################


curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X PUT -H 'Content-Type: application/json' -d "$data" $URL$page_id | python -mjson.tool
