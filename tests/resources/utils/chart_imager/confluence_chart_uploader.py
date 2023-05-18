# coding=utf-8
"""
This is example to attach file with mimetype

"""
import logging
import linecache
import os

from atlassian import Confluence

logging.basicConfig(level=logging.DEBUG)

API_TOKEN = os.environ['CONFLUENCE_TOKEN']

confluence = Confluence(
    url="https://confluence.skatelescope.org",
    token = API_TOKEN,
)



def update_skampi_charts():
    PAGE_ID = "221065346"
    PAGE_TITLE = f"SKAMPI Chart Dependencies"
    TYPE = "page"
    REPRESENTATION = "storage"
    BODY = f"""
   <h2>Overview</h2>
    <p>
        <br />The below graphs shows a view of helm charts decomposition in SKAMPI mid and low.
        <br />The graphs created to make it easier to understand the helm charts used in SKAMPI mid and low are dependent on, their current versions, the flow/control.
    </p>
    <h2>SKAMPI Mid Chart</h2>
    <h2>
        <ac:image ac:style="max-height: 250.0px;" ac:height="400">
            <ri:attachment ri:filename="images/ska_mid_charts.png" />
        </ac:image>
     <br />SKAMPI Low Chart</h2>
    <p>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;<ac:image ac:style="max-height: 250.0px;" ac:height="150">
        <ri:attachment ri:filename="images/ska_low_charts.png" />
    </ac:image>&nbsp; &nbsp; &nbsp;</p>
    """
    try:
        response = confluence.update_page(
            page_id=PAGE_ID, title=PAGE_TITLE, body=BODY, type=TYPE, representation=REPRESENTATION, 
        )
        print(f"Confluence Page: https://confluence.skatelescope.org{response['_links']['webui']} Updated Successfully.")

    except Exception:
        return 1
    return 0


update_skampi_charts()