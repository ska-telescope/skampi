"""Simple echo server to demonstrate building OCI images"""

from bottle import route, run, template


@route("/<data:re:.*>")
def index(data):
    """serve the root URI and echo back the URI string"""
    return template("<b>Got: {{data}}</b>!\n", data=data)


run(host="0.0.0.0", port=8080, debug=True)
