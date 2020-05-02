from bs4 import BeautifulSoup
import datetime
import pandas as pd
import requests
import string
import re as regexz
import random
import os.path
from tqdm import tqdm
import json
import os
from getImagesFunctions import *
from htmldate import find_date
import time
import uuid
from nltk.tokenize import word_tokenize

base_path = os.getcwd()

#class Organize(folder_base, iteration):
#    def __init__(self, folder_base, iteration):
#        self.folder_base = folder_base
#        self.iteration = iteration

def gatherImagessUrls(name, n_folders) :
    base_path = os.getcwd()
    all_url = []
    for n in range(1,n_folders+1):
        folder_path = name + str(n)
        folder_path = os.path.join(base_path, folder_path)
        print(folder_path)
        if os.path.isdir(folder_path):
            list_json = [j for j in os.listdir(folder_path) if ".json" in j]
        if os.path.isdir(os.path.join(folder_path,"img")):
            list_imgs = [i for i in os.listdir(os.path.join(folder_path,"img"))]

        for js in list_json:
            json_data = loadJson(os.path.join(folder_path,js))
            try:
                temp_url = getImageURL(json_data)
                all_url = all_url + temp_url
            except KeyError:
                print('corrupted json file, probably an 400 Error!')
                continue
    return all_url

def gatherProcessedImagessUrls(folder) :
    if not os.path.exists(folder):
        print('no images found in {}: path does not yet exist'.format(folder))
        return
    else:
        list_txt = [i for i in os.listdir(folder) if ".txt" in i]
        list_txt = [os.path.join(folder,i) for i in list_txt]

        success = 0
        errors = 0

        if len(list_txt) == 0:
            print('no images found in {}: no images in folder'.format(folder))
        else:
            list_url = []
            for t in list_txt:
                with open(t,'r') as f:
                    c = f.readlines()
                if c[0][:5] == "ERROR":
                    errors += 1
                    list_url.append(c[0])
                else:
                    success += 1
                    list_url.append(c[0])
            print("{} successful and {} failed scrapes".format(success, errors))
            return list_url

def gatherPagesUrls(name, n_folders) :
    print("Initating gatherPagesUrls")
    base_path = os.getcwd()
    all_url = dict()
    for n in range(1,n_folders+1):
        folder_path = name + str(n)
        folder_path = os.path.join(base_path, folder_path)
        print(folder_path)

        if os.path.isdir(folder_path):
            list_json = [j for j in os.listdir(folder_path) if ".json" in j]
        if os.path.isdir(os.path.join(folder_path,"img")):
            list_imgs = [i for i in os.listdir(os.path.join(folder_path,"img"))]

        errors = 0
        for js in list_json:
            json_data = loadJson(os.path.join(folder_path,js))
            try:
                temp_url = getPages(json_data)
                all_url.update({n:temp_url})
            except KeyError:
                errors += 1
                continue
    print('finished page url gathering: {} .json file errors'.format(errors))
    return all_url

def gatherPagesUrlsFolder(folder_path) :
    if os.path.isdir(folder_path):
        list_json = [j for j in os.listdir(folder_path) if ".json" in j]
    if os.path.isdir(os.path.join(folder_path,"img")):
        list_imgs = [i for i in os.listdir(os.path.join(folder_path,"img"))]

    errors = 0
    all_url = dict()
    for c,js in enumerate(list_json):
        json_data = loadJson(os.path.join(folder_path,js))
        try:
            temp_url = getPages(json_data)
            all_url.update({c:temp_url})
        except KeyError:
            errors += 1
            continue
    print('finished page url gathering: {} .json file errors'.format(errors))
    all_url = [list(v) for k,v in all_url.items()]
    all_url = [item for sublist in all_url for item in sublist]
    return all_url

def gatherDates(list_urls):
    url_d = dict()
    for i in list_urls:
        #print(i)
        try:
            d = find_date(i)
            url_d.update({i:d})
        except Exception as e:
            print(e)
            continue
    return url_d

def gatherSingleDate(url):
    try:
        d = find_date(url)
        return d
    except Exception as e:
        print(e)
        return e

    return {url:d}

def gatherFullText(url):
    article = Article(url)
    article.download()
    article.parse()
    txt = article.text
    txt = txt.replace('\n\n', '\n')
    return txt

