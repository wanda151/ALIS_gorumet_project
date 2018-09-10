import urllib
import json
import sys
import codecs
import urllib.request
import urllib.parse
import pprint
import datetime
import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from itertools import zip_longest

tag_name = "ALISグルメ企画"
new_tag_name= urllib.parse.quote(tag_name)
api_tag = 'https://alis.to/api/search/articles?tag='+new_tag_name
url_tag = urllib.request.urlopen(api_tag)
article_tags = json.loads(url_tag.read().decode("utf-8"))
article_ids = [article_tag.get('article_id') for article_tag in article_tags]
#article idを取り出す

user_ids = [article_tag.get('user_id') for article_tag in article_tags]
#user id を取り出す

api_article_ids = ["https://alis.to/api/articles/"+article_id for article_id in article_ids]
#article_idをAPIで取り出しやすい形にする

user_id_info_apis = ["https://alis.to/api/users/"+user_id+"/info" for user_id in user_ids]
#user_id_infoをAPIで取り出しやすい形にする

user_id_infos = [json.loads(urllib.request.urlopen(user_id_info_api).read().decode("utf-8")) for user_id_info_api in user_id_info_apis]
#/users/{user_id}/infoを取り出す

user_display_names = [user_id_info.get('user_display_name') for user_id_info in user_id_infos]
#user_display_name　を取り出す

likes_apis = ["https://alis.to/api/articles/"+article_id+"/likes" for article_id in article_ids]
#likes_apiをAPIで取り出しやすい形にする

likes = [json.loads(urllib.request.urlopen(likes_api).read().decode("utf-8")) for likes_api in likes_apis]
likes_counts = [like.get('count') for like in likes]
#Like数　を取り出す

articles_bodys = [json.loads(urllib.request.urlopen(api_article_id).read().decode("utf-8")) for api_article_id in api_article_ids]
def get_block(text, start_text, end_text):
    if not text.find(start_text) >= 0:
        return []
    new_texts = []
    for split_text in text.split(start_text):
        if split_text.find(end_text) >= 0:
            new_texts.append(split_text.split(end_text)[0])
    return new_texts
def get_block_tag(texts, start_text, end_text=None, tags=None):
    
    if not end_text:
        end_text = "<end>"
        
    if not tags:
        tags = ["企画タグ", "料理ジャンル", "店名", "住所"]
    
    texts = [text+end_text for text in texts]
    for tag in tags:
        texts = [text.replace(tag,end_text+tag) for text in texts]
    
    text = "".join(texts)
    
    if not text.find(start_text) >= 0:
        return []
    
    new_texts = []
    for split_text in text.split(start_text):
        if split_text.find(end_text) >= 0:
            new_texts.append(split_text.split(end_text)[0])
    
    remove_words = [":", "：", "<br>","(〒含む)","&nbsp;"]
    for remove_word in remove_words:
        new_texts = [new_text.replace(remove_word, "") for new_text in new_texts]
        
    new_texts = [new_text for new_text in new_texts if new_text]
    
    return new_texts

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
#googleスプレッドシートに書き込む準備をする

credentials = ServiceAccountCredentials.from_json_keyfile_name('ALIS-gourmet-project-a055ee392457.json', scope)
#jsonファイル

gc = gspread.authorize(credentials)
workbook = gc.open_by_key('1TFm1xMoRKLB95UrlA55ihlG3WNKpnqmL1595Yip568U')
#googleスプレッドシートを指定する

worksheet = workbook.sheet1
#sheet1を選択する
worksheet.clear()
line = 2 # initial value of line


for i, articles_body in enumerate(articles_bodys):
    texts = get_block(articles_body.get("body"), "<blockquote>", "</blockquote>")
    texts = [text for text in texts if text.find("〒") >= 0]
    project_names = get_block_tag(texts, "企画タグ")
    food_genres = get_block_tag(texts, "料理ジャンル")
    store_names = get_block_tag(texts, "店名")
    locations = get_block_tag(texts, "住所")
    
    article_url="https://alis.to/"+str(user_ids[i]) +"/articles/"+ str(article_ids[i])
    user_display_name = user_display_names[i]
    likes_count = likes_counts[i]

    for project_name, food_genre, store_name, location in zip_longest(project_names, food_genres, store_names, locations):
        tags_name=[project_name, food_genre, store_name, location]
        project_names = tags_name[0]
        food_genres = tags_name[1]
        store_names = tags_name[2]
        locations = tags_name[3]
        
        worksheet.update_cell(line, 1, project_names)
        worksheet.update_cell(line, 2, food_genres)
        worksheet.update_cell(line, 3, store_names) 
        worksheet.update_cell(line, 4, locations)
        worksheet.update_cell(line, 5, article_url)
        worksheet.update_cell(line, 6, user_display_name)
        worksheet.update_cell(line, 7, likes_count)

        line += 1

sheet_row_1 = ["企画タグ","料理ジャンル","店名","住所","記事URL","ユーザー名","いいね数"]
for i, sheet_rows_1 in enumerate(sheet_row_1):
    worksheet.update_cell(1, i+1, sheet_row_1[i])
print("実行完了!")
