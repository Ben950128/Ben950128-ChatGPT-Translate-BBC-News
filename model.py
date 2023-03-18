import openai
import os
from bs4 import BeautifulSoup


def connect_gpt_api(prompt: str)-> str:
    openai.api_key = os.getenv("CHATGPT_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


def crawl_bbc_news(driver):
    news_set = {
        "world": [], 
        "business": [], 
        "technology": [], 
        "science_and_environment": [], 
        "stories": [], 
        "entertainment_and_arts": [], 
        "health": []
    }
    news_temp_set = set()
    
    for news_type in news_set.keys():
        driver.get("https://www.bbc.com/news/" + news_type)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_tags = soup.select("a.gs-c-promo-heading")
        for title_tag in title_tags:
            if "news" in title_tag["href"] and "http" not in title_tag["href"] and title_tag["href"] not in news_temp_set:
                news_set[news_type].append(title_tag["href"])
                news_temp_set.add(title_tag["href"])
    return news_set