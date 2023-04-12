from model import connect_gpt_api, crawl_bbc_news, upload_image_to_s3
import os
import uuid
import psycopg
import warnings
import boto3
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()
warnings.simplefilter('ignore')
sched = BlockingScheduler(timezone="Asia/taipei")

def my_job():
    s3 = boto3.client("s3", 
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), 
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    news_set = crawl_bbc_news(driver)
    base_url = "https://www.bbc.com"

    # 將bbc新聞給chatgpt翻譯後塞進postgresql
    with psycopg.connect(os.getenv("DATABASE_CONFIG")) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT title FROM bbc_news.bbc_news")
            exist_news = {t[0] for t in cursor.fetchall()}
            
    for news_type in news_set.keys():
        num = 0
        for sub_url in news_set[news_type]:
            news_url = base_url + sub_url
            driver.get(news_url)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            article = soup.select("article")

            try:
                # 網址有可能是新聞影片
                title = article[0].select("header > h1")[0].text
                image_url = article[0].select(".ssrcss-evoj7m-Image.ee0ct7c0")[0]["src"]
            except:
                pass
            else:
                time_stamp = article[0].select("time[data-testid='timestamp']")[0]["datetime"]
                time_stamp_format = time_stamp.split("T")[0] + " " + time_stamp.split("T")[1].split(".")[0]
                news_time = datetime.strptime(time_stamp_format, "%Y-%m-%d %H:%M:%S")

                # 確保該新聞為今日新聞，且跟DB的新聞不重複
                if news_time < datetime.now() - timedelta(days=1) or title in exist_news:
                    continue
                contents = article[0].select("div[data-component='text-block']")
                news = " ".join([content.text for content in contents])

                # 控制新聞字數在800字內
                if len(news.split()) < 800:
                    num += 1
                    news_origin = connect_gpt_api(f"將以下文章分段，請用英文回傳:\n{news}").lstrip()
                    news_tw = connect_gpt_api(f"翻譯以下文章並分段，請用繁體中文回傳:\n{news_origin}").lstrip()
                    toeic_500 = connect_gpt_api(f"請用多益500的程度將文章改寫並分段，盡量不要刪減文章原意，請用英文回傳:\n{news_origin}").lstrip()
                    toeic_700 = connect_gpt_api(f"請用多益700的程度將文章改寫並分段，盡量不要刪減文章原意，請用英文回傳:\n{news_origin}").lstrip()
                    news_id = str(uuid.uuid4())
                    upload_image_to_s3(s3, image_url, news_type, news_id)
                    news_image_in_s3 = f"https://bbc-news-bucket.s3.ap-northeast-1.amazonaws.com/images/{news_type}/{news_id}.jpg"

                    with psycopg.connect(os.getenv("DATABASE_CONFIG")) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(f"""
                                INSERT INTO bbc_news.bbc_news 
                                ("news_id", "type", "title", "news_origin", "news_tw", "toeic_500", "toeic_700", "news_url", "image_path", "news_time") VALUES 
                                (%(news_id)s, %(type)s, %(title)s, %(news_origin)s, %(news_tw)s, %(toeic_500)s, %(toeic_700)s, %(news_url)s, %(image_path)s, %(news_time)s)
                            """, {
                                "news_id": news_id,
                                "type": news_type,
                                "title": title,
                                "news_origin": news_origin,
                                "news_tw": news_tw,
                                "toeic_500": toeic_500,
                                "toeic_700": toeic_700,
                                "news_url": news_url,
                                "image_path": news_image_in_s3,
                                "news_time": news_time
                            })
                            conn.commit()

                    news_origin, news_tw, toeic_500, toeic_700 = "", "", "", ""
                    print(news_type, flush=True)
                    if num == 1:    # 每個主題的新聞只insert 1個
                        break

    print(datetime.now(), "已新增完成", flush=True)

my_job()
sched.add_job(my_job, 'cron', hour='7', minute=0, second=0)
sched.start()