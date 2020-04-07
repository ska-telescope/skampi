from models.SKAGitLab import SKAGitLab
from models.ReadtheDocsProject import create_readthedocs_project, ReadtheDocs
from models.User import User
import fire
from flask import url_for


def import_docs(name_with_namespace, repository, prog_lang= "py", lang= "en", test_sub= False):

    return create_readthedocs_project(name_with_namespace,repository,prog_lang=prog_lang,lang=lang,test_sub=test_sub)


def create_repo(project_name,maintainer_ids, template= None):

    gitlab = SKAGitLab()

    
    result = gitlab.create_gitlab_repo(project_name,maintainer_ids,template=template)

    # next_urls = {'import_readthedocs': url_for('import_docs', _external=True)}

    # result['_api_links'] = next_urls

    return result


if __name__ == "__main__":
    fire.Fire()
