import time
import requests
import threading
import queue
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont
from io import BytesIO
from lxml import etree
import re
import csv
import string


def fetchUrl(urlQueue):
    while True:
        try:
   #不阻塞的读取队列数据
            url = urlQueue.get_nowait()
            i = urlQueue.qsize()
        except Exception as e:
            break
        try:
            list_res = requests.get(url)
        except Exception as e:
                continue
        if list_res.status_code == 200:
           #抓取内容的数据处理可以放到这里
           #为了突出效果， 设置延时
            soup = BeautifulSoup(list_res.text,'html.parser')
            h4s = soup.find_all('h4')
            for h4 in h4s:
                aa = h4.find_all('a')
                for a in aa:
                    #打开函数
                    url = 'https:'+a['href']  # 选取某一小说
                    print (url)
                    get_html_info(url)
                    web_font_relation = get_font(get_html_info(url)[0])
                    get_encode_font(get_html_info(url)[1],web_font_relation,get_html_info(url)[2],get_html_info(url)[3],get_html_info(url)[4],get_html_info(url)[5],get_html_info(url)[6],get_html_info(url)[7])


def get_font(url):
    """
    获取源代码中数字信息与英文单词之间的映射关系
    :param url: <str> 网页源代码中的字体地址
    :return: <dict> 网页字体映射关系
    """
    response = requests.get(url)
    font = TTFont(BytesIO(response.content))
    web_font_relation = font.getBestCmap()
    font.close()
    return web_font_relation


#在fontcreator中查看此ttf文件中英文单词与阿拉伯数字的映射关系，写入字典
python_font_relation = {
    'one':1,
    'two':2,
    'three':3,
    'four':4,
    'five':5,
    'six':6,
    'seven':7,
    'eight':8,
    'nine':9,
    'zero':0,
    'period':'.'
}

def get_html_info(url):
    """
    解析网页，获取文字文件的地址和需要解码的数字信息
    :param url: <str> 需要解析的网页地址
    :return:    <str> 文字文件ttf的地址
                <list> 反爬的数字，一维列表
    """
    proxy = ['219.138.58.114:3128', '61.135.217.7:80', '101.201.79.172:808', '122.114.31.177:808']
    # 用户代理列表
    headers = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
                 'User-Agent:Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident/5.0',
                 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
                 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16']

    html_data = requests.get(url)
    # 获取网页的文字ttf文件的地址
    url_ttf_pattern = re.compile('<style>(.*?)\s*</style>',re.S)
    fonturl = re.findall(url_ttf_pattern,html_data.text)[0]
    url_ttf = re.search('woff.*?url.*?\'(.+?)\'.*?truetype', fonturl).group(1)
    
    # 获取所有反爬的数字
    word_pattern = re.compile('</style><span.*?>(.*?)</span>', re.S)#制定正则匹配规则，匹配所有<span>标签中的内容
    numberlist = re.findall(word_pattern, html_data.text)
    
    soup = BeautifulSoup(html_data.text,'html.parser')
    info = soup.title
    book_name = "".join(re.compile('title>《'+'(.*?)'+'》_',re.S).findall(str(info)))
    author = "".join(re.compile('》_'+'(.*?)'+'著_',re.S).findall(str(info)))
    book_type = "".join(re.compile('著_'+'(.*?)'+'_',re.S).findall(str(info)))
    ifing = "".join(re.compile('<p class="tag"><span class="blue">'+'(.*?)'+'</span',re.S).findall(html_data.text))
    firsttime = re.compile('首发时间：'+'(.*?)'+' 章节字数：',re.S).findall(html_data.text)
    book_chapter = soup.select("#J-catalogCount")[0].string
    return url_ttf,numberlist,book_name,author,book_type,ifing,firsttime,book_chapter
def get_encode_font(numberlist,web_font_relation,book_name,author,book_type,ifing,firsttime,book_chapter):
    """
    把源代码中的数字信息进行2次解码
    :param numberlist: <list> 需要解码的一维数字信息
    :return:
    """
    data = [
        (book_name),(author),(book_type),(ifing),(firsttime[0]),(firsttime[-1]),(book_chapter)
    ]
    for i in numberlist:
        fanpa_data = ''
        index_i = numberlist.index(i)
        words = i.split(';')
        for k in range(0,len(words)-1):
            words[k] = words[k].strip('&#')
            #print(words[k])
            words[k] = str(python_font_relation[web_font_relation[int(words[k])]])
            #print(words[k])
            fanpa_data += words[k]
        #print(fanpa_data)
        
        data.append(fanpa_data)
    #print(data[0],'万字')
    #print(data[1], '万阅文总点击')
    #print(data[2], '万会员周点击')
    #print(data[3], '万总推荐')
    #print(data[4], '万周推荐')
    with open('demo.csv', 'a',encoding='utf-8') as f:
        writer = csv.writer(f)
        # 写入表头，表头是单行数据
        #writer.writerow(['歌曲', '用户名', '评论内容','点赞数'])
        # 写入这些多行数据
        writer.writerow(data)


    

#主函数
if __name__ == '__main__':
    startTime = time.time()
    baseurl = 'https://www.qidian.com/all?orderId=&style=1&pageSize=20&siteid=1&pubflag=0&hiddenField=0&page='
            

    urlQueue = queue.Queue()
    spag = 1
    epag = 5002
    while spag<epag:
        url = baseurl + str(spag)
        urlQueue.put(url)
        spag = spag+1

    threads = []
 # 可以调节线程数， 进而控制抓取速度
    threadNum = 20
    for i in range(0, threadNum):
        t = threading.Thread(target=fetchUrl, args=(urlQueue,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
  #多线程多join的情况下，依次执行各线程的join方法, 这样可以确保主线程最后退出， 且各个线程间没有阻塞
        t.join()

    endTime = time.time()
    #print ('Done, Time cost: %s ' % (endTime - startTime))
