SELECT * FROM bbc_news.bbc_news
-- drop table bbc_news.bbc_news
CREATE TABLE IF NOT EXISTS bbc_news.bbc_news
(
    news_id uuid NOT NULL,
    type CHARACTER VARYING(50),
    title CHARACTER VARYING(255),
    news_origin TEXT,
    news_tw TEXT,
    toeic_500 TEXT,
    toeic_700 TEXT,
	news_url CHARACTER VARYING(255),
    date date,
    CONSTRAINT bbc_news_pkey PRIMARY KEY (news_id)
)
SELECT pg_column_size(type) FROM bbc_news.bbc_news;