def SearchURLMatch(url):
    poss_years = [str(i) for i in range(1990,2021)]
    poss_months_char = {"jan":'01', "feb":'02', "mar":'03', "apr":'04', "may":'05', "jun":'06', "jul":'07', "aug":'08',"sep":'09', "oct":'10', "nov":'11', "dec":'12'}
    poss_months_int = "01 02 03 04 05 06 07 08 09 10 11 12"
    poss_days_int = [str(i) for i in range(1,32)]
    poss_days_int = ["0"+i for i in poss_days_int if len(i) == 1] + [i for i in poss_days_int if len(i) > 1]

    u = url.split('/')
    doubts = "no"
    year = "na"
    month = 'na'
    day = 'na'

    if any(y in u for y in poss_years):
        index_year = u.index([y for y in u if y in poss_years][0])

        # IF MONTH IS A STRING: "JAN" OR "OCT"
        if u[index_year+1] in poss_months_char.keys():
            year = u[index_year]
            month = poss_months_char[u[index_year+1]]
            if u[index_year+2] in poss_days_int:
                day = u[index_year+2]
                status = "found something"
            if u[index_year+2] not in poss_days_int:
                day = "na"


        # IF PATTERN IS YEAR-MONTH-DAY
        try:
            if u[index_year+1] in poss_months_int and u[index_year+2] in poss_days_int:
                year = u[index_year]
                month = u[index_year+1]
                day = u[index_year+2]
                status = "found something"
                if u[index_year+2] in poss_months_int and u[index_year+1] in poss_days_int and u[index_year+1] != u[index_year+2]:
                    doubts = "yes"
        except IndexError:
            doubts = "yes"


        # IF PATTERN IS YEAR-DAY-MONTH
        try:
            if u[index_year+1] in poss_days_int and u[index_year+2] in poss_months_int:
                year = u[index_year]
                month = u[index_year+2]
                day = u[index_year+1]
                status = "found something"
                if u[index_year+1] in poss_months_int and u[index_year+2] in poss_days_int and u[index_year+2] != u[index_year+1]:
                        doubts = "yes"
        except IndexError:
                doubts = "yes"

        # IF PATTERN IS MONTH-DAY-YEAR
        try:
            if u[index_year-1] in poss_days_int and u[index_year-2] in poss_months_int:
                year = u[index_year]
                month = u[index_year-2]
                day = u[index_year-1]
                status = "found something"
                if u[index_year-1] in poss_months_int and u[index_year-2] in poss_days_int and u[index_year-1] != u[index_year-2]:
                    doubts = "yes"
        except IndexError:
                doubts = "yes"

        # IF PATTERN IS DAY-MONTH-YEAR
        try:
            if u[index_year-2] in poss_days_int and u[index_year-1] in poss_months_int:
                year = u[index_year]
                month = u[index_year-1]
                day = u[index_year-2]
                status = "found something"
                if u[index_year-2] in poss_months_int and u[index_year-1] in poss_days_int and u[index_year-2] != u[index_year-1]:
                    doubts = "yes"
        except IndexError:
                doubts = "yes"

        status = "found something"

        if doubts == "no" and status == "found something" and year != "na" and month != "na" and day != "na":
            return [year,month,day]

        elif doubts == "yes":
            return ["na"]
    else:
        status = "found nothing"

def ArticleText(url_element, preprocess=True):
    fn = url_element[0]
    url = url_element[1]

    a = Article(url)

    with open(fn, 'rb') as fh:
        a.html = fh.read()
    a.download_state = 2
    a.parse()
    text = a.text

    if preprocess == True:
        text = text.lower()
        text = text.replace('\n','').split('.')
        #text = [t for t in text if t]
        text = [word_tokenize(s) for s in text]
        text = [s for s in text if len(s) > 1]

    return {fn.split('/')[-1].split('\\')[1] + "_" + url:text}

def gatherHTML(url):
    title = str(uuid.uuid4()) + '.html'
    resp = requests.get(url)
    #d = SearchURLMatch(url)
    #if d == "found nothing":
    #    d = find_date(url)
    with open(title, "wb") as fh:
        fh.write(resp.content)

    with open('results.txt', "a") as fh:
        fh.write("{}|{}{}".format(title[:-5], url, '\n'))

    time.sleep(0.1)

def gatherAllHTML(list_urls):
    threads = min(MAX_THREADS, len(list_urls))

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(gatherHTML, list_urls)

def gatherHTMLFunctions(list_urls):
    t0 = time.time()
    gatherAllHTML(list_urls)
    t1 = time.time()
    print(f"{round(t1-t0)} seconds to download {len(list_urls)} html.")