"""
The python script will upload the images to the provided confluence page id and page title.
"""
import logging
import os

#import magic commented as libmagic library not available on SKAMPI
import sys

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
    BODY = """
    <h2>Overview</h2>
    <p>
        <br />The below graphs shows a view of helm charts decomposition in SKAMPI mid and low. 
        <br />The graphs created to make it easier to understand the helm charts used in SKAMPI mid and low are dependent on, their current versions, the flow/control.
    </p>
    <h2>SKAMPI Mid Chart</h2>
    <h2><ac:image ac:height="400">
        <ri:attachment ri:filename="ska_mid_charts.png" />
        </ac:image>
    </h2>
    <h2><br />SKAMPI Low Chart</h2>
    <p><br /></p>
    <p><ac:image ac:height="250">
        <ri:attachment ri:filename="ska_low_charts.png" />
        </ac:image>
    </p>
    <p><br /></p>
    """

    PAGE_ID = "221065346"
    PAGE_TITLE = "SKAMPI Chart Dependencies"
    TYPE = "page"
    REPRESENTATION = "storage"
    SPACE = "TS"
    image_names = ["ska_low_charts.png","ska_mid_charts.png"]

    for image_name in image_names:
        file_absolute_path = f"{DIR_PATH}/images/{image_name}"
        #mime_type = magic.from_file(file_absolute_path, mime=True)
        #upload the images to confluence page first.
        try:
            confluence.attach_file(
                filename=file_absolute_path,
                name=image_name,
                #content_type=mime_type,
                content_type="image/png", #currently on skampi libmagic library is not installed, so directly providing the value o mime_type
                page_id=PAGE_ID,
                space=SPACE
            )
        except Exception as err:
            logging.error(f"Error: {err}")
    
    #Update the confluence page
    try:
        response = confluence.update_page(
            page_id=PAGE_ID, title=PAGE_TITLE, body=BODY, type=TYPE, representation=REPRESENTATION, 
        )
        print(f"SKAMPI Chart Dependencies Confluence Page: https://confluence.skatelescope.org{response['_links']['webui']}")
    
    except Exception as err:
        logging.error(f"Error: {err}")

update_skampi_charts()
