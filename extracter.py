# coding=utf-8

from goose import Goose
import logging
import feedparser
from NER_DB import nlp_DB as DB

db_obj = DB()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


goose_obj = Goose()

class text_extractor():
    #Get Text By beautiful soup
    def get_only_text(self,url):
        text = ''
        title = ''
        try:
            article = goose_obj.extract(url=url)
            title = article.title
            text = article.cleaned_text
            publish_date = article.publish_date
            meta_Description = article.meta_description
        except Exception:
            logger.debug(Exception)
            text = ''
            title = ''
            publish_date = ''
            meta_Description = ''
        return title, text, publish_date, meta_Description
    
    
    def parseRSS(self, rss_url):
        # Function to fetch the rss feed and return the parsed RSS
        return feedparser.parse( rss_url ) 

    
    def getLinks( self, rss_url):
        # Function grabs the rss feed links and returns them as a list
        link_rss = []
        feed = self.parseRSS( rss_url )
        for newsitem in feed['items']:
            link_rss.append(newsitem['links'])
        return link_rss

    def add_text_url(self, project_id, url):
        #  add data from url into database
        return_data = []
        title, text, publish_date, meta_Description = self.get_only_text(url)
        return_data_dic = {}
        return_data_dic['title'] = title
        return_data_dic['text'] = text
        try:
            text = text.encode('ascii', 'ignore').decode('ascii')
            db_obj.insert_record_content(project_id, title, text)
        except Exception as e:
            logger.error('Exception in Extracting text from URL ', exc_info=True)
            return 'error'
        return_data.append(return_data_dic)
        return return_data  
        
        
    def add_text_title(self, project_id, title, text):
        # add title and raw text in the Database
        return_data = []
        return_data_dic = {}
        return_data_dic['title'] = title
        return_data_dic['text'] = text
        try:
            text = text.encode('ascii', 'ignore').decode('ascii')
            db_obj.insert_record_content(project_id, title, text)
        except Exception as e:
            logger.error('Exception in Extracting text from URL ', exc_info=True)
            return 'error'
        return_data.append(return_data_dic)
        return return_data
        
    def add_text_RSS_Feed(self, project_id, rss_url):
        # A list to hold all links
        URLS = []
        all_links = []
        
        all_links.append( self.getLinks( rss_url ) )
        for hl in all_links:
            for i in hl:
                URLS.append(i[0]['href'])
       
        return_data = []
        for url in URLS:
            title, text, publish_date, meta_Description = self.get_only_text(url)
            return_data_dic = {}
            return_data_dic['title'] = title
            return_data_dic['text'] = text
            try:
                text = text.encode('ascii', 'ignore').decode('ascii')
                db_obj.insert_record_content(project_id, title, text)
            except Exception as e:
                raise e
            return_data.append(return_data_dic)
        return return_data  
    
# if __name__ == '__main__':

#     wks_obj = text_extractor()
#     project_id = 1
#     rss_url = 'http://pehub.com/category/pe-backed-ma/feed'
#     text = wks_obj.getText(project_id, rss_url)
#     print text
#     for i in text:
#         print i['title']