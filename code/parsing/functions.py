from bs4 import BeautifulSoup
import datetime, csv
import pandas as pd
import requests
import string
import re as regexz
import random
from tqdm import tqdm
import json
import os
from htmldate import find_date
import time
import uuid
import concurrent.futures
from nltk.tokenize import word_tokenize
import spacy
from boilerpipe.extract import Extractor
import codecs
import math
import shutil
from PIL import Image
import io
from urllib.parse import urlparse
import langid
from langid.langid import LanguageIdentifier, model

identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

nlp = spacy.load('en_core_web_sm')

class dateparser():
    def __init__(self,url,list_url,filename):
        self.url = url
        self.list_url = list_url
        self.filename = filename

    def gatherDateMatch(url):
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
            if u[index_year+1] and u[index_year+1] in poss_months_char.keys():
                year = u[index_year]
                month = poss_months_char[u[index_year+1]]
                if u[index_year+2] and u[index_year+2] in poss_days_int:
                    day = u[index_year+2]
                    status = "found something"
                if u[index_year+2] and u[index_year+2] not in poss_days_int:
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
                #return [year,month,day]
                return "-".join([year,month,day])

            elif doubts == "yes":
                #return ["na"]
                return "na"
        else:
            #status = "found nothing"
            return "na"

    def gatherSingleDate(url):
        date = dateparser.gatherDateMatch(url)
        if date == "na":
            try:
                date = find_date(url)
                return date
            except Exception as e:
                print(e)
                date = "ERROR:{}".format(e)
                return date
        else:
            return date

    def gatherSingleDateMultiProc(url,filename):
        date = dateparser.gatherDateMatch(url)
        if date == "na":
            try:
                date = find_date(url)
                if date is None:
                    date = "na"
                with open(filename, 'a') as f:
                    f.write(url+'|'+date+"\n")
            except Exception as e:
                print(e)
                date = "ERROR:{}".format(e)
                if date is None:
                    date = "na"
                with open(filename, 'a') as f:
                    f.write(url+'|'+date+"\n")
        elif date is None:
            with open(filename, 'a') as f:
                f.write(url+'|'+"na"+"\n")
        else:
            with open(filename, 'a') as f:
                f.write(url+'|'+date+"\n")

    def gatherListDates(list_urls):
        url_d = dict()
        for u in list_urls:
            date = Date.gatherSingleDate(u)
            url_d.update({u:date})
        return url_d

    def PoolScrapeDate(list_url, destination_path,filename):
        threads = min(30, len(list_url))

        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(dateparser.gatherSingleDateMultiProc, url, filename): url for url in list_url}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    pass
                    #print('%r generated an exception: %s' % (url, exc))
                else:
                    pass

class pagescraper():
    def __init__(self,destination_path, list_url,filename):
        self.destination_path = destination_path
        self.list_url = list_url
        self.filename = filename

    def Scraper(url, destination_path):
        #print('Called')
        title = os.path.join(destination_path, str(uuid.uuid4()) + '.html')
        resp = requests.get(url, verify=False, timeout=30)

        with open(title, "wb") as fh:
            fh.write(resp.content)

        with open(os.path.join(destination_path,"results.txt"), "a") as fh:
            fh.write("{}|{}{}".format(title[:-5], url, '\n'))

        time.sleep(0.1)

    def PoolScrape(list_url, destination_path):
        threads = min(30, len(list_url))

        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(pagescraper.Scraper, url, destination_path): url for url in list_url}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                except Exception as exc:
                    pass
                    #print('%r generated an exception: %s' % (url, exc))
                else:
                    pass

