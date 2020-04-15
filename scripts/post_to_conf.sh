CONFLUENCE_PWD="EnglandSignal08,"
CONFLUENCE_USER="g.leroux"
URL="https://confluence.skatelescope.org/rest/api/content/"
page_name="Latest+Version+-+PI6"
humane_page_name="Latest Version - PI6"
Space="SWSI"

HELM_RELEASE=test
KUBE_NAMESPACE=integration
date=$(date)
head="{'<p>The following table lists the deployment status as recorded on $date</p><p><table><colgroup><col/><col/><col/></colgroup><tbody><tr><th>Pod</th><th>Container</th><th>Image</th></tr>'}"
path="$head{range .items[*]}"
path="$path{'<tr><td>'}{.metadata.name}{'</td><td></td><td></td></tr>'}"
path="$path{range .spec.containers[*]}"
path="$path{'<tr><td></td><td>'}{.name}{'</td><td>'}{.image}{'</td></tr>'}"
path="$path{end}"
path="$path{end}{'</tbody></table></p>'}"
content=$(kubectl get pods -n $KUBE_NAMESPACE -o jsonpath="$path")


##get the page id
page_id=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET "$URL?title=$page_name&spaceKey=$Space" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['id']")
#hget the page versionF
page_version=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET \
 "$URL?title=$page_name&spaceKey=$Space&expand=version" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['version']['number']")
echo "setting up for $page_id version $(($page_version + 1))"
page_version=$(($page_version + 1))

##data specification
data="{\"id\":\"$page_id\","
data="$data\"type\":\"page\","
data="$data\"title\":\"$humane_page_name\","
data="$data\"space\":{\"key\":\"$Space\"},"
data="$data\"body\":"
data="$data{   \"storage\":"
data="$data{       \"value\":"
data="$data                 \"$content\""
data="$data,       \"representation\":\"storage\"}},"
data="$data\"version\":"
data="$data{   \"number\":\"$page_version\"}}"
#################################################


curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X PUT -H 'Content-Type: application/json' -d "$data" $URL$page_id | python -mjson.tool


##########################################section on imges
page_name="Images"
humane_page_name="Images"

path="{range .items[*]}"
path="$path{range .spec.containers[*]}"
path="$path{.image}{'\t\t'}{.name}{'\n'}"
path="$path{end}{'\n'}"
head="<p>The following table lists images used by pods as recorded on $date</p><p><table><colgroup><col /><col /></colgroup><tbody><tr><th>Image</th><th>Container</th></tr>"
results=$(kubectl get pods -n $KUBE_NAMESPACE -o jsonpath="$path" | uniq | sort | awk 'NR > 1 {print "<tr><td>" $1 "</td><td>" $2 "</td></tr>"}')
content="$head$results</tbody></table></p>"
content=${content//$'\n'/}
echo "$content" > "test.html"
##get the page id
page_id=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET "$URL?title=$page_name&spaceKey=$Space" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['id']")
#hget the page versionF
page_version=$(curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X GET \
 "$URL?title=$page_name&spaceKey=$Space&expand=version" |\
 python -mjson.tool |\
 python2 -c "import sys, json; print json.load(sys.stdin)['results'][0]['version']['number']")
echo "setting up for $page_id version $(($page_version + 1))"
page_version=$(($page_version + 1))



##data specification
data="{\"id\":\"$page_id\","
data="$data\"type\":\"page\","
data="$data\"title\":\"$humane_page_name\","
data="$data\"space\":{\"key\":\"$Space\"},"
data="$data\"body\":"
data="$data{   \"storage\":"
data="$data{       \"value\":"
data="$data                 \"$content\""
data="$data,       \"representation\":\"storage\"}},"
data="$data\"version\":"
data="$data{   \"number\":\"$page_version\"}}"
#################################################

curl -u $CONFLUENCE_USER:$CONFLUENCE_PWD -X PUT -H 'Content-Type: application/json' -d "$data" $URL$page_id | python -mjson.tool