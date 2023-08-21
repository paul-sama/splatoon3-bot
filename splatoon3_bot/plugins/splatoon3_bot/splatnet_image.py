from nonebot import logger
from playwright.async_api import async_playwright
from .splat import API_URL

COOKIES = [{'name': '_gtoken', 'value': 'undefined', 'domain': 'api.lp1.av5ja.srv.nintendo.net', 'path': '/',
            'expires': -1, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'}]


async def get_app_screenshot(gtoken, key='', url='', mask=False):
    logger.info(f'get_app_screenshot： {len(gtoken)}, {key}, {url}')
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        cookies = COOKIES[:]
        cookies[0]['value'] = gtoken
        height = 1000
        for _k in ('对战', '武器', '鲑鱼跑', '徽章'):
            if _k in key:
                height = 2500
        if mask:
            height = 740
        if url and 'coop' in url:
            height = 1500
        context = await browser.new_context(viewport={"width": 500, "height": height})
        await context.add_cookies(cookies)
        page = await context.new_page()
        if url:
            await page.goto(url)
            if mask and url and 'detail' in url:
                await page.locator('"WIN!"').nth(0).click()
                await page.locator('"LOSE..."').nth(0).click()
            if mask and url and 'coop' in url:
                for _r in ('"Clear!!"', '"Failure"'):
                    try:
                        await page.locator(_r).nth(0).click()
                    except:
                        pass
        else:
            await page.goto(f"{API_URL}/?lang=zh-CN")
        key = [] if not key else key.split(' ')
        for k in key:
            await page.get_by_text(k, exact=True).nth(0).click()
        await page.wait_for_timeout(6000)
        img_raw = await page.screenshot(full_page=True)

    return img_raw
