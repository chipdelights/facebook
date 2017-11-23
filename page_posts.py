#Author : Pavani Boga ( pavanianapla@gmail.com )
#Date: 11/18/2017
#Job: https://www.upwork.com/jobs/~01c09ae409e0b04306
#This script will fetch all the posts , likes and comments from a facebook page and save it to mysqldb
#Run : python3.6 page_posts.py -u <<fb_username>> -p <<fb_password>> -f <<page_urls.txt>>

import requests
import json
from selenium import webdriver
import pymysql
import time
import re
import random
import argparse

fb_url = 'https://graph.facebook.com/v2.10/'

def gen_token(username,password):
    browser = webdriver.Chrome()
    browser.get('https://wwww.facebook.com/login.php')
    email = browser.find_element_by_id('email')
    email.send_keys(username)
    passwd = browser.find_element_by_id('pass')
    passwd.send_keys(password)
    login = browser.find_element_by_id('loginbutton')
    login.click()
    browser.get('https://developers.facebook.com/tools/explorer')
    token = browser.find_element_by_xpath('//input[contains(@placeholder,"Paste in an existing Access Token")]').get_attribute('value')
    browser.close()
    return token

def make_http(url,randsleep=5):
    res = list()
    while True:
        try:
            #time.sleep(random.randint(1,randsleep))
            r = requests.get(url)
            if not r.ok:
                print('Exception in Facebook API Call: %s' %r.text)
                sys.exit(1)
            response = json.loads(r.text)
            if 'data' in response:
                res.extend([entry for entry in response['data']])
            else:
                res.append(response)
            url = response['paging']['next']
        except Exception as e:
            break

    return res

def mysql_init(topic):
    connection = pymysql.connect(host='localhost',user='root',db='posts',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor,use_unicode=True,autocommit=True)
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS %s_posts;CREATE TABLE %s_posts(post_id VARCHAR(256), message VARCHAR(10240) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci, no_likes INT, no_comments INT) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci" %(topic,topic))
    cursor.execute("DROP TABLE IF EXISTS %s_comments;CREATE TABLE %s_comments(post_id VARCHAR(256), comment VARCHAR(10240) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci" %(topic,topic))
    return cursor

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--user',help='Facebook User Name')
    parser.add_argument('-p','--password',help='Facebook User Password')
    parser.add_argument('-f','--file',help='Facebook URLs File')
    args = parser.parse_args()
    token = gen_token(args.user,args.password)

    for page in open('/tmp/fb_urls.txt').readlines():
        page_id = page.split('/')[-1].strip()
        cursor = mysql_init(page_id)
        # get posts
        posts_url = fb_url + page_id + '/posts?limit=100&access_token=%s' %token
        response = make_http(posts_url)
        posts = [ entry['id'] for entry in response ]
        for post in posts:
            msg_url = fb_url + post + '?fields=message&access_token=%s' %token
            msg_response = make_http(msg_url)[0]
            try:
                msg = msg_response['message']
            except Exception as e:
                story_url = fb_url + post + '?fields=story&access_token=%s' %token
                story_response = make_http(story_url)[0]
                try:
                    msg = story_response['story']
                except Exception as e:
                    msg = 'NA'
            likes_url = fb_url + post + '/likes?limit=100&access_token=%s' %token
            likes_response = make_http(likes_url)
            comments_url = fb_url + post + '/comments?limit=100&access_token=%s' %token
            comments_response = make_http(comments_url)
            comments = [entry['message'] for entry in comments_response]
            #out_text.append({ 'msg':dd msg, 'no_likes': len(likes_response), 'no_comments': len(comments), 'comments': comments })
            cursor.execute("INSERT INTO %s_posts(post_id,message,no_likes,no_comments) VALUES('%s','%s',%d,%d)" %(page_id,post,pymysql.escape_string(msg),len(likes_response),len(comments)))
            for comment in comments:
                cursor.execute("INSERT INTO %s_comments(post_id,comment) VALUES('%s','%s')" %(page_id,post,pymysql.escape_string(comment)))


            
