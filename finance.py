from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions
import requests

# from webdriver_manager.chrome import ChromeDriverManager
# # app = Flask(__name__)

# service = Service(executable_path=r"./chromedriver.exe")

options = Options()
options.add_argument('--headless')  # --headless
# options.binary_location = '/Applications/Arc.app/Contents/MacOS/Arc'
# driver_path = r"./chromedriver"
driver = webdriver.Chrome(options=options)
# driver.get("https://finance.yahoo.com/")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


def searchold(finp, isre=False):
    try:
        inputTag = driver.find_element(By.ID, "yfin-usr-qry")
        try:
            clearbutton = WebDriverWait(driver, 2).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="header-search-form"]/button')))
            clearbutton.click()
        except:
            pass
        inputTag.send_keys(finp)
        getlist = []
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="header-search-form"]/div[2]/div[1]/div/div[1]')))
        listbox = driver.find_elements(
            By.CLASS_NAME, "modules_quoteSymbol__hpPcM")
        # https://query1.finance.yahoo.com/v1/finance/search?q=aapl&lang=en-US

        print(listbox)
        for i in listbox:
            getlist.append(i.get_attribute('innerHTML'))

        return getlist
    except:
        if isre:
            return []
        else:
            driver.get("https://finance.yahoo.com/")
            return searchold(finp, True)


def search(finp, isre=False, num=0):
    se_stock = finp
    lang = "en-US"

    r = requests.get(
        f'https://query1.finance.yahoo.com/v1/finance/search?q={se_stock}&lang={lang}', headers=headers)
    # print code
    print(r.status_code)
    data = r.json()
    quotes = data['quotes']
    stocks = []
    for stocki in quotes:
        stocks.append(stocki['symbol'])
    if num == 5:
        return []
    else:
        if len(stocks) == 0:
            return search(finp, True, num+1)
        else:
            return stocks


def getinfoold(finp):
    print("finp", finp)
    original_window = driver.current_window_handle
    driver.switch_to.new_window('tab')
    driver.get(f"https://finance.yahoo.com/quote/{finp}")
    # get the price
    name = driver.find_element(
        By.XPATH, '//*[@id="quote-header-info"]/div[2]/div[1]/div[1]/h1').text

    price = driver.find_element(
        By.XPATH, '//*[@id="quote-header-info"]/div[3]/div[1]/div/fin-streamer[1]').text

    percentage = driver.find_element(
        By.XPATH, '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[3]/span').text

    adjustments = driver.find_element(
        By.XPATH, '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[2]/span').text

    try:
        if 'rgb(0, 171, 94)' in driver.find_element(
                By.XPATH, '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[2]/span').get_attribute('style'):
            adjustments = adjustments
            percentage = percentage.replace('(', '').replace(')', '')
        else:
            adjustments = adjustments
            percentage = percentage.replace('(', '').replace(')', '')

    except selenium.common.exceptions.NoSuchElementException:
        if 'rgb(0, 171, 94)' in driver.find_element(
                By.XPATH, '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[3]/span').get_attribute('style'):
            adjustments = adjustments
            percentage = percentage.replace('(', '').replace(')', '')
        else:
            adjustments = + adjustments
            percentage = + percentage.replace('(', '').replace(')', '')

    # close the tab
    driver.close()
    driver.switch_to.window(original_window)
    return {"name": name, "price": price, "percentage": percentage, "adjustments": adjustments}


