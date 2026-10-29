import asyncio, sys, time, pathlib
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
async def main(local_html, live_url):
    bc = BrowserConfig(headless=True, verbose=False, extra_args=["--no-sandbox"])
    rc = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=30000)
    async with AsyncWebCrawler(config=bc) as c:
        t=time.time()
        r = await c.arun(url="file://"+str(pathlib.Path(local_html).resolve()), config=rc)
        md = str(r.markdown or "")
        print("LOCAL success", r.success, "secs", round(time.time()-t,1), "md_chars", len(md), "tables", len((r.tables or [])) if hasattr(r,'tables') else 'n/a')
        i = md.find("선화2구역"); print("LOCAL snippet:", md[max(0,i-150):i+120].replace("\n"," "))
        t=time.time()
        r = await c.arun(url=live_url, config=rc)
        print("LIVE success", r.success, "secs", round(time.time()-t,1), "status", r.status_code, "err", (r.error_message or "")[:300])
asyncio.run(main(sys.argv[1], sys.argv[2]))
