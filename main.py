

from repositories.repositories import Repository, GitLabRepo, list_gitlab_repositories, create_gitlab_repo

from readthedocs.readthedocs import list_of_readthedocs_projects, ReadthedocsProject, ReadtheDocs

if __name__ == '__main__':

    # gitlabRepos = list_gitlab_repositories()

    #TEST REPO
    gitlabRepos = [GitLabRepo(name="My Mac", path='https://github.com/adriaan-sac/mymac.git')]

    for labRepo in gitlabRepos:
        rtd_project = ReadthedocsProject(name=labRepo.name, repo_url=labRepo.path, language="en", programming_language="py")
        rtd_project.create_project()
        slug = rtd_project.slug
        print(ReadtheDocs().make_subproject("devdeveloperskatelescopeorg", slug))
