import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def crawl_website(url):
    # Configure the browser settings
    browser_config = BrowserConfig(
        headless=True,  # Run in headless mode
        verbose=True,   # Enable verbose logging
    )
    
    # Configure the crawler run settings
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        excluded_tags=['nav', 'footer', 'aside'],
            remove_overlay_elements=True,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
                options={
                    "ignore_links": True
                }
            ),
    )
    
    # Use the AsyncWebCrawler to perform the crawl
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )
        return result.markdown

def main():
    url = "https://www.example.com"  # Replace with the target URL
    result = asyncio.run(crawl_website(url))
    print(result)

if __name__ == "__main__":
    main() 