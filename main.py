from model import connect_gpt_api, crawl_bbc_news
import os
import uuid
import psycopg
import warnings
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()
warnings.simplefilter('ignore')
sched = BlockingScheduler(timezone="Asia/taipei")

def my_job():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    news_set = crawl_bbc_news(driver)

    # 將bbc新聞給chatgpt翻譯後塞進postgresql
    conn = psycopg.connect(os.getenv("DATABASE_CONFIG"))
    cursor = conn.cursor()
    base_url = "https://www.bbc.com"
    for key in news_set.keys():
        num = 0
        for sub_url in news_set[key]:
            news_url = base_url + sub_url
            driver.get(news_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            article = soup.select("article")

            try:
                # 網址有可能是新聞影片
                header = article[0].select("header > h1")[0].text
            except:
                pass
            else:
                contents = article[0].select("div[data-component='text-block']")
                news = " ".join([content.text for content in contents])
                # 控制新聞字數在800字內
                if len(news.split()) < 800:
                    num += 1
                    news_origin = connect_gpt_api(f"將以下文章分段，請用英文回傳:\n{news}").lstrip()
                    news_tw = connect_gpt_api(f"翻譯以下文章並分段，請用繁體中文回傳:\n{news_origin}").lstrip()
                    toeic_500 = connect_gpt_api(f"請用多益500的程度將文章改寫並分段，盡量不要刪減文章原意，請用英文回傳:\n{news_origin}").lstrip()
                    toeic_700 = connect_gpt_api(f"請用多益700的程度將文章改寫並分段，盡量不要刪減文章原意，請用英文回傳:\n{news_origin}").lstrip()
                    cursor.execute(f"""
                        INSERT INTO bbc_news.bbc_news 
                        ("news_id", "type", "title", "news_origin", "news_tw", "toeic_500", "toeic_700", "news_url", "date") VALUES 
                        (%(id)s, %(type)s, %(title)s, %(news_origin)s, %(news_tw)s, %(toeic_500)s, %(toeic_700)s, %(news_url)s, %(today)s)
                    """, {
                        "id": str(uuid.uuid4()),
                        "type": key,
                        "title": header,
                        "news_origin": news_origin,
                        "news_tw": news_tw,
                        "toeic_500": toeic_500,
                        "toeic_700": toeic_700,
                        "news_url": news_url,
                        "today": str(date.today())
                    })
                    conn.commit()
                    print(key, flush=True)
                    if num == 1:    # 每個主題的新聞只insert 1個
                        break
    cursor.close()
    conn.close()

my_job()
sched.add_job(my_job, 'cron', hour='7', minute=0, second=0)
sched.start()