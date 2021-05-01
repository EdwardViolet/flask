from database_util import database_util
from wordcloud import WordCloud
import PIL .Image as image
import numpy as np
import jieba
# 生成词云
class GenerWord:
    def __init__(self):
        self.database = database_util()
    
    def generNewsWord(self):
        # 查询数据
        content = self.database.query_last_week_news()
        self.get_image(self.removeUnuseWord(content),"./app/static/images/school_news.png")

    def removeUnuseWord(self,content):
        return content.replace('生日','').replace('学校','').replace('工作','')

    def generWeiboWord(self):
        content = self.database.query_last_week_weibo()
        self.get_image(self.removeUnuseWord(content),"./app/static/images/week.png")

    def generWeiboTopicWord(self):
        content = self.database.query_last_week_weibo_topic()
        self.get_image(self.removeUnuseWord(content),"./app/static/images/weibo_topic.png")

    def trans_CN(self,text):

        word_list = jieba.cut(text)
        # 分词后在单独个体之间加上空格
        result = " ".join(word_list)
        return result

    def get_image(self,data,savePath):

        coloring = np.array(image.open('./app/static/images/蒙版.png'))

        text  = self.trans_CN(data)

        wordcloud = WordCloud(
            mask=coloring,
            background_color="white",
            font_path = "C:\\Windows\\Fonts\\msyh.ttc"
        ).generate(text)

        # image_produce = wordcloud.to_image()
        # image_produce.show()
        wordcloud.to_file(savePath)

    def build_word(self):
        self.generNewsWord()
        self.generWeiboWord()
        self.generWeiboTopicWord()


if __name__ == "__main__":
    gener = GenerWord()
    gener.build_word()

