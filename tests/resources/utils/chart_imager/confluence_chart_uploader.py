"""
The python script will upload the images to the provided confluence page id and page title.
"""
import logging
import sys,os

from atlassian import Confluence

logging.basicConfig(level=logging.DEBUG)

API_TOKEN = os.environ['RT_API_TOKEN']
DIR_NAME = os.path.dirname(sys.argv[0])
DIR_PATH = os.path.abspath(DIR_NAME)

confluence = Confluence(
    url="https://confluence.skatelescope.org",
    token = API_TOKEN,
)



def update_skampi_charts():
    PAGE_ID = "221065346"
    PAGE_TITLE = "SKAMPI Chart Dependencies"
    TYPE = "page"
    REPRESENTATION = "storage"
    BODY = f"""
   <h2>Overview</h2>
    <p>
        <br />The below graphs shows a view of helm charts decomposition in SKAMPI mid and low.
        <br />The graphs created to make it easier to understand the helm charts used in SKAMPI mid and low are dependent on, their current versions, the flow/control.
    </p>
    <h2>SKAMPI Mid Chart</h2>
    <h2><ac:image ac:style="max-height: 250.0px;" ac:height="400">
        <ri:attachment ri:filename="{DIR_PATH}/images/ska_mid_charts.png" />
    </ac:image>
    <br />SKAMPI Low Chart</h2>
    <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;<ac:image ac:style="max-height: 250.0px;" ac:height="250">
        <ri:attachment ri:filename="{DIR_PATH}/images/ska_low_charts.jpg" />
    </ac:image>
    </p>
    """

    response = confluence.update_page(
        page_id=PAGE_ID, title=PAGE_TITLE, body=BODY, type=TYPE, representation=REPRESENTATION, 
    )
    print(f"SKAMPI Chart Dependencies Confluence Page: https://confluence.skatelescope.org{response['_links']['webui']}")


update_skampi_charts()
