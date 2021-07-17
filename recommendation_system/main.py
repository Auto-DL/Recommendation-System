import os
import pathlib

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
import pickle
from uuid import uuid4

import re

GITHUB_ACCESS_TOKEN=os.getenv('GITHUB_ACCESS_TOKEN')
g=gh.Github(GITHUB_ACCESS_TOKEN)
print(g.get_user())

query='tensorflow language:python created:2021-04-01..2021-04-02'
urls = []
result=g.search_repositories(query)
for repository in result:
    urls.append(repository.html_url)

options=Options()
options.headless = True
options.add_experimental_option('prefs',{'permissions-policy: interest-cohort':()})
driver=webdriver.Chrome(ChromeDriverManager(path='./').install(),options=options)

def get_data_from_repository(url,startTime):
    queue=list()
    links_list = set()
    sequential_list=list()

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
        if '/tree/' in link and not 'venv' in link:
            driver.get(link)
            time.sleep(2.5)
            try:
                table=driver.find_element_by_xpath("//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-block']")
                links=table.find_elements_by_tag_name('a')
                push_to_queue(links)
            except:
                print("No element found")
        elif '.py' in link and not 'venv' in link:
            driver.get(link)
            time.sleep(2.5)
            code_body=driver.find_element_by_xpath("//*[@class='highlight tab-size js-file-line-container']")
            if 'Sequential' in code_body.text:
                print('bam')
                sequential_list.append(get_model_arrays(code_body.text))
            
        
    def bfs():
        while queue:
            currentTime = time.time()
            if (currentTime- startTime) > 300:
                break
            link=queue.pop(0)
            search_through_files(link)

    def get_all_relevant_links(url):
        links_list.add(url)
        driver.get(url)
        try:
            table=driver.find_element_by_xpath("//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-md-block']")
            links=table.find_elements_by_tag_name('a')
            for link in links:
                href=link.get_attribute('href')
                if ('/tree/' in href or '.py' in href) and not 'venv' in href:
                    links_list.add(href)
                    queue.append(href)
        except:
            print('Error')
        bfs()
        print("Ended")

    get_all_relevant_links(url)
    return sequential_list

def getLayerSequence1helper(code):
    '''
    This is the function for models of type Sequential([...])
    :param code: the code to check layer sequence
    :return: array in correct sequence of layers
    :rtype: array model.add(.*)
    '''
    # re.findall('Sequential\((.*)',code,re.DOTALL)
    # re.findall('(Sequential\()(.+)((?:\n.+)+)(\]\))',code)
    # re.findall('(?s)_\(Sequential(.*?)\)',code) \[([^]]+)\]
    rawLayerSequence = re.findall('Sequential\(\[([^]]+)\]\)',code,re.DOTALL)
    layerSequence = list()
    temp=list()
    for i in rawLayerSequence:
        temp = re.findall('.?(.*)\)',i)
        layerSequence.append(temp)
    return layerSequence

def getCleanedLayers(layerlist):
    isValid = True
    for model in layerlist:
        temp=list()
        for layer in model:
            word=layer.split('(')[0]
            word=word.split('.')[-1]
            word=''.join([char for char in word if char.isalnum()])
            temp.append(word)
        layers = ['Conv2D', 'Dense', 'LSTM', 'SimpleRNN', 'Dropout', 'Flatten', 'ZeroPadding2D', 'AveragePooling2D', 'MaxPooling2D']
        for layer in temp:
            if layer not in layers:
                isValid = False
        if len(model) < 4:
            isValid = False
        if isValid:
            model_to_pickle(temp)

def getLayerSequence1(code):
    layerlist=getLayerSequence1helper(code)
    getCleanedLayers(layerlist)

def getLayerSequence2(code):
    '''
    This is the function for models of type model.add(layerName)
    :param code: the code to check layer sequence
    :return: None
    :rtype: None 
    '''
    isValid = True
    model_names = re.findall('(.*) *=.*Sequential\(\)',code)
    for model in model_names:
        modelLayers = []
        model.strip()
        model = model.replace(' ', '')
        rawLayerSequences = re.findall(f"{model}\.add\((.*)\(",code)
        for rawLayerSequence in rawLayerSequences:
            k = rawLayerSequence.split('(')[0]
            k=k.split('.')[-1]
            modelLayers.append(k)
        layers = ['Conv2D', 'Dense', 'LSTM', 'SimpleRNN', 'Dropout', 'Flatten', 'ZeroPadding2D', 'AveragePooling2D', 'MaxPooling2D']
        for layer in modelLayers:
            if layer not in layers:
                isValid = False
        if len(model) < 4:
            isValid = False
        if isValid:
            model_to_pickle(modelLayers)

def get_model_arrays(code):
    getLayerSequence1(code)
    getLayerSequence2(code)

def model_to_pickle(model):
    fname=str(uuid4().hex[:32])+'.pkl'
    curr_dir=pathlib.Path(os.getcwd()).parent
    fpath=os.path.join(curr_dir,'data',fname)
    with open(fpath,'wb') as f:
        pickle.dump(model,f)
        f.close()

url2 = 'https://github.com/bamblebam/image-classification-rps'

def main():
    start = time.time()
    for url in urls:
        startTimeForUrl = time.time()
        get_data_from_repository(url, startTimeForUrl)
    end = time.time()
    print("Total time taken:", {end-start})

main()