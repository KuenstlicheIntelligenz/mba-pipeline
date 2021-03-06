from bs4 import BeautifulSoup
import requests 
from requests_html import HTMLSession
import pandas as pd
import numpy as np
import argparse
import sys
import urllib.request
from urllib.request import Request, urlopen
import urllib.parse as urlparse
from urllib.parse import quote_plus
from urllib.parse import unquote_plus
from urllib.parse import urlencode
from urllib.parse import urljoin
import mba_url_creator as url_creator
import utils
import random 
from lxml.html import fromstring
from itertools import cycle
import datetime 
import shutil 
from google.cloud import storage
from google.cloud import bigquery
import os
import time 
from proxy_requests import ProxyRequests


def get_images_urls_not_crawled(marketplace):
    bq_client = bigquery.Client(project='mba-pipeline')
    df_images = bq_client.query("SELECT t0.asin, t0.url_image_hq, t0.url_image_lowq FROM mba_" + marketplace + ".products t0 LEFT JOIN mba_" + marketplace + ".products_images t1 on t0.asin = t1.asin where t1.asin IS NULL order by t0.timestamp").to_dataframe().drop_duplicates()
    return df_images

def save_img(response, file_name):
    with open("mba-pipeline/crawler/mba/data/shirts/"+ file_name +".jpg", 'wb') as f:
        f.write(response.get_raw())

def get_asin_images_crawled(table_id):
    '''
        Returns a unique list of asins that are already crawled
    '''
    bq_client = bigquery.Client(project='mba-pipeline')
    # todo: change table name in future | 
    list_asin = bq_client.query("SELECT asin FROM " + table_id + " group by asin").to_dataframe()["asin"].tolist()
    return list_asin

def main(argv):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('marketplace', help='Shortcut of mba marketplace. I.e "com" or "de", "uk"', type=str)
    parser.add_argument('--number_images', default=10, type=int, help='Number of images that shoul be crawled. If 0, every image that is not already crawled will be crawled.')

    # if python file path is in argv remove it 
    if ".py" in argv[0]:
        argv = argv[1:len(argv)]

    # get all arguments
    args = parser.parse_args(argv)
    marketplace = args.marketplace
    number_images = args.number_images
    
    # get all arguments
    args = parser.parse_args()

    # get already crawled asin list
    #asin_crawled_list = get_asin_images_crawled("mba_de.products_images")

    df_images = get_images_urls_not_crawled(marketplace)

    # if number_images is equal to 0, evry image should be crawled
    if number_images == 0:
        number_images = len(df_images)

    for j, image_row in df_images.iloc[0:number_images].iterrows():
        asin = image_row["asin"]
        url_image_hq = image_row["url_image_hq"]
        url_image_lowq = image_row["url_image_lowq"]

        #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
        #proxy_list = get_proxies("de", True)
        #proxy = next(iter(proxy_list))
        #proxies={"http": proxy, "https": proxy}

        r = ProxyRequests(url_image_hq)
        r.get()
        print("Proxy used: " + str(r.get_proxy_used()))
        if 200 == r.get_status_code():
            print(r.get_status_code())
            # save image locally
            with open("data/shirts/shirt.jpg", 'wb') as f:
                f.write(r.get_raw())

            utils.upload_blob("5c0ae2727a254b608a4ee55a15a05fb7", "data/shirts/shirt.jpg", "mba-shirts/"+marketplace+"/" + asin + ".jpg")
            df_img = pd.DataFrame(data={"asin":[asin],"url":["https://storage.cloud.google.com/5c0ae2727a254b608a4ee55a15a05fb7/mba-shirts/"+marketplace+"/"+asin+".jpg"],"url_gs":["gs://5c0ae2727a254b608a4ee55a15a05fb7/mba-shirts/"+marketplace+"/"+asin+".jpg"],"url_mba_lowq":[url_image_lowq],"url_mba_hq":[url_image_hq], "timestamp":[datetime.datetime.now()]}, dtype=np.object)
            df_img['timestamp'] = df_img['timestamp'].astype('datetime64')
            df_img.to_gbq("mba_" + marketplace + ".products_images",project_id="mba-pipeline", if_exists="append")
            print("Successfully crawled image: %s | %s of %s" % (asin, j+1, number_images))
        else:
            print("Could not crawl image: %s | %s of %s" (asin, j+1, number_images))
        
        #response = requests.get(quote_plus(url_image_hq),proxies=proxies,headers=headers, stream=True)
        test = 0

    bucket_name = "5c0ae2727a254b608a4ee55a15a05fb7"
    folder_name = "mba-shirts"
    file_path = "mba-pipeline/crawler/mba/data/test.jpg"
    #upload_blob("5c0ae2727a254b608a4ee55a15a05fb7", file_path , "mba-shirts/test.jpg")

    
    test = 0

if __name__ == '__main__':
    main(sys.argv)

