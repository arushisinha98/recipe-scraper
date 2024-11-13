from crawler import RecipeCrawler, get_start_url

start_url = get_start_url("https://www.gimmesomeoven.com/all-recipes")
crawler = RecipeCrawler(start_url, 10)
crawler.crawl()

