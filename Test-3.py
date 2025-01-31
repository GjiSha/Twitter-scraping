import asyncio
import aiohttp
from playwright.async_api import async_playwright
import pandas as pd
import os
import numpy as np

df = pd.read_csv('dyper_tw_2024-10-01_2024-12-27.csv')
df['tweet_url'] = df['item_id'].apply(lambda x: f'https://twitter.com/anyuser/status/{x[2:]}')
df['Status'] = np.NaN

async def download_media(session, url, folder_path, tweet_id, index):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()

        file_extension = os.path.splitext(url.split('?')[0])[1]
        if not file_extension:
            file_extension = '.mp4' if 'video' in url else '.jpg'

        file_name = f"{tweet_id}_{index}{file_extension}"
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'wb') as file:
            file.write(content)

        print(f"Downloaded: {url} to {file_path}")
        return file_path, 'Downloaded'
    
    except aiohttp.ClientError as e:
        print(f"Error downloading {url}: {e}")
        return None, 'Not Downloaded'

async def process_tweet(page, session, url, folder_path):
    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
    except Exception as e:
        print(f'Error navigating to {url}: {e}')
        return [], 'Not Downloaded'

    try:
        os.makedirs(folder_path, exist_ok=True)
        tweet_id = url.split('/')[-1]
        media_urls = []

        # Find all tweet elements
        tweet_elements = await page.query_selector_all('article[data-testid="tweet"]')
        for tweet_element in tweet_elements:
            # Find all image elements within the tweet
            image_elements = await tweet_element.query_selector_all('img')
            for img_element in image_elements:
                src = await img_element.get_attribute('src')
                alt = await img_element.get_attribute('alt')
                if src and alt != "" and 'twimg.com' in src:
                    media_urls.append(src)
                    print(f"Found image URL: {src}")

            # Find all video elements within the tweet
            video_containers = await tweet_element.query_selector_all('div[data-testid="videoComponent"]')
            for video_container in video_containers:
                video_element = await video_container.query_selector('video')
                if video_element:
                    src = await video_element.get_attribute('src')
                    if src:
                        media_urls.append(src)
                        print(f"Found video URL: {src}")

        print(f"Total media URLs found: {len(media_urls)}")

        downloaded_files = []
        status = 'Not Downloaded'
        for index, media_url in enumerate(media_urls):
            file_path, download_status = await download_media(session, media_url, folder_path, tweet_id, index)
            if file_path:
                downloaded_files.append(file_path)
                status = 'Downloaded'

        return downloaded_files, status
    except Exception as e:
        print(f"An error occurred processing {url}: {e}")
        return [], 'Not Downloaded'

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        tweet_urls = list(df['tweet_url'])[:2]
        folder_path = 'downloaded_media'
        
        async with aiohttp.ClientSession() as session:
            for index, url in enumerate(tweet_urls):
                try:
                    downloaded_files, status = await process_tweet(page, session, url, folder_path)
                    print(f"Downloaded files for {url}: {downloaded_files}")
                    df.loc[index, 'Status'] = status
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    df.loc[index, 'Status'] = 'Not Downloaded'
                
                # Add a delay to avoid rate limiting
                await asyncio.sleep(2)

        df.to_csv('dyper_tw_2024-10-01_2024-12-27_updated.csv', index=False)

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
