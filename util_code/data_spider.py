#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import codecs
import copy
import csv
import json
import math
import os
import random
import sys
import traceback
from collections import OrderedDict
from datetime import date, datetime, timedelta
from time import sleep
from time_util import trans_format
import unicodedata
import requests
from lxml import etree
from requests.adapters import HTTPAdapter
from tqdm import tqdm
import re
from bs4 import BeautifulSoup
import requests
from database_util import database_util
from config import *
from lxml import etree
from lxml import html
from html import unescape
import time
import re
import json
# 数据采集
class data_spider:
    def __init__(self):
        self.database = database_util()
        self.headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }
        self.cookie = {'Cookie': weibo_config['cookie']}  # 微博cookie，可填可不填
        self.user = {}  # 存储目标微博用户信息
        self.got_count = 0  # 存储爬取到的微博数
        self.weibo = []  # 存储爬取到的所有微博信息
        self.weibo_id_list = []  # 存储爬取到的所有微博id
        self.comments = [] # 存储爬取到的所有评论
        self.mysql_config = weibo_config['mysql_config']
        self.since_date = datetime.now().strftime('%Y-%m-%d')

    
    def start_spider(self):
        for item in spider_list:
            if(item == 'news'):
                self.spider_news()
            elif(item == 'tieba'):
                self.spider_tieba()
            elif(item == 'weibo'):
                self.spider_weibo()
    
    
    def spider_news(self):

        url = 'http://www.xbmu.edu.cn/frontChannelPage.action?siteId=12&articleClassId=151&currentPage={}'
        response = requests.get(url.format(1))
        html = etree.HTML(str(response.content,'utf-8'))
        per_count = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/div/span/text()')
        per_count = str(re.findall('(?<=/).{3}', str(per_count))).strip("['']")
        # all_count = html.xpath('//em[@class="all_pages"]/text()')[0])
        # page = (round(all_count//per_count) + 1) if (all_count%per_count!=0) else round(all_count//per_count)
        return_flag = False
        page = int(per_count)
        print(type(page))
        for i in range(1, page):
            try:
                list_url = url.format(i)
                response = requests.get(list_url)
                html = etree.HTML(str(response.content,'utf-8'))
                # # 创建人列表
                # creator_list = html.xpath('//table[@id="newslist"]//table//tr/td[1]/text()')
                # 新闻标题列表
                title_list = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/ul/li/div/div[2]/a/text()')
                # 新闻链接列表            //*[@id="wp_news_w13"]/ul/li[1]/p/span/a  /html/body/div[1]/div[3]/div[1]/div[3]/ul/li/div/div[2]/a
                link_list = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/ul/li/div/div[2]/a/@href')
                # print(link_list)

                # 创建时间列表
                create_time_list = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/ul/li/div/div[4]/text()')
                create_time_list = trans_format(str(create_time_list).strip("['']"))
                # print(create_time_list)
                # for i in range(len(create_time_list)):
                #     print(trans_format(create_time_list[i]))

                for i in range(len(title_list)):
                    item = dict()
                    item['title'] = title_list[i]
                    # 如果数据库中已经存在,就不用继续执行了
                    result = self.database.query_news(item['title'])
                    if(result):
                        return_flag = True
                        continue
                    item['creator'] = '学校官网'
                    item['create_time'] = create_time_list[i]
                    link = 'http://www.xbmu.edu.cn/'+link_list[i]
                    # print(link)
                    if('_redirect' in link or '/_upload' in link_list[i]):
                        item['content'] = ''
                        item['link'] = link
                        print(item['link'])
                    elif('https' in link_list[i] or 'http' in link_list[i]):
                        item['content'] = ''
                        item['link'] = link_list[i]
                        print(item['link'])
                    else:
                        try:
                            item['link'] = link
                            print(link)
                            response = requests.get(link)
                            # print(response)
                            html = etree.HTML(str(response.content,'utf-8'))
                            # print(str(response.content,'utf-8'))
                            content = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/div[3]/p/span/text()')
                            # content = unicodedata.normalize('NFKC', str(content))
                            content = str(content).strip("['']").replace(u'\u3000', '')
                            # content = etree.tostring(content, method='html')
                            # print(content)
                            item['content'] = content

                            create_time = html.xpath('/html/body/div[1]/div[3]/div[1]/div[3]/div[2]/text()')
                            item['create_time'] = trans_format(str(re.findall('(?<=发布时间：).{28}', str(create_time))).strip("['']"))
                            # print(item['create_time'])

                        except Exception as e:
                            print(e)
                            item['link'] = link
                            item['content'] = ''
                            continue

                    print(item)
                    self.database.save_news(item)
                if(return_flag):
                    continue
                if(i%20 == 0):
                    time.sleep(2)
            except Exception as e:
                print(e)
                continue
    
    # 采集百度贴吧的数据
    def spider_tieba(self):
        url = 'https://tieba.baidu.com/f?kw=%CE%F7%B1%B1%C3%F1%D7%E5%B4%F3%D1%A7&fr=ala0&tpl=5'
        self.spider_tieba_list(url)
    
     
    def GetMiddleStr(self,content,startStr,endStr):
        patternStr = r'%s(.+?)%s'%(startStr,endStr)
        p = re.compile(patternStr,re.IGNORECASE)
        m= re.match(p,content)
        if m:
            return m.group(1)

    # 时间转换
    def get_time_convert(self,timeStr):
        if(re.match('^\d{1,2}:\d{1,2}$',timeStr) != None):
            day = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            timeStr = day+' '+timeStr+':00'
        elif(re.match('^\d{4}-\d{1,2}$',timeStr) != None):
            day = time.strftime('%d',time.localtime(time.time()))
            timeStr = timeStr+'-'+day+' 00:00:00'
        elif(re.match('^\d{1,2}-\d{1,2}$',timeStr) != None):
            day = time.strftime('%Y',time.localtime(time.time()))
            timeStr = day+'-'+timeStr+' 00:00:00'
        return timeStr


    # 过滤表情
    def filter_emoji(self,desstr,restr=''):  
        try:  
            co = re.compile(u'[\U00010000-\U0010ffff]')  
        except re.error:  
            co = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')  
        return co.sub(restr, desstr)

    # 采集百度贴吧列表数据
    def spider_tieba_list(self,url):
        print(url)
        response = requests.get(url,headers=self.headers)
        try:
            response_txt = str(response.content,'utf-8')
        except Exception as e:
            response_txt = str(response.content,'gbk')
        # response_txt = str(response.content,'utf-8')
        bs64_str = re.findall('<code class="pagelet_html" id="pagelet_html_frs-list/pagelet/thread_list" style="display:none;">[.\n\S\s]*?</code>', response_txt)
        
        bs64_str = ''.join(bs64_str).replace('<code class="pagelet_html" id="pagelet_html_frs-list/pagelet/thread_list" style="display:none;"><!--','')
        bs64_str = bs64_str.replace('--></code>','')
        print(bs64_str)
        html = etree.HTML(bs64_str)
        # print(thread_list)
        # 标题列表
        title_list = html.xpath('//div[@class="threadlist_title pull_left j_th_tit "]/a[1]/@title')
        # print(title_list)
        # 链接列表
        link_list = html.xpath('//div[@class="threadlist_title pull_left j_th_tit "]/a[1]/@href')
        # 发帖人
        creator_list = html.xpath('//div[@class="threadlist_author pull_right"]/span[@class="tb_icon_author "]/@title')
        # 发帖时间
        create_time_list = html.xpath('//div[@class="threadlist_author pull_right"]/span[@class="pull-right is_show_create_time"]/text()')
        creator_list = creator_list[1:]
        create_time_list = create_time_list[1:]
        print(create_time_list)
        print(create_time_list[1])
        for i in range(len(title_list)):
            item = dict()
            item['create_time'] = create_time_list[i]
            if(item['create_time'] == '广告'):
                continue
            item['create_time'] = self.get_time_convert(item['create_time'])
            print(item['create_time'])
            item['title'] = self.filter_emoji(title_list[i])
            item['link'] = 'https://tieba.baidu.com'+link_list[i]
            item['creator'] = self.filter_emoji(creator_list[i]).replace('主题作者: ','')
            item['content'] = self.filter_emoji(item['title'])
            print(item['creator'])
            # 保存帖子数据
            result = self.database.query_tieba(item['link'])
            if(not result):
                self.database.save_tieba(item)
            self.spider_tieba_detail(item['link'])    
        # 定时采集任务则只采集最新的一页数据
        # 如果有下一页继续采集下一页
        # nex_page = html.xpath('//a[@class="next pagination-item "]/@href')
        # if(len(nex_page)>0):
        #     next_url = 'https:'+nex_page[0]
        #     self.spider_tieba_list(next_url)

    # 采集帖子详情页
    def spider_tieba_detail(self,link):
        response = requests.get(link,headers=self.headers)
        html = etree.HTML(response.text)
        data_fields = html.xpath('//*[@id="j_p_postlist"]/div/@data-field')
        # html = etree.HTML(str(response.content,'utf-8'))
        author_list = html.xpath('//div[@id="j_p_postlist"]/div/div[@class="d_author"]/ul/li[@class="d_name"]/a/text()')
        content_list = html.xpath('//div[@class="d_post_content j_d_post_content  clearfix"]/text()')
        id_list = html.xpath('//div[@class="d_post_content j_d_post_content  clearfix"]/@id')       
    
        for j in range(len(data_fields)):
            data_field = data_fields[j]
            data = json.loads(data_field)
            reply_item = dict()
            reply_item['content'] = self.filter_emoji(content_list[j])
            reply_item['creator'] = self.filter_emoji(author_list[j])
            reply_item['create_time'] = data['content']['date']
            reply_item['link'] = link            
            reply_item['reply_id'] = data['content']['post_id']
            reply_result = self.database.query_tieba_reply(reply_item['reply_id'])
            if(not reply_result):
                self.database.save_tieba_reply(reply_item)
        nex_page = html.xpath('//ul[@class="l_posts_num"]/text()/li[@class="l_pager pager_theme_5 pb_list_pager"]/@href')
        nex_page_text = html.xpath('//ul[@class="l_posts_num"]/text()/li[@class="l_pager pager_theme_5 pb_list_pager"]/text()')
        if(len(nex_page)>0):
            for t in range(len(nex_page_text)):
                if(nex_page_text[t]=='下一页'):
                    next_url = 'https://tieba.baidu.com'+nex_page[t]
                    self.spider_tieba_detail(next_url)

        
    def spider_weibo(self):
        self.get_pages()
        self.get_comments()


    def get_pages(self):
        """获取全部微博"""
        self.get_user_info()
        if self.get_page_count() > 100:
            global page_count
            page_count = 6
        wrote_count = 0
        page1 = 0
        random_pages = random.randint(1, 5)
        self.start_date = datetime.now().strftime('%Y-%m-%d')
        for page in tqdm(range(1, page_count + 1), desc='Progress'):
            is_end = self.get_one_page(page)
            if is_end:
                break
            if page % 5 == 0:  # 每爬20页写入一次文件
                self.weibo_to_mysql(wrote_count)
                wrote_count = self.got_count

            # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
            # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
            # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
            if (page - page1) % random_pages == 0 and page < page_count:
                sleep(random.randint(6, 10))
                page1 = page
                random_pages = random.randint(1, 5)

        self.weibo_to_mysql(wrote_count)  # 将剩余不足20页的微博写入文件
        print(u'微博爬取完成，共爬取%d条微博' % self.got_count)

    def get_user_info(self):
        """获取用户信息"""
        params = {'containerid': '100505' + str(weibo_config['user_id'])}
        js = self.get_json(params)
        if js['ok']:
            info = js['data']['userInfo']
            user_info = {}
            user_info['id'] = weibo_config['user_id']
            user_info['screen_name'] = info.get('screen_name', '')
            user_info['gender'] = info.get('gender', '')
            user_info['statuses_count'] = info.get('statuses_count', 0)
            user_info['followers_count'] = info.get('followers_count', 0)
            user_info['follow_count'] = info.get('follow_count', 0)
            user_info['description'] = info.get('description', '')
            user_info['profile_url'] = info.get('profile_url', '')
            user_info['profile_image_url'] = info.get('profile_image_url', '')
            user_info['avatar_hd'] = info.get('avatar_hd', '')
            user_info['urank'] = info.get('urank', 0)
            user_info['mbrank'] = info.get('mbrank', 0)
            user_info['verified'] = info.get('verified', False)
            user_info['verified_type'] = info.get('verified_type', 0)
            user_info['verified_reason'] = info.get('verified_reason', '')
            user = self.standardize_info(user_info)
            self.user = user

    def standardize_info(self, weibo):
        """标准化信息，去除乱码"""
        for k, v in weibo.items():
            if 'bool' not in str(type(v)) and 'int' not in str(
                    type(v)) and 'list' not in str(
                        type(v)) and 'long' not in str(type(v)):
                weibo[k] = v.replace(u"\u200b", "").encode(
                    sys.stdout.encoding, "ignore").decode(sys.stdout.encoding)
        return weibo

    def get_page_count(self):
        """获取微博页数"""
        try:
            weibo_count = self.user['statuses_count']
            page_count = int(math.ceil(weibo_count / 10.0))
            return page_count
        except KeyError:
            sys.exit(u'程序出错')


    def get_one_page(self, page):
        """获取一页的全部微博"""
        try:
            js = self.get_weibo_json(page)
            if js['ok']:
                weibos = js['data']['cards']
                for w in weibos:
                    if w['card_type'] == 9:
                        wb = self.get_one_weibo(w)
                        if wb:
                            if wb['id'] in self.weibo_id_list:
                                continue
                            created_at = trans_format(wb['created_at'])
                           #created_at = datetime.strptime(
                                # wb['created_at'], '%Y-%m-%d')

                            since_date = self.since_date
                            # since_date = datetime.strptime(
                               # self.since_date, '%Y-%m-%d')

                            # if created_at < since_date:
                            #     if self.is_pinned_weibo(w):
                            #         continue
                            # else:
                            #     print(u'{}已获取{}({})的第{}页微博{}'.format(
                            #         '-' * 30, self.user['screen_name'],
                            #         self.user['id'], page, '-' * 30))
                            #     return True

                            if ('retweet' not in wb.keys()):
                                self.weibo.append(wb)
                                self.weibo_id_list.append(wb['id'])
                                self.got_count += 1
            print(u'{}已获取{}({})的第{}页微博{}'.format('-' * 30, self.user['screen_name'], self.user['id'], page, '-' * 30))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def is_pinned_weibo(self, info):
        """判断微博是否为置顶微博"""
        weibo_info = info['mblog']
        title = weibo_info.get('title')
        if title and title.get('text') == u'置顶':
            return True
        else:
            return False

    def get_weibo_json(self, page):
        """获取网页中微博json数据"""
        params = {
            'containerid': '107603' + str(weibo_config['user_id']),
            'page': page
        }
        js = self.get_json(params)
        return js

    def get_json(self, params):
        """获取网页中json数据"""
        url = 'https://m.weibo.cn/api/container/getIndex?'
        r = requests.get(url, params=params, cookies=self.cookie)
        return r.json()

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo_info = info['mblog']
            weibo_id = weibo_info['id']
            retweeted_status = weibo_info.get('retweeted_status')
            is_long = weibo_info.get('isLongText')
            if retweeted_status:  # 转发
                retweet_id = retweeted_status.get('id')
                is_long_retweet = retweeted_status.get('isLongText')
                if is_long:
                    weibo = self.get_long_weibo(weibo_id)
                    if not weibo:
                        weibo = self.parse_weibo(weibo_info)
                else:
                    weibo = self.parse_weibo(weibo_info)
                if is_long_retweet:
                    retweet = self.get_long_weibo(retweet_id)
                    if not retweet:
                        retweet = self.parse_weibo(retweeted_status)
                else:
                    retweet = self.parse_weibo(retweeted_status)
                retweet['created_at'] = self.standardize_date(
                    retweeted_status['created_at'])
                weibo['retweet'] = retweet
            else:  # 原创
                if is_long:
                    weibo = self.get_long_weibo(weibo_id)
                    if not weibo:
                        weibo = self.parse_weibo(weibo_info)
                else:
                    weibo = self.parse_weibo(weibo_info)
            weibo['created_at'] = self.standardize_date(
                weibo_info['created_at'])
            return weibo
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_long_weibo(self, id):
        """获取长微博"""
        for i in range(5):
            url = 'https://m.weibo.cn/detail/%s' % id
            html = requests.get(url, cookies=self.cookie).text
            html = html[html.find('"status":'):]
            html = html[:html.rfind('"hotScheme"')]
            html = html[:html.rfind(',')]
            html = '{' + html + '}'
            js = json.loads(html, strict=False)
            weibo_info = js.get('status')
            if weibo_info:
                weibo = self.parse_weibo(weibo_info)
                return weibo
            sleep(random.randint(6, 10))

    def parse_weibo(self, weibo_info):
        weibo = OrderedDict()
        if weibo_info['user']:
            weibo['user_id'] = weibo_info['user']['id']
            weibo['screen_name'] = weibo_info['user']['screen_name']
        else:
            weibo['user_id'] = ''
            weibo['screen_name'] = ''
        weibo['id'] = int(weibo_info['id'])
        weibo['bid'] = weibo_info['bid']
        text_body = weibo_info['text']
        selector = etree.HTML(text_body)
        weibo['text'] = etree.HTML(text_body).xpath('string(.)')
        weibo['text'] = self.clear_character_chinese(weibo['text'])
        weibo['pics'] = self.get_pics(weibo_info)
        weibo['video_url'] = self.get_video_url(weibo_info)
        weibo['location'] = self.get_location(selector)
        weibo['created_at'] = weibo_info['created_at']
        weibo['source'] = weibo_info['source']
        weibo['attitudes_count'] = self.string_to_int(
            weibo_info.get('attitudes_count', 0))
        weibo['comments_count'] = self.string_to_int(
            weibo_info.get('comments_count', 0))
        weibo['reposts_count'] = self.string_to_int(
            weibo_info.get('reposts_count', 0))
        weibo['topics'] = self.get_topics(selector)
        weibo['at_users'] = self.get_at_users(selector)
        return self.standardize_info(weibo)

    #去除字母数字表情和其它字符
    def clear_character_chinese(self,sentence):
        pattern1='[a-zA-Z0-9]'
        pattern2 = '\[.*?\]'
        pattern3 = re.compile(u'[^\s1234567890:：' + '\u4e00-\u9fa5]+')
        pattern4='[’!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~]+'
        line2=re.sub(pattern2,'',sentence)   #去除表情
        new_sentence=''.join(line2.split()) #去除空白
        return new_sentence

    def get_pics(self, weibo_info):
        """获取微博原始图片url"""
        if weibo_info.get('pics'):
            pic_info = weibo_info['pics']
            pic_list = [pic['large']['url'] for pic in pic_info]
            pics = ','.join(pic_list)
        else:
            pics = ''
        return pics

    def get_live_photo(self, weibo_info):
        """获取live photo中的视频url"""
        live_photo_list = []
        live_photo = weibo_info.get('pic_video')
        if live_photo:
            prefix = 'https://video.weibo.com/media/play?livephoto=//us.sinaimg.cn/'
            for i in live_photo.split(','):
                if len(i.split(':')) == 2:
                    url = prefix + i.split(':')[1] + '.mov'
                    live_photo_list.append(url)
            return live_photo_list

    def get_video_url(self, weibo_info):
        """获取微博视频url"""
        video_url = ''
        video_url_list = []
        if weibo_info.get('page_info'):
            if weibo_info['page_info'].get('media_info') and weibo_info[
                    'page_info'].get('type') == 'video':
                media_info = weibo_info['page_info']['media_info']
                video_url = media_info.get('mp4_720p_mp4')
                if not video_url:
                    video_url = media_info.get('mp4_hd_url')
                    if not video_url:
                        video_url = media_info.get('mp4_sd_url')
                        if not video_url:
                            video_url = media_info.get('stream_url_hd')
                            if not video_url:
                                video_url = media_info.get('stream_url')
        if video_url:
            video_url_list.append(video_url)
        live_photo_list = self.get_live_photo(weibo_info)
        if live_photo_list:
            video_url_list += live_photo_list
        return ';'.join(video_url_list)

    def get_location(self, selector):
        """获取微博发布位置"""
        location_icon = 'timeline_card_small_location_default.png'
        span_list = selector.xpath('//span')
        location = ''
        for i, span in enumerate(span_list):
            if span.xpath('img/@src'):
                if location_icon in span.xpath('img/@src')[0]:
                    location = span_list[i + 1].xpath('string(.)')
                    break
        return location

    def get_topics(self, selector):
        """获取参与的微博话题"""
        span_list = selector.xpath("//span[@class='surl-text']")
        topics = ''
        topic_list = []
        for span in span_list:
            text = span.xpath('string(.)')
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                topic_list.append(text[1:-1])
        if topic_list:
            topics = ';'.join(topic_list)
        return topics

    

    def get_at_users(self, selector):
        """获取@用户"""
        a_list = selector.xpath('//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if '@' + a.xpath('@href')[0][3:] == a.xpath('string(.)'):
                at_list.append(a.xpath('string(.)')[1:])
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    def string_to_int(self, string):
        """字符串转换为整数"""
        if isinstance(string, int):
            return string
        elif string.endswith(u'万+'):
            string = int(string[:-2] + '0000')
        elif string.endswith(u'万'):
            string = int(string[:-1] + '0000')
        return int(string)

    def standardize_date(self, created_at):
        """标准化微博发布时间"""
        if u"刚刚" in created_at:
            created_at = datetime.now().strftime("%Y-%m-%d")
        elif u"分钟" in created_at:
            minute = created_at[:created_at.find(u"分钟")]
            minute = timedelta(minutes=int(minute))
            created_at = (datetime.now() - minute).strftime("%Y-%m-%d")
        elif u"小时" in created_at:
            hour = created_at[:created_at.find(u"小时")]
            hour = timedelta(hours=int(hour))
            created_at = (datetime.now() - hour).strftime("%Y-%m-%d")
        elif u"昨天" in created_at:
            day = timedelta(days=1)
            created_at = (datetime.now() - day).strftime("%Y-%m-%d")
        elif created_at.count('-') == 1:
            year = datetime.now().strftime("%Y")
            created_at = year + "-" + created_at
        return created_at

    # 获取全部微博的评论
    def get_comments(self):
        write_count = 0
        for mid in self.weibo_id_list:
            try:
                m_id = 0
                id_type = 0
                jsondata = self.get_comments_page(m_id, id_type,mid=mid)
                results = self.parse_comments_page(jsondata)
                maxpage = results['max']
                print('多少页',maxpage)
                for page in range(maxpage):
                    print('采集第{}页的微博'.format(page))
                    jsondata = self.get_comments_page(m_id, id_type,mid)
                    print(jsondata)
                    datas = jsondata.get('data').get('data')
                    self.add_comments_json(datas)
                    if(len(self.comments)%100 == 0):
                        self.comments_to_mysql(write_count)
                        write_count = write_count+100
                    results = self.parse_comments_page(jsondata)
                    sleep(random.randint(2,4))
                    if page%30==0:
                        sleep(6)
                    m_id = results['max_id']
                    id_type = results['max_id_type']    
            except Exception as e:
                print(e)
                pass           
        self.comments_to_mysql(write_count)

    def add_comments_json(self,jsondata):
        for data in jsondata:
            item = dict()
            item['id'] = data.get('id')
            item['mid'] = data.get('mid')
            item['like_count'] = data.get("like_count")
            item['source'] = data.get("source")
            item['floor_number'] = data.get("floor_number")
            item['screen_name'] = data.get("user").get("screen_name")
            # 性别
            item['gender'] = data.get("user").get("gender")
            if(item['gender'] == 'm'):
                item['gender'] = '男'
            elif(item['gender'] == 'f'):
                item['gender'] = '女'
            item['rootid'] = data.get("rootid")
            item['create_time'] = data.get("created_at")
            import time
            item['create_time'] = time.strptime(item['create_time'], '%a %b %d %H:%M:%S %z %Y')
            item['create_time'] = time.strftime('%Y-%m-%d',item['create_time'])
            item['comment'] = data.get("text")
            item['comment'] = BeautifulSoup(item['comment'], 'html.parser').get_text()
            item['comment'] = self.clear_character_chinese(item['comment'])
            print('当前楼层{},评论{}'.format(item['floor_number'],item['comment']))
            # 评论这条评论的信息
            comments = data.get("comments")
            if(comments):
                self.add_comments_json(comments)
            # print jsondata.dumps(comment, encoding="UTF-8", ensure_ascii=False)
            self.comments.append(item)
            
    def get_comments_page(self,max_id, id_type,mid):
        from get_weibo_cookie import get_cookie
        params = {
            'max_id': max_id,
            'max_id_type': id_type
            }
        try:
            url = 'https://m.weibo.cn/comments/hotflow?id={id}&mid={mid}&max_id='
        #     headers = {
        #     'Cookie': 'T_WM=96849642965; __guid=52195957.2500582256236055600.1583058027995.9556; WEIBOCN_FROM=1110006030; SCF=Aimq85D9meHNU4Ip0PFUjYBTDjXFB0VtQr3EKoS8DHQDobRNUO3lDIufAcUg69h4J7BQWqryxQpuU3ReIHHxvQ4.; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5H0p180lDMiCjNvXD_-uOh5JpX5KzhUgL.FoM0S0n0eo-0Sh.2dJLoI0qLxKqL1KMLBK-LxK-LBonLBonLxKMLB.-L12-LxK-LBK-LBoeLxK-L1hnL1hqLxKBLB.2LB-zt; XSRF-TOKEN=ca0a29; SUB=_2A25zWlwFDeRhGeFN7FoS8ivPzzWIHXVQpWRNrDV6PUJbkdANLW_9kW1NQ8CH90H5f8j5r1NA4GNPvu6__ERL-Jat; SUHB=0vJIkXXtLIIaZO; SSOLoginState=1583230037; MLOGIN=1; M_WEIBOCN_PARAMS=oid%3D4474164293517551%26luicode%3D20000174%26lfid%3D102803%26uicode%3D20000174; monitor_count=45',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        #     'X-Requested-With': 'XMLHttpRequest'
        # }
            r = requests.get(url.format(id=mid,mid=mid), params=params)
            print(r.url)
            if r.status_code == 200:
                return r.json()
        except requests.ConnectionError as e:
            print('error', e.args)    
    
    def add_comments(self,jsondata):
        datas = jsondata.get('data').get('data')
        for data in datas:
            item = dict()
            item['id'] = data.get('id')
            item['mid'] = data.get('mid')
            item['like_count'] = data.get("like_count")
            item['source'] = data.get("source")
            item['floor_number'] = data.get("floor_number")
            item['screen_name'] = data.get("user").get("screen_name")
            # 性别
            item['gender'] = data.get("user").get("gender")
            if(item['gender'] == 'm'):
                item['gender'] = '男'
            elif(item['gender'] == 'f'):
                item['gender'] = '女'
            item['created_at'] = self.standardize_date(
                data.get(['created_at']))
            import time
            item['create_time'] = time.strptime(item['create_time'], '%a %b %d %H:%M:%S %z %Y')
            item['create_time'] = time.strftime('%Y-%m-%d',item['create_time'])
            item['rootid'] = data.get("rootid")
            
            item['comment'] = data.get("text")
            item['comment'] = BeautifulSoup(item['comment'], 'html.parser').get_text()
            item['comment'] = self.clear_character_chinese(item['comment'])
            print('当前楼层{},评论{}'.format(item['floor_number'],item['comment']))
            # 评论这条评论的信息
            comments = data.get("comments")

            # print jsondata.dumps(comment, encoding="UTF-8", ensure_ascii=False)
            self.comments.append(item)

    def parse_comments_page(self,jsondata):
        if jsondata:
            items = jsondata.get('data')
            item_max_id = {}
            item_max_id['max_id'] = items['max_id']
            item_max_id['max_id_type'] = items['max_id_type']
            item_max_id['max'] = items['max']
            return item_max_id    

    def weibo_to_mysql(self, wrote_count):
        """将爬取的微博信息写入MySQL数据库"""
        mysql_config = {
        }
        weibo_list = []
        retweet_list = []
        info_list = self.weibo[wrote_count:]
        for w in info_list:
            # print(info_list[0]['created_at'])
            # 数据库存储时间格式化
            w['created_at'] = trans_format(w['created_at'])

            if 'retweet' in w:
                w['retweet']['retweet_id'] = ''
                retweet_list.append(w['retweet'])
                w['retweet_id'] = w['retweet']['id']
                del w['retweet']
            else:
                w['retweet_id'] = ''
            weibo_list.append(w)
        # 在'weibo'表中插入或更新微博数据
        self.mysql_insert(mysql_config, 'weibo', retweet_list)
        self.mysql_insert(mysql_config, 'weibo', weibo_list)
        print(u'%d条微博写入MySQL数据库完毕' % self.got_count)

    def comments_to_mysql(self,write_count):
        """将爬取的用户信息写入MySQL数据库"""
        mysql_config = {
        }
        self.mysql_insert(mysql_config, 'comments', self.comments[write_count:])

    def mysql_insert(self, mysql_config, table, data_list):
        """向MySQL表插入或更新数据"""
        import pymysql

        if len(data_list) > 0:
            keys = ', '.join(data_list[0].keys())
            values = ', '.join(['%s'] * len(data_list[0]))
            if self.mysql_config:
                mysql_config = self.mysql_config
            connection = pymysql.connect(**mysql_config)
            cursor = connection.cursor()

            sql = """INSERT INTO {table}({keys}) VALUES ({values}) ON
                     DUPLICATE KEY UPDATE""".format(table=table,
                                                    keys=keys,
                                                    values=values)
            update = ','.join([
                " {key} = values({key})".format(key=key)
                for key in data_list[0]
            ])
            sql += update
            try:
                cursor.executemany(
                    sql, [tuple(data.values()) for data in data_list])
                connection.commit()
            except Exception as e:
                connection.rollback()
                print('Error: ', e)
                traceback.print_exc()
            finally:
                connection.close()


    
if __name__ == "__main__":
    data_spider = data_spider()
    data_spider.start_spider()
    # test()

