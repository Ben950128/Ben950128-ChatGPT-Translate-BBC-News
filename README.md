# ChatGPT-Translate-BBC-News
## 爬取BBC News新聞
* 用apscheduler設定每天早上爬取BBC新聞。

## 串接gpt-3.5-turbo API
* 翻譯成繁體中文。
* 將BBC新聞依照多益程度進行改寫(ex: 將文章以多益500、700分程度進行改寫)。

## 新增資料進資料庫
* main.py 是將資料INSERT進PostgreSQL。
* main.ipynb 有將資料新增至Elasticsearch的範例。

## 啟動程式
```
python main.py
```