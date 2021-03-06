'''
Script for identifying images on the web using the Google Cloud Vision API.
Author: Ruben Ros, ruben@rubenros.nl

The script uploads one or more photos to the API and retrieves the result. To increase the number of results, images that are located on the identified
webpages are reuploaded. Because of slight variations, this yields more results. However, this also introduces noise, as potentially irrelevant objects
are identified and taken as input in later iterations. It is therefore recommended to use the 'scrape-manual.py' script that works with command line arguments
and allows for the verification of the output after each iteration.

Required folder structure:

- photo_folder
  |__photo_1
     |__photo_1_source
        |__photo1.jpg
  |__photo_2
      |__photo_2_source
         |__photo2.jpg

'''

from multiprocessing.dummy import Pool as ThreadPool
import concurrent.futures
from gcv_api import main
from functions import *
import multiprocessing
from tqdm import tqdm
import logging
import os,sys
import time


dfr = pd.DataFrame()


for topfolder in ["carlo-batch"]:

    base_path = "/media/ruben/Data Drive/react-data/protest/{}".format(topfolder)
    print("INFO: found {} photos in folder {}".format(len([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]), topfolder))

    for photo in [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]:

        #Configuration:
        api_key = ""
        num_iterations = config_["num_iterations"]
        start_iter = config_["start_iter"]
        range_iter = [str(i) for i in list(range(1,num_iterations+1))]

        #Start Loop:
        for n in range_iter:

            print('INFO: -- Photo: {}'.format(photo))
            print('INFO: --- Iteration ' + str(n))

            # Post Images to API
            if int(n) == 1:
                input_folder_ = os.path.join(base_path, photo, photo + "_" + "source")

            if int(n) > 1:
                input_folder_ = os.path.join(base_path, photo, photo + "_" + str(int(n)-1), "img")

            try:
                main.main(
                        input_folder = input_folder_,
                        key = api_key,
                        output_folder = os.path.join(base_path, photo, photo + "_"),
                        iteration = n
                        )
            except Exception as e:
                print(e)
                dfr = dfr.append(pd.DataFrame([photo,int(n)-1]).T)
                break

            # Gather Image URLs from Output files (.json files) and (if n > 1) remove duplicates
            list_json = [os.path.join(base_path, photo, photo + "_" +str(n),f) for f in os.listdir(os.path.join(base_path,photo,photo + "_" + str(n))) if '.json' in f]
            image_url = Json.extract_image_folder(list_json)

            if int(n) > 1:
                processed_urls = []
                for iter_previous in range(1,int(n)):
                    list_json = [os.path.join(base_path, photo, photo + "_" +str(iter_previous),f) for f in os.listdir(os.path.join(base_path,photo,photo + "_" + str(iter_previous))) if '.json' in f]
                    image_url = Json.extract_image_folder(list_json)
                    processed_urls = processed_urls + image_url
                num_removed = len([u for u in image_url if u in processed_urls])
                print("INFO: {}/{} image-URLs removed (duplicates)".format(num_removed,len(image_url)))
                image_url = [u for u in image_url if u not in list(set(processed_urls))]

            # Check if there are Images to Scrape, if not: break and go to next Photo
            if len(image_url) == 0 or image_url is None:
                print("INFO: No URLs found in Iteration {}, going to next photo".format(n))
                dfr = dfr.append(pd.DataFrame([photo,int(n)-1]).T)
                break

            # Scrape images
            images_destination = os.path.join(base_path,photo,photo + "_" + str(n), "img")
            if not os.path.exists(images_destination):
                os.makedirs(images_destination)

            os.chdir(images_destination)
            Im.Scrape(image_url)

            # Remove duplicates
            if len(image_url) > 1:
                Im.RemoveSmall(images_destination,4000)
                Duplicates.remove(images_destination)

            time.sleep(10)

dfr.columns = ['photo','max_iteration']
dfr.to_csv(os.path.join(base_path,"results.csv"),index=False)