def getinfo(finp, timerange="1d", intenvel="1m"):
    se_stock = finp
    print("finp", finp, timerange, intenvel)
    lang = "en-US"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_3_3; en-US) AppleWebKit/536.18 (KHTML, like Gecko) Chrome/53.0.1853.222 Safari/536',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

    # https://query1.finance.yahoo.com/v8/finance/chart/2317.TW
    r = requests.get(
        f'https://query1.finance.yahoo.com/v8/finance/chart/{se_stock}?interval={intenvel}&range={timerange}', headers=headers)

    data = r.json()
    currency = data['chart']['result'][0]['meta']['currency']
    symbol = data['chart']['result'][0]['meta']['symbol']
    exchangeName = data['chart']['result'][0]['meta']['exchangeName']
    instrumentType = data['chart']['result'][0]['meta']['instrumentType']
    firstTradeDate = data['chart']['result'][0]['meta']['firstTradeDate']
    regularMarketTime = data['chart']['result'][0]['meta']['regularMarketTime']
    gmtoffset = data['chart']['result'][0]['meta']['gmtoffset']
    timezone = data['chart']['result'][0]['meta']['timezone']
    exchangeTimezoneName = data['chart']['result'][0]['meta']['exchangeTimezoneName']
    regularMarketPrice = data['chart']['result'][0]['meta']['regularMarketPrice']
    chartPreviousClose = data['chart']['result'][0]['meta']['chartPreviousClose']
    previousClose = data['chart']['result'][0]['meta']['previousClose']
    scale = data['chart']['result'][0]['meta']['scale']
    # print(f"""
    #     currency: {currency}
    #     symbol: {symbol}
    #     exchangeName: {exchangeName}
    #     instrumentType: {instrumentType}
    #     firstTradeDate: {firstTradeDate}
    #     regularMarketTime: {regularMarketTime}
    #     gmtoffset: {gmtoffset}
    #     timezone: {timezone}
    #     exchangeTimezoneName: {exchangeTimezoneName}
    #     regularMarketPrice: {regularMarketPrice}
    #     chartPreviousClose: {chartPreviousClose}
    #     previousClose: {previousClose}
    #     scale: {scale}
    #     """)

    stamp_data = []
    length = len(data['chart']['result'][0]['timestamp'])
    for i in range(0, length):
        stamp = data['chart']['result'][0]['timestamp'][i]
        low = data['chart']['result'][0]['indicators']['quote'][0]['low'][i]
        high = data['chart']['result'][0]['indicators']['quote'][0]['high'][i]
        open = data['chart']['result'][0]['indicators']['quote'][0]['open'][i]
        close = data['chart']['result'][0]['indicators']['quote'][0]['close'][i]
        volume = data['chart']['result'][0]['indicators']['quote'][0]['volume'][i]
        stamp_data.append({
            "timestamp": int(stamp) * 1000,
            "low": low,
            "high": high,
            "open": open,
            "close": close,
            "volume": volume
        })

    r = requests.get(
        f'https://query1.finance.yahoo.com/v1/finance/search?q={se_stock}&lang={lang}', headers=headers)

    data = r.json()
    quotes = data['quotes']
    try:
        name = quotes[0].get('longname', quotes[0]['shortname'])
    except:
        return getinfo(finp)
    price = regularMarketPrice
    percentage = (regularMarketPrice - previousClose) / previousClose * 100
    adjustments = regularMarketPrice - chartPreviousClose

    return {"name": name, "price": price, "percentage": percentage, "adjustments": adjustments, "stamp_data": stamp_data, 'currency':  currency}


# 取得匯率
def getrate(fromex='USD', toex='TWD', price=1, ):
    headers.update(
        {'Referer': f'https://www.xe.com/currencyconverter/convert/?Amount={price}&From={fromex}&To={toex}'})
    headers.update({'Sec-Fetch-Site': 'same-site'})
    headers['Authorization'] = 'Basic bG9kZXN0YXI6ZG1nMllpcnRqTTRxMkVUTWQyc0hFOVhHVkZUV1dLSFQ='
    r = requests.get(
        f'https://www.xe.com/api/protected/midmarket-converter/', headers=headers)
    data = r.json()['rates']
    rate = data[toex]
    priceusd = price / data[fromex]
    priceret = priceusd * rate
    return priceret


# if __name__ == "__main__":
#     while True:
#         finp = input("Enter the stock symbol: ")
#         datal = search(finp)
#         if len(datal) == 0:
#             print("No results found")
#             continue
#         print("Results:")
#         for i in range(len(datal)):
#             print(f"{i}. {datal[i]}")
#         sekey = int(input("Select the stock (-1 to exit) : "))
#         if sekey != -1:
#             print(f"{datal[sekey]} {getinfo(datal[sekey])}")
#         print("Done")
print(getrate("USD", "JPY", 2))
