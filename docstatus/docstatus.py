# import schedule
# import time
# import requests
# from github import Github
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# import os
# import pprint

from repositories.repositories import Repository, list_gitlab_repositories


def google_sheet(id):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json',
                                                             scope)  # to get credentials: https://gspread.readthedocs.io/en/latest/oauth2.html
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(
        '1A_mCbsg1sbqcJ_3ly66pqwWfWU6eEoEd5i3cbj3FMSk').get_worksheet(id)  # https://docs.google.com/spreadsheets/d/HERES-THE-ID/edit#gid=0
    return worksheet


def update_sheet(sheet_id, gitlab_repo_list=None, google_sheet_list=None, readthedocs_list=None):
    pass


if __name__ == '__main__':

    gitlabRepos = list_gitlab_repositories()

    repos = []

    for labRepo in gitlabRepos:
        print("Repo Name: " + labRepo.name)
        repo = Repository(labRepo.name, gitlab_repo=labRepo)
        repo.set_folder_exists()
        repo.set_readme_exists()

    sheet = google_sheet(1)

    index = 2
    for repo in repos:
        # Select a range
        cell_list = sheet.range('A' + str(index) + ':F' + str(index))

        if repo.gitlab is not None:
            cell_list[0].value = repo.name
            cell_list[1].value = "TBD"
            cell_list[2].value = repo.docs_folder_exists
            cell_list[3].value = repo.readme_exists
            # cell_list[3].value = repo.gitlab.mirror
            cell_list[4].value = str(repo.gitlab.creator)
            # cell_list[5].value = ""

            # print(str(repo.name) + "\t\t\t\t github: NO \t || gtilab: YES \t || \t admins: " + str(repo.gitlab.creator))

        # Update in batch
        sheet.update_cells(cell_list)

        index = index + 1
