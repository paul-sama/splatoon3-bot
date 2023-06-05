from nonebot import logger
from playwright.async_api import async_playwright
from .splat import API_URL

COOKIES = [{'name': '_gtoken', 'value': 'undefined', 'domain': 'api.lp1.av5ja.srv.nintendo.net', 'path': '/',
            'expires': -1, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'}]


async def get_app_screenshot(gtoken, key='', url=''):
    logger.info(f'get_app_screenshot： {len(gtoken)}, {key}, {url}')
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        cookies = COOKIES[:]
        cookies[0]['value'] = gtoken
        context = await browser.new_context(viewport={"width": 500, "height": 1000})
        await context.add_cookies(cookies)
        page = await context.new_page()
        if url:
            await page.goto(url)
        else:
            await page.goto(f"{API_URL}/?lang=zh-CN")
        key = [] if not key else key.split(' ')
        for k in key:
            await page.get_by_text(k).click()
        await page.wait_for_timeout(6000)
        img_raw = await page.screenshot(full_page=True)

    return img_raw
