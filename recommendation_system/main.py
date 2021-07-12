import os
import github as gh
import bs4 as bs
import requests
from lxml import etree

import selenium
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import time
from tqdm import tqdm

# Getting user
GITHUB_ACCESS_TOKEN=os.getenv('GITHUB_ACCESS_TOKEN')
g = gh.Github(GITHUB_ACCESS_TOKEN)
print(g.get_user())

# Getting all urls in past month made with tensorflow
query='tensorflow language:python created:2021-04-01..2021-04-02'
urls = []
result=g.search_repositories(query)
print(result.totalCount)
print(dir(result))
for repository in result:
    urls.append(repository.html_url)

# Initializing variables
options=Options()
options.headless=True
driver = webdriver.Chrome(ChromeDriverManager(path='./').install(), options=options)

queue=list()
full_list=list()
links_list = set()
sequential_list = list()

# Defining Functions
def push_to_queue(links):
    for link in links:
        href=link.get_attribute('href')
        if href in links_list:
            continue
        if '/tree/' in href or '.py' in href:
            links_list.add(href)
            queue.append(href)

def search_through_files(link):
    print(link)
    if '/tree/' in link:
        driver.get(link)
        time.sleep(2.5)
        table=driver.find_element_by_xpath("//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-block']")
        links=table.find_elements_by_tag_name('a')
        push_to_queue(links)
    elif '.py' in link:
        driver.get(link)
        time.sleep(2.5)
        full_list.append(link)
        code_body=driver.find_element_by_xpath("//*[@class='Box-body p-0 blob-wrapper data type-python  gist-border-0']")
        if 'Sequential' in code_body.text:
            sequential_list.append(link)

def bfs():
    while queue:
        link=queue.pop(0)
        search_through_files(link)



def get_all_relevant_links(url):
    links_list.add(url)
    driver.get(url)
    table=driver.find_element_by_xpath("//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-md-block']")
    links=table.find_elements_by_tag_name('a')
    for link in links:
        href=link.get_attribute('href')
        if '/tree/' in href or '.py' in href:
            links_list.add(href)
            queue.append(href)
    bfs()
    print("Ended")

res=get_all_relevant_links('https://github.com/Z-yq/TensorflowTTS')
def getSequentialModel(full_list):
    count=0
    for url in full_list:
        driver.get(url)
        time.sleep(2.5)
        print(url)
        code_body=driver.find_element_by_xpath("//*[@class='Box-body p-0 blob-wrapper data type-python  gist-border-0']")
        if 'Sequential' in code_body.text:
            count+=1
    return count