class textparser():
    def __init__(self,html_folder):
        self.html_folder = html_folder

    def Import(html_folder):

        if os.path.exists(os.path.join(html_folder, "results.txt")):
            with open(os.path.join(html_folder, "results.txt")) as f:
                urls = f.readlines()
                urls_new = []
                for u in urls:
                    try:
                        id = str(u).split('|')[0]
                        url = str(u).split('|')[1].replace('\n','')
                        id = id + '.html'
                        id = os.path.join(html_folder,id)
                        urls_new.append((id, url))
                    except IndexError:
                        continue
                return urls_new
        else:
            print("results.txt not found in {}".format(html_folder))


    def ParserBoilerArticle(html_object):
        extractor = Extractor(extractor='ArticleSentencesExtractor', html=html_object)
        sents = extractor.getText()
        try:
            sents = list(nlp(sents).sents)
            return sents
        except Exception as e:
            return

    def ParserBoilerDefault(html_object):
        extractor = Extractor(extractor='DefaultExtractor', html=html_object)
        sents = extractor.getText()
        try:
            sents = list(nlp(sents).sents)
            return sents
        except Exception as e:
            return

    def ParserBoilerEverything(html_object):
        extractor = Extractor(extractor='DefaultExtractor', html=html_object)
        sents = extractor.getText()
        try:
            sents = list(nlp(sents).sents)
            return sents
        except Exception as e:
            return

    def ParserRaw(html_object):
        soup = BeautifulSoup(html_object, "html.parser")
        [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
        text = soup.getText()
        #text = [t for t in text if t]
        return text

    def Parse(html_folder):
        urls = textparser.Import(html_folder)
        errors = 0
        print("INFO: parsing tekst from {} files".format(len(urls)))
        destination_path = os.path.join(html_folder[:-4], "txt")

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        text_dict = dict()
        for u in tqdm(urls):
            fn = os.path.join(html_folder, u[0])
            url = u[1]
            id = "_".join([fn,url])
            try:
                with codecs.open(fn,'r',encoding='utf-8',errors='ignore') as f:
                    html_object = f.read()

                sents = textparser.ParserBoilerArticle(html_object)

                if len(sents) < 2 or sents is None:
                    sents = textparser.ParserBoilerDefault(html_object)
                if len(sents) < 2 or sents is None:
                    sents = textparser.ParserBoilerEverything(html_object)
                if len(sents) < 2 or sents is None:
                    sents = textparser.ParserRaw(html_object)

                if type(sents) == list:
                    text_dict.update({id:" ".join([str(sent) for sent in sents])})
                if type(sents) == str:
                    text_dict.update({id:sents})

            except Exception as e:
                continue

        with open(os.path.join(destination_path, "parsed_text.json"), "w") as js:
            json.dump(text_dict,js)

class imagescraper():
    def __init__(url,filename):
        self.url = url
        self.filename = filename

    def Scrape(url):
        fn = uuid.uuid1()
        #fn = re.sub(r'\W+', '', url)

        if "png" in url:
            fn = str(fn) + ".png"
        elif "jpg" in url:
            fn = str(fn) + ".jpg"
        elif "Jpeg" in url:
            fn = str(fn) + ".jpg"
        elif "jpeg" in url:
            fn = str(fn) + ".jpg"
        elif "JPG" in url:
            fn = str(fn) + ".jpg"
        else:
            return 0
        print(fn)

        #try:
            #image_content = requests.get(url, timeout=20).content

        #except Exception as e:
            #with open(fn[:-4] + ".txt",'w') as f:
            #    f.write("ERROR: " + str(e) + "|" + url)
            #return

        try:
            image_content = requests.get(url, timeout=20,stream=True).content
            image_file = io.BytesIO(image_content)
            image = Image.open(image_file).convert('RGB')
            with open(fn, 'wb') as f:
                image.save(f)
            with open(fn[:-4] + ".txt",'w',encoding='utf-8') as f:
                f.write("SUCCESS: " + url)
            del image

        except Exception as e:
            with open(fn[:-4] + ".txt",'w') as f:
                f.write("ERROR: " + str(e) + "|" + url)
            return

    def findtags(filename):
        extensions = ".jpg .JPG .JPEG .jpeg .Jpeg .png".split(' ')

        #try:
            #content = requests.get(url,t).content
        #except Exception as e:
            #print(e)
            #return
        #soup = BeautifulSoup(content,'lxml')

        with codecs.open(filename,'r',encoding='utf-8',errors='ignore') as f:
            html_object = f.read()
        soup = BeautifulSoup(html_object, "html.parser")
        image_tags = []
        for tag in ['img','meta','a']:
            tt = soup.findAll(tag)
            image_tags = image_tags + tt
        list_url = []
        for c,tag in enumerate(image_tags):
            attributes = dict(tag.attrs)

            for k,v in attributes.items():
                # Extract Image
                if any(substring in v for substring in extensions):
                    list_url.append(v)

        if len(list_url) > 0:
            return list_url
        else:
            return


class Parse():
    """docstring for Parse.
    - Texts() parses texts from .html file using boilerpipe
    - Languages() parses languages from webpage content using the langid library
    - Dates() parses dates from urls and webpage content by regex patters and the htmldate library
    """

    def __init__(self,photo, base_path):
        super(Parse, self).__init__()
        self.photo = photo
        self.base_path = base_path

    def Texts(base_path,photo):
        photo_folder = os.path.join(base_path, photo)
        num_iterations = len([fol for fol in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder,fol)) and "source" not in fol])
        start_iter = 1
        range_iter = [str(i) for i in list(range(1,num_iterations))]
        folder_base = os.path.join(base_path,photo,photo)

        for iteration in range_iter:
            print("INFO: scraping text for {}, iteration {}".format(photo, iteration))
            for iteration in range_iter:
                textparser.Parse(os.path.join(folder_base+ "_" + str(iteration), "html"))

    def Languages(base_path,photo):
        photo_folder = os.path.join(base_path, photo)
        num_iterations = len([fol for fol in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder,fol)) and "source" not in fol])
        start_iter = 1
        range_iter = [str(i) for i in list(range(1,num_iterations+1))]
        folder_base = os.path.join(base_path,photo,photo)

        print('INFO: Scraping Languages for photo {}'.format(photo))

        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

        language_dict = {}
        for iteration in range_iter:

            if os.path.isdir(os.path.join(folder_base + "_" + str(iteration) + "/txt")) == False:
                print('INFO: No texts in this iteration, stopping..')
                continue

            language_dict.update({str(iteration):{}})

            list_json= [js for js in os.listdir(os.path.join(base_path,photo,photo + "_" + str(iteration),"txt")) if ".json" in js]

            for js in list_json:
                with open(os.path.join(base_path,photo,photo + "_" + str(iteration),"txt", js)) as f:
                    json_content = json.load(f)

                for id_, text in json_content.items():

                    language_score = identifier.classify(str(text))
                    print(language_score)
                    language_dict[str(iteration)].update({id_:[language_score[0],language_score[1]]})

        # Write Detected Languages to language.json
        print("INFO: Writing detected languages to {}".format(os.path.join(photo,'languages.json')))
        with open(os.path.join(base_path,photo,'languages-{}.json'.format(photo)), 'w') as fp:
            json.dump(language_dict, fp)

    def Dates(base_path,photo):

        #########################
        photo_folder = os.path.join(base_path, photo)
        num_iterations = len([fol for fol in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder,fol)) and "source" not in fol])
        start_iter = 1
        range_iter = [str(i) for i in list(range(1,num_iterations+1))]
        folder_base = os.path.join(base_path,photo,photo)
        #########################

        scraped_urls = {}
        print('INFO: Scraping Dates')

        for iteration in range_iter:
            try:
                with open(os.path.join(base_path, photo, photo + "_" + str(iteration), "html", "results.txt"), 'r', encoding='utf-8') as f:
                    lu = f.readlines()
                lu = [l.split('|') for l in lu]
                lu = [l for l in lu if len(l) == 2]
                lu = [l[1].replace('\n','') for l in lu]
                print("---- {} dates found in iteration {}".format(len(lu),iteration))
                scraped_urls.update({str(iteration):lu})
            except Exception as e:
                print("Error: ", e)

        dates_dict = {}

        for it, list_ in scraped_urls.items():
            dates_dict.update({str(it):dict()})
            print('---- Scraping Dates Iteration {}, {} URLs'.format(it,len(list_)))

            for u in tqdm(list_):
                try:
                    date = dateparser.gatherSingleDate(u)
                    dates_dict[str(it)].update({u:date})
                except Exception as e:
                    print(e)

        # Write Detected Dates to language.json
        print("INFO: Writing detected dates to {}".format(os.path.join(photo,'dates.json')))
        with open(os.path.join(base_path,photo,'dates-{}.json'.format(photo)), 'w') as fp:
            json.dump(dates_dict, fp)

    def Entities(base_path,photo):
        #########################
        photo_folder = os.path.join(base_path, photo)
        num_iterations = len([fol for fol in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder,fol)) and "source" not in fol])
        start_iter = 1
        range_iter = [str(i) for i in list(range(1,num_iterations+1))]
        folder_base = os.path.join(base_path,photo,photo)
        #########################

        print("INFO: Named Entitiy Recognition using Spacy")

        selected_languages = "en de fr es it nl pt".split(' ')
        selected_languages = {i:i+"_core_news_sm" for i in selected_languages}
        selected_languages.update({"en":"en_core_web_sm"})

        def PreProc(text):
            text = text[1:-1].replace('\xa0', ' ')
            text = " ".join(text.split('\r\n'))
            return text

        d_ = {}
        for iteration in range_iter:
            fn = os.path.join(folder_base + "_" +str(iteration),"txt", "parsed_text.json")
            if os.path.isdir(os.path.join(folder_base + "_" +str(iteration),"txt")) == False:
                print('INFO: no parsed text found in iteration {}'.format(iteration))
                continue

            with open(fn) as fp:
                pages = json.load(fp)

            df = []
            for id_,sentences in pages.items():

                sentences = [s.replace("\n","").lower() for s in sentences]
                sentences = [re.sub(' +', ' ', s) for s in sentences]

                url = id_.split('html_')[-1]
                id_ = id_.split('/html/')[1].split('.html_')[0]
                language = identifier.classify(str(sentences))[0]
                df.append([url,id_,language,str(sentences)])

            df = pd.DataFrame(df,columns=['url','id','lang','text'])

            # NER
            for lang in [i for i in list(set(df['lang'])) if i in selected_languages.keys()]:
                print('INFO: working on language: {}'.format(lang))
                if lang not in d_.keys():
                    d_.update({lang:dict()})
                nlp = spacy.load(selected_languages[lang])
                tmp = df[df['lang'] == lang]

                for count,text in enumerate(df['text']):
                    identif = str(df['id'][count])
                    d_[lang].update({identif:dict()})
                    d_[lang][identif].update({"text":text})
                    doc = nlp(text)
                    doc = [(ent.text, ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
                    d_[lang][identif].update({"entities":doc})

        with open(os.path.join(base_path, photo,"entities-{}.json".format(photo)), 'w') as fp:
            json.dump(d_, fp)

    def ContextImages(base_path,photo):

        ###############################
        photo_folder = os.path.join(base_path, photo)
        num_iterations = len([fol for fol in os.listdir(photo_folder) if os.path.isdir(os.path.join(photo_folder,fol)) and "source" not in fol and "context_images" not in fol])
        start_iter = 1
        range_iter = [str(i) for i in list(range(1,num_iterations+1))]
        folder_base = os.path.join(base_path,photo,photo)
        ###############################

        list_fn = dict()

        for it in range_iter:
            fp = os.path.join(base_path,photo,photo+"_"+str(it),"html")
            fps = [os.path.join(fp,i) for i in os.listdir(fp) if ".html" in i]
            if len(fps) > 0:
                list_fn.update({it:fps})

        d_ = dict()

        for it,list_ in list_fn.items():
            d_.update({it:dict()})
            list_context = []

            for u in list_:
                context_images = imagescraper.findtags(u)
                if context_images is not None:
                    d_[it].update({u:context_images})

        cn = {}
        for iteration, dict1 in d_.items():
            cn.update({iteration:dict()})
            for fn,imgs in dict1.items():

                commas = [item for sublist in [i.split(',') for i in imgs if "," in i] for item in sublist]
                imgs = list(set(imgs + commas))

                correct = [i for i in imgs if "?w" not in i]
                potentials = [i.split("?w") for i in imgs if "?w" in i]

                for pbase in list(set([i[0] for i in potentials])):
                    all_p = [i for i in potentials if i[0] == pbase]
                    pdef = "?w".join(all_p[0])
                    if "," in pdef:
                        [correct.append(i) for i in pdef.split(',')]
                    else:
                        correct.append(pdef)
                cn[iteration].update({fn:correct})

        print('INFO: Dictionary made: {}'.format(os.path.join(base_path,photo,'context-images.json')))
        with open(os.path.join(base_path,photo,'context-images.json'), 'w') as fp:
            json.dump(cn, fp)

        urls = cn

        context_images_path = os.path.join(base_path,photo,"context_images")

        if not os.path.exists(context_images_path):
            os.makedirs(context_images_path)

        # Enable threading for faster scraping (requires function that works with single url)
        os.chdir(context_images_path)

        for k,v in urls.items():

            for page,all_url in v.items():
                with concurrent.futures.ThreadPoolExecutor() as e:
                    for u in all_url:
                        e.submit(imagescraper.Scrape, u)

        list_images = [l for l in os.listdir(context_images_path) if ".png" in l or ".jpg" in l or ".Jpeg" in l or ".Jpg" in l]
        small_images = [l for l in list_images if int(os.stat(l).st_size) < 1500]

        for i in small_images:
            os.remove(os.path.join(context_images_path,i))

        list_images = [l[:-4] for l in os.listdir(context_images_path) if ".png" in l or ".jpg" in l]
        list_redtxt = [l for l in os.listdir(context_images_path) if ".txt" in l and l[:-4] not in list_images]
        for i in list_redtxt:
            os.remove(os.path.join(context_images_path,i))
