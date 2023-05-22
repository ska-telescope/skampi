"""
The python script will upload the images to the provided confluence page id and page title.
"""
import logging
import os
import sys

from atlassian import Confluence

# import magic commented as libmagic library not available on SKAMPI


# Enable below instruction for debugging
# logging.basicConfig(level=logging.DEBUG)

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.environ["RT_API_TOKEN"]
DIR_NAME = os.path.dirname(sys.argv[0])
DIR_PATH = os.path.abspath(DIR_NAME)

# Get access to confluence
confluence = Confluence(
    url="https://confluence.skatelescope.org",
    token=API_TOKEN,
)


def update_skampi_charts():
    """
    Function to Upload the SKAMPI chart images
    :param PAGE_ID: Confluence url page id
    :type  PAGE_ID: ``integer constant``
    :param PAGE_TITLE: Confluence page url
    :type  PAGE_TITLE: ``string constant``
    :param SPACE: Confluence page space
    :type SPACE: ``string constant``
    :param image_names: list of image names
    :type image_names: ``list``
    """
    PAGE_ID = "221065346"
    PAGE_TITLE = "SKAMPI Chart Dependencies"
    SPACE = "TS"
    image_names = ["ska_low_charts.png", "ska_mid_charts.png"]

    for image_name in image_names:
        file_absolute_path = f"{DIR_PATH}/images/{image_name}"
        # mime_type = magic.from_file(file_absolute_path, mime=True)

        # Upload the images to confluence page.
        try:
            response = confluence.attach_file(
                filename=file_absolute_path,
                name=image_name,
                # content_type=mime_type,
                # currently on SKAMPI libmagic library is not installed,
                # so directly providing the value of mime_type
                content_type="image/png",
                page_id=PAGE_ID,
                title=PAGE_TITLE,
                space=SPACE,
                comment=f"Uploaded SKAMPI {image_name.split('_')[1]} chart {image_name} ",
            )
            logging.info(
                f"{response['version']['message']} at {response['version']['when']}"
            )

        except Exception as err:
            logging.error(f"File Upload Error: {err}")


update_skampi_charts()
