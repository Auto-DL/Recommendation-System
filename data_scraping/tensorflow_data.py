import os
import sys

import github as gh

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import time
from tqdm import tqdm
import pickle
from uuid import uuid4

import re


def get_data_from_repository(url, driver, startTime, path):
    """
    Function to get data from a repository
    :param url: url of the repository
    :param driver: webdriver to get the data
    :param startTime: time taken when the function is called used to give the scraping time an upper bound
    :param path: path to save the data
    :return: List of models in terms of layer data (Not required will be deprecated)
    :rtype: list
    """
    queue = list()
    links_list = set()
    sequential_list = list()

    def push_to_queue(links):
        """
        Function to push the file links at a particular level of the repository to the queue
        :param links: list of file links at the parent level
        :return: None
        :rtype: None
        """
        for link in links:
            href = link.get_attribute("href")
            if href in links_list:
                continue
            if "/tree/" in href or href.endswith(".py"):
                links_list.add(href)
                queue.append(href)

    def search_through_files(link):
        """
        Function to search through a file or folder
        :param link: link to the file or folder
        :return: None
        :rtype: None
        """
        print(link)
        if "/tree/" in link and not "venv" in link:
            driver.get(link)
            time.sleep(2.5)
            try:
                table = driver.find_element_by_xpath(
                    "//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-block']"  # xpath for file table
                )
                links = table.find_elements_by_tag_name("a")
                push_to_queue(links)
            except:
                print("No element found")
        elif link.endswith(".py") and not "venv" in link:
            driver.get(link)
            time.sleep(2.5)
            try:
                code_body = driver.find_element_by_xpath(
                    "//*[@class='highlight tab-size js-file-line-container']"  # xpath for code container
                )
                if "Sequential" in code_body.text:
                    print("sequential")
                    sequential_list.append(get_model_arrays(code_body.text, path))
            except:
                print("ERROR")

    def bfs():
        """
        Function to perform reccurent BFS to traverse the repository
        :return: None
        :rtype: None
        """
        while queue:
            currentTime = time.time()
            if (currentTime - startTime) > 600:
                break
            link = queue.pop(0)
            search_through_files(link)

    def get_all_relevant_links(url):
        """
        Function to get the root file and folder urls and initialize the entire thing
        :param url: url of the repository
        :return: None
        :rtype: None
        """
        links_list.add(url)
        driver.get(url)
        try:
            table = driver.find_element_by_xpath(
                "//*[@class='Details-content--hidden-not-important js-navigation-container js-active-navigation-container d-md-block']"
            )
            links = table.find_elements_by_tag_name("a")
            for link in links:
                href = link.get_attribute("href")
                if ("/tree/" in href or href.endswith(".py")) and not "venv" in href:
                    links_list.add(href)
                    queue.append(href)
        except:
            print("Error")
        bfs()
        print("Ended")

    get_all_relevant_links(url)
    return sequential_list


def getLayerSequence1helper(code):
    """
    Helper function to get models of type Sequential([...])
    :param code: the code from the .py file
    :return: list in correct sequence of layers
    :rtype: list model.add(.*)
    """
    rawLayerSequence = re.findall("Sequential\(\[([^]]+)\]\)", code, re.DOTALL)
    layerSequence = list()
    temp = list()
    for i in rawLayerSequence:
        temp = re.findall(".?(.*)\)", i)
        layerSequence.append(temp)
    return layerSequence


def getCleanedLayers(layerlist, path):
    """
    Function to clean the layers recieved from getLayerSequence1helper
    :param layerlist: the list of layers from getLayerSequence1helper
    :param path: path to save the data
    :return: None
    :rtype: None
    """
    layers = [
        "Conv2D",
        "Dense",
        "LSTM",
        "SimpleRNN",
        "Dropout",
        "Flatten",
        "ZeroPadding2D",
        "AveragePooling2D",
        "MaxPooling2D",
    ]
    for model in layerlist:
        isValid = True
        temp = list()
        for layer in model:
            word = layer.split("(")[0]
            word = word.split(".")[-1]
            word = "".join([char for char in word if char.isalnum()])
            if word not in layers:
                isValid = False
                break
            temp.append(word)
        if len(model) < 4:
            isValid = False
        if isValid:
            model_to_pickle(temp, path)


def getLayerSequence1(code, path):
    """
    Function to get the models of type Sequential([...])
    :param code: the code from the .py file
    :param path: path to save the data
    :return: None
    :rtype: None
    """
    layerlist = getLayerSequence1helper(code)
    getCleanedLayers(layerlist, path)


def getLayerSequence2(code, path):
    """
    Function to get models of type model.add(layerName)
    :param code: the code from the .py file
    :param path: path to save the data
    :return: None
    :rtype: None
    """
    layers = [
        "Conv2D",
        "Dense",
        "LSTM",
        "SimpleRNN",
        "Dropout",
        "Flatten",
        "ZeroPadding2D",
        "AveragePooling2D",
        "MaxPooling2D",
    ]
    model_names = re.findall("(.*) *=.*Sequential\(\)", code)
    for model in model_names:
        isValid = True
        modelLayers = []
        model.strip()
        model = model.replace(" ", "")
        rawLayerSequences = re.findall(f"{model}\.add\((.*)\(", code)
        for rawLayerSequence in rawLayerSequences:
            k = rawLayerSequence.split("(")[0]
            k = k.split(".")[-1]
            if k not in layers:
                isValid = False
                break
            modelLayers.append(k)
        if len(modelLayers) < 4:
            isValid = False
        if isValid:
            model_to_pickle(modelLayers, path)


def get_model_arrays(code, path):
    """
    Wrapper function to call the other functions to get the model arrays
    :param code: the code from the .py file
    :param path: path to save the data
    :return: None
    :rtype: None
    """
    getLayerSequence1(code, path)
    getLayerSequence2(code, path)


def model_to_pickle(model, path):
    """
    Function to convert the model to a pickle object
    :param model: the model to be converted
    :param path: path to save the data
    :return: None
    :rtype: None
    """
    fname = str(uuid4().hex[:32]) + ".pkl"
    fpath = os.path.join(path, fname)
    with open(fpath, "wb") as f:
        pickle.dump(model, f)
        f.close()


def main(startDate, endDate, dataFolderPath):
    """
    Function to run the code from the command line
    :param startDate: start date of the data
    :param endDate: end date of the data
    :param dataFolderPath: path to the data folder
    :return: None
    :rtype: None
    """
    startTime = time.time()
    GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
    g = gh.Github(GITHUB_ACCESS_TOKEN)
    query = f"tensorflow language:python created:{startDate}..{endDate}"
    urls = []
    result = g.search_repositories(query)
    for repository in result:
        urls.append(repository.html_url)
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(
        ChromeDriverManager(path="./").install(), options=options
    )  # downloads the latest version of the chrome drivers
    for url in tqdm(urls):
        startTimeForUrl = time.time()
        get_data_from_repository(url, driver, startTimeForUrl, dataFolderPath)
    endTime = time.time()
    print("Total time taken:", {endTime - startTime})


# startDate = sys.argv[1]
# endDate = sys.argv[2]
# dataFolderPath = sys.argv[3]
# main(startDate, endDate, dataFolderPath)
