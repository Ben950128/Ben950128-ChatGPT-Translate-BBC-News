# ChatGPT-Translate-BBC-News
## 爬取BBC News
* 用apscheduler設定每天早上爬取BBC新聞。

## 串接gpt-3.5-turbo API
* 翻譯成繁體中文。
* 將BBC新聞依照多益程度進行改寫(ex: 將文章以多益500、700分程度進行改寫)。

## 新增資料進資料庫
* main.py 最後是將資料INSERT進PostgreSQL，以下為table的schema。
```
CREATE TABLE IF NOT EXISTS bbc_news.bbc_news
(
    news_id uuid NOT NULL,
    type character varying(50),
    title character varying(255),
    news_origin text,
    news_tw text,
    toeic_500 text,
    toeic_700 text,
	news_url character varying(255),
    date date,
    CONSTRAINT bbc_news_pkey PRIMARY KEY (news_id)
)
```
* main.ipynb 有將資料新增至Elasticsearch的範例。

## 啟動容器
```
docker compose up -d
```