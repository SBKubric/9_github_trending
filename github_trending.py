import concurrent.futures
import requests
from datetime import date
from dateutil.relativedelta import relativedelta

TOP_SIZE = 20


def get_repo_open_issues_urls(full_repo_name):
    request = requests.get('https://api.github.com/repos/%s/issues' % full_repo_name)
    issues_urls = []
    for issue in request.json():
        issues_urls.append(issue['html_url'])
    return issues_urls


def get_trending_repos(top_size):
    week_ago = date.today() + relativedelta(weeks=-1)
    params = {'q': 'created:>%s' % week_ago,
              'sort': 'stars',
              'order': 'desc',
              }
    request = requests.get('https://api.github.com/search/repositories', params=params)
    trending_repos = []
    for repo in request.json()['items'][:top_size]:
        trending_repos.append({
            'full_name': repo['full_name'],
            'stargazers_count': repo['stargazers_count'],
        })
    return trending_repos


def get_issues_count_and_issue_links(repos):
    pool = concurrent.futures.ThreadPoolExecutor(len(repos))
    names = []
    for repo in repos:
        names.append(repo['full_name'])
    open_issues_urls = list(pool.map(get_repo_open_issues_urls, names))
    for repo, repo_open_issue_urls in zip(repos, open_issues_urls):
        repo['open_issues_counter'] = len(repo_open_issue_urls)
        repo['open_issues_urls'] = repo_open_issue_urls
    return repos


def print_trending_repos(repos):
    for num, repo in enumerate(repos, start=1):
        author_name, repo_name = repo['full_name'].split('/')
        print("%s. Author: %s Repo_name: %s  Stars: %s Open_issues: %s" % (
            num,
            author_name,
            repo_name,
            repo['stargazers_count'],
            repo['open_issues_counter'],
        ))
        if repo['open_issues_counter']:
            print('Open issues urls:')
        for url in repo['open_issues_urls']:
            print(' %s' % url)
        print('\n')


if __name__ == '__main__':
    trending_repos_list = get_trending_repos(TOP_SIZE)
    get_issues_count_and_issue_links(trending_repos_list)
    print_trending_repos(trending_repos_list)