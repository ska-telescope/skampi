import requests
import json
import sys
import pprint
import re

# This script retrieves all the members of the group ska-telescope and return them as a valid string to be put in charts/auth/values.yaml

headers = {'PRIVATE-TOKEN': '6YgsopqwUS_DMj7sw_Sz'}

def get(url):
    """ Retrieve given URL with token header """
    print ("GET " + url)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def get_json(url):
    """ Retrieve URL and parse as JSON """
    return json.loads(get(url))

# Base URLs
api_base = "https://gitlab.com/api/v4/"
page=1

json_members = get_json("https://gitlab.com/api/v4/groups/3180705/members?per_page=100&page=" + str(page))
output_members = []
count = len(json_members)

while len(json_members) > 0:
    for member in json_members:
        #pprint.pprint(member)
        output_members.append("https://gitlab.com#" + str(member["id"]))

    page=page + 1
    json_members = get_json("https://gitlab.com/api/v4/groups/3180705/members?per_page=100&page=" + str(page))
    count = count + len(json_members)

print ("Total members= "+ str(count))
print ("***********************")
print(output_members)
print ("***********************")

page=1
json_proj = get_json("https://gitlab.com/api/v4/groups/3180705/projects?per_page=100&page=" + str(page))
output_proj = []
count = len(json_proj)
count_branches = 0

while len(json_proj) > 0:
    for proj in json_proj:
        try:
            json_branches = get_json("https://gitlab.com/api/v4/projects/" + str(proj["id"])+ "/repository/branches?per_page=100&page=1")
            count_branches = count_branches + len(json_branches)
            print("Project " + str(proj["description"]) + " has " + str(len(json_branches)) + " branches.")
            output_proj.append(str(proj["name"]) + "\t" + str(len(json_branches)))
        except:
            pass

    page=page + 1
    json_proj = get_json("https://gitlab.com/api/v4/groups/3180705/projects?per_page=100&page=" + str(page))
    count = count + len(json_proj)

print ("Total Projects= "+ str(count))
print ("Total Branches= "+ str(count_branches))
print ("***********************")
print(output_proj)
print ("***********************")
