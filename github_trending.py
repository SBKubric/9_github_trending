import argparse
import concurrent.futures
import requests
from datetime import date
from dateutil.relativedelta import relativedelta

TOP_SIZE = 20


def parse_args():
    parser = argparse.ArgumentParser(description='This script fetches the most starred repos from GitHub.')
    parser.add_argument('-at', '--access_token', help='Use your access_token for overriding the limits of unauthorized '
                                                      'access to GitHub API. For more info go to '
                                                      'https://developer.github.com/v3/rate_limit/')
    parser.add_argument('-ts', '--top_size', default=20, help='Set this value to show less/more repos. '
                                                              'Default is 20')
    parser.add_argument('-tp', '--time_period', default=7, help='It is amount of days during '
                                                                'which the repos were created'
                                                                'Default is 7')
    return parser.parse_args()


def get_repo_open_issues_urls(full_repo_name, access_token=None):
    params = {}
    if access_token:
        params['access_token'] = access_token
        request = requests.get('https://api.github.com/repos/{}/issues'.format(full_repo_name), params=params)
    else:
        request = requests.get('https://api.github.com/repos/{}/issues'.format(full_repo_name))
    return list(issue['html_url'] for issue in request.json())


def get_trending_repos(top_size, days_before_today, access_token=None):
    since_date = date.today() + relativedelta(days=-days_before_today)
    params = {
        'q': 'created:>%s' % since_date,
        'sort': 'stars',
        'order': 'desc',
    }
    if access_token:
        params['access_token'] = access_token
    request = requests.get('https://api.github.com/search/repositories', params=params)
    trending_repos = list(
        {
            'full_name': repo['full_name'],
            'stargazers_count': repo['stargazers_count'],
        } for repo in request.json()['items'][:top_size]
    )
    return trending_repos


def get_issues_count_and_issue_links(repos, access_token=None):
    pool = concurrent.futures.ThreadPoolExecutor(len(repos))
    names = list(repo['full_name'] for repo in repos)
    access_tokens = list(access_token for repo in repos)
    open_issues_urls = list(pool.map(get_repo_open_issues_urls, names, access_tokens))
    for repo, repo_open_issue_urls in zip(repos, open_issues_urls):
        repo['open_issues_counter'] = len(repo_open_issue_urls)
        repo['open_issues_urls'] = repo_open_issue_urls
    return repos


def print_trending_repos(repos):
    for num, repo in enumerate(repos, start=1):
        author_name, repo_name = repo['full_name'].split('/')
        print('{}., Author: {} Repo_name: {}  Stars: {} Open_issues: {}'.format(
            num,
            author_name,
            repo_name,
            repo['stargazers_count'],
            repo['open_issues_counter'],
        ))
        if repo['open_issues_counter']:
            print('Open issues urls:')
        for url in repo['open_issues_urls']:
            print(' {}'.format(url))
        print('\n')


if __name__ == '__main__':
    args = parse_args()
    trending_repos_list = get_trending_repos(args.top_size, args.time_period, access_token=args.access_token)
    get_issues_count_and_issue_links(trending_repos_list, args.access_token)
    print_trending_repos(trending_repos_list)
