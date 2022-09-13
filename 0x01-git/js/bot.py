from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException, InvalidCookieDomainException
import undetected_chromedriver.v2 as uc
import time, argparse


def wait_for_page_loaded(driver):
    while driver.execute_script("return document.readyState") != "complete":
        time.sleep(1)
    return True

def wait_until_visible(driver, xpath=None, class_name=None, el_id=None, tag_name=None, duration=10000, frequency=0.01):
    if xpath:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
    elif class_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
    elif el_id:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, el_id)))
    elif tag_name:
        WebDriverWait(driver, duration, frequency).until(EC.visibility_of_all_elements_located((By.TAG_NAME, tag_name)))


def _accept_cookies(driver):
    accept_button = driver.find_element("xpath", '//*[@id="hf_cookie_text_cookieAccept"]')
    if accept_button.is_displayed() and accept_button.is_enabled():
        try:
            accept_button.send_keys(Keys.ENTER)
        except:
            accept_button = driver.find_element("xpath", '//*[@data-var="acceptBtn1"]')
            accept_button.click()
    return True


def accept_cookies(driver):
    try:
        return _accept_cookies(driver)
    except NoSuchElementException:
        return False

def _login(driver, email, password):
    logged_in = False
    accept_cookies(driver)
    wait_until_visible(driver, xpath='//*[@name="emailAddress"]', duration=10)
    try:
        wait_until_visible(driver, xpath='//*[@data-var="userName"]', duration=5)
        print("LOGGED IN")
        return True
    except TimeoutException:
        logged_in = False
    email_box = driver.find_element("xpath", '//*[@name="emailAddress"]')
    password_box = driver.find_element("xpath", '//*[@name="password"]')
    accept_button = driver.find_element("xpath", '//*[@type="button"]')
    driver.execute_script("arguments[0].value = arguments[1]", email_box, email)
    time.sleep(0.5)
    driver.execute_script("arguments[0].value = arguments[1]", password_box, password)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click()", accept_button)

def login(driver, email, password):
    is_logged_in = False
    n_tries = 5
    c_tries = 0
    while not is_logged_in:
        print(n_tries, c_tries)
        if _login(driver, email, password):
            is_logged_in = True
            break
        try:
            wait_until_visible(driver, class_name="nike-unite-error-close", duration=10)
            error_close = driver.find_element(By.CLASS_NAME, "nike-unite-error-close")
            time.sleep(100)
            error_close.find_element(By.TAG_NAME, "input").click()
            c_tries += 1
        except TimeoutException:
            is_logged_in = True
            break
        if c_tries == n_tries:
            break
        time.sleep(5)
    if not is_logged_in:
        print("LOGIN FAILED !!!")
        exit(0)

def scroll_down(steps=10):
    for x in range(0, steps):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.9)

def search(driver, query):
    while driver.current_url.find("w?q=") == -1:
        try:
            search_box = driver.find_element("xpath", '//*[@id="VisualSearchInput"]')
            #search_box.send_keys(Keys.ENTER)
            time.sleep(0.5)
            search_box.click()
            time.sleep(0.5)
            search_box.send_keys(query)
            time.sleep(0.5)
            driver.find_element("xpath", '//*[@data-var="vsButton"]').click()
            time.sleep(1)
        except StaleElementReferenceException:
            time.sleep(0.5)


def go_to_url(driver, url):
    while not driver.current_url == url:
        print(url, driver.current_url)
        driver.get(url)
        time.sleep(0.5)
    accept_cookies(driver) 

def select_item(driver, item, shoe_size):
    item.click()
    wait_for_page_loaded(driver)
    wait_until_visible(driver, class_name="size-grid-button", duration=10)

    time.sleep(0.5)

def select_shoe_size(driver, shoe_size):
    wait_until_visible(driver, xpath='//*[@id="buyTools"]', duration=10)
    size_found = False
    all_sizes = driver.find_elements("xpath", '//*[@name="skuAndSize"]')
    while not size_found:
        for s in all_sizes:
            try:
                s_parent = s.find_element(By.XPATH, "./..")
                label = s_parent.find_element(By.TAG_NAME, "label")
                if label:
                    if label.text.strip().replace(" ", "") == shoe_size.strip().replace(" ", ""):
                        if s.is_enabled():
                            driver.execute_script("arguments[0].click()", s)
                            size_found = True
                        else:
                            print(label.text, "Is disabled")
                            size_found = False
            except StaleElementReferenceException:
                pass
    return size_found

def get_collection_item(driver, collection, keyword, shoe_size):
    if not collection and not keyword:
        print("You have to give both a collection and a keyword to look for")
    if keyword.startswith('http'):
        if collection.startswith('http'):
            go_to_url(driver, collection)
            wait_for_page_loaded(driver)
    else:
        coll = COLLECTIONS.get(collection)
        if not coll:
            print("%s Does not exist in the current collections list" % collection)
            exit(1)
        go_to_url(driver, COLLECTIONS[collection])
        wait_for_page_loaded(driver)
    wait_until_visible(driver, xpath='//*[@data-testid="product-card"]')
    scroll_down()
    all_items = driver.find_elements("xpath", '//*[@data-testid="product-card"]')
    for i in all_items:
        name = i.text.split('\n', 1)[0]
        if keyword == name:
            link_elm = i.find_element("xpath", '//*[@class="product-card__link-overlay"]')
            link = link_elm.get_attribute("href")
            go_to_url(driver, link)
            wait_for_page_loaded(driver)
            break
    is_available = select_shoe_size(driver, shoe_size)
    if is_available:
        time.sleep(0.5)
        wait_until_visible(driver, xpath='//*[@data-browse-component="ATCButton"]')
        btn_div = driver.find_element("xpath", '//*[@data-browse-component="ATCButton"]')
        action_buttons = btn_div.find_elements(By.TAG_NAME, "button")
        driver.execute_script("arguments[0].click()", action_buttons[0])
        return True


def checkout(driver, cart_url, cvv):
    go_to_url(driver, cart_url)
    time.sleep(0.5)
    wait_until_visible(driver, xpath='//*[@data-automation="member-checkout-button"]')
    btn = driver.find_element("xpath", '//*[@data-automation="member-checkout-button"]')
    driver.execute_script("arguments[0].click()", btn)
    wait_until_visible(driver, class_name="checkout__summary-sections")
    btn = driver.find_element(By.CLASS_NAME, "btn--primary")
    driver.execute_script("arguments[0].click()", btn)
    print(181)
    wait_until_visible(driver, class_name="cart-item-display", duration=10)
    wait_for_page_loaded(driver)
    time.sleep(1.5)
    btn = driver.find_element(By.CLASS_NAME, "btn--primary")
    driver.execute_script("arguments[0].click()", btn)
    print(184)
    wait_until_visible(driver, class_name="order-summary")
    btn = driver.find_element(By.CLASS_NAME, "btn--primary")
    driver.execute_script("arguments[0].click()", btn)
    wait_until_visible(driver, el_id="cardCvv-input")
    driver.find_element(By.ID, "cardCvv-input").send_keys(cvv)
    time.sleep(0.5)
    driver.find_element(By.ID, "stored-cards-paynow").click()

def add_to_kart_all(driver, shoe_size):
    scroll_down()
    all_items = driver.find_elements("xpath", '//*[@data-testid="product-card"]')
    for i in all_items:
        print(dir(i))
        link_elm = i.find_element("xpath", '//*[@class="product-card__link-overlay"]')
        driver.get(link_elm.get_attribute('href'))
        wait_for_page_loaded(driver)
        wait_until_visible('size-grid-button', duration=10)
        all_sizes = driver.find_element("xpath", "//*[starts-with('@for', 'skuAndSize') and ends-with(@id, '_text')]")#("xpath", '//*[matches(@for="skuAndSize__27632098", skuAndSize__*)]')
        print(all_sizes)
        

if __name__ == "__main__":

    BASE_URL = "https://www.nike.com/th/"
    LOGIN_URL = "%s/member/profile/login?continueUrl=https://www.nike.com/th" % BASE_URL
    CART_URL = "%s/cart" % BASE_URL

    COLLECTIONS = {
            'Dunk': 'https://www.nike.com/th/w/dunk-shoes-90aohzy7ok',
            'Metcon': 'https://www.nike.com/th/w/metcon-shoes-3yxqszy7ok',
            'Jordan Paris Saint-Germain': 'https://www.nike.com/th/w/jordan-paris-saint-germain-37eefzaurdi',
            'SuperRep Training & Gym Shoes': 'https://www.nike.com/th/w/nike-superrep-training-gym-shoes-58jtoz8g3lnzy7ok',
            'Women\'s Nike Air Force 1': 'https://www.nike.com/th/w/womens-air-force-1-shoes-5e1x6z5sj3yzy7ok',
            'White Air Force 1': 'https://www.nike.com/th/w/white-air-force-1-shoes-4g797z5sj3yzy7ok',
            'Nike Essentials': 'https://www.nike.com/th/w/nike-essentials-3u82',
            'FlyEase Shoes': 'https://www.nike.com/th/w/flyease-shoes-1eghpzy7ok',
            'Air Force 1': 'https://www.nike.com/th/w/air-force-1-shoes-5sj3yzy7ok',
            'Blazer': 'https://www.nike.com/th/w/blazer-shoes-9gw3azy7ok',
            'Air Max': 'https://www.nike.com/th/w/air-max-shoes-a6d8hzy7ok',
            'Air Max 90': 'https://www.nike.com/th/w/air-max-90-shoes-auqmozy7ok',
            'Air Max Plus': 'https://www.nike.com/th/w/air-max-plus-shoes-ahvdnzy7ok',
            'Air Jordan 1': 'https://www.nike.com/th/w/jordan-1-shoes-4fokyzy7ok',
            'React Running Shoes': 'https://www.nike.com/th/w/react-running-shoes-37v7jz7cmrozy7ok',
            'Pegasus Running Shoes': 'https://www.nike.com/th/w/pegasus-running-shoes-37v7jz8nexhzy7ok',
            'Phantom Football Shoes': 'https://www.nike.com/th/w/phantom-football-shoes-1gdj0z1msyxzy7ok',
            'Mercurial Football Shoes': 'https://www.nike.com/th/w/mercurial-football-shoes-1gdj0z4f1bzy7ok',
            'National Team Football': 'https://www.nike.com/th/w/national-team-football-1gdj0zav9de',
            'Football Clubs': 'https://www.nike.com/th/w/club-football-teams-6fu9q',
            'F.C. Barcelona Kits & Shirts': 'https://www.nike.com/th/w/fc-barcelona-5y174',
            'Liverpool Kit & Shirts': 'https://www.nike.com/th/w/liverpool-fc-98py8',
            'Paris Saint-Germain Kit & Shirts': 'https://www.nike.com/th/w/paris-saint-germain-aurdi',
            'Chelsea': 'https://www.nike.com/th/w/chelsea-fc-2yc65',
            'Tottenham': 'https://www.nike.com/th/w/tottenham-8hd03',
            'Inter Milan': 'https://www.nike.com/th/w/inter-milan-qfxi',
            'Kids Nike Air Max Trainers': 'https://www.nike.com/th/w/kids-air-max-shoes-a6d8hzv4dhzy7ok',
            'Kids Air Force 1 Shoes': 'https://www.nike.com/th/w/kids-air-force-1-shoes-5sj3yzv4dhzy7ok',
            'Kids Running': 'https://www.nike.com/th/w/kids-running-37v7jzv4dh',
            'Kids Football': 'https://www.nike.com/th/w/kids-football-1gdj0zv4dh',
            'Kids Basketball': 'https://www.nike.com/th/w/kids-basketball-3glsmzv4dh',
            'Kids Training & Gym': 'https://www.nike.com/th/w/kids-training-gym-58jtozv4dh',
            'Kids Jordan': 'https://www.nike.com/th/w/kids-jordan-37eefzv4dh',
            }

    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--cvv", required=True, help="Credit Card Cvv")
    parser.add_argument("--shoe-size", required=True, help="Shoe Size")
    parser.add_argument("--collection", required=False, help="Collection to get results for")
    parser.add_argument("--keyword", required=False, help="Keyword or link for the item in the collection")
    parser.add_argument("--collections", required=False, action="store_true", help="Prints all collections")
    args = parser.parse_args()

    if args.collections:
        for c in COLLECTIONS.keys():
            print(c)
        exit()  

    options = uc.ChromeOptions()
    options.add_argument('example.com') # Opens the browser in en random url to bypass nike's bot detection
    options.add_argument('--user-data-dir=%s' % './.cache/')
    #options.add_argument("--headless")
    #options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.maximize_window()
    time.sleep(0.5)
    driver.execute_script("window.open('%s', '_blank')" % LOGIN_URL)
    time.sleep(0.5)
    wait_for_page_loaded(driver)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        })
    """
    })
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(1)
    accept_cookies(driver)
    time.sleep(1)   
    login(driver, args.email, args.password)
    wait_for_page_loaded(driver)
    print("Loaded")
    time.sleep(1)
    #search(driver, "Air Force 1")
    #time.sleep(0.5)
    wait_for_page_loaded(driver)
    item_available = get_collection_item(driver, args.collection, args.keyword, args.shoe_size)
    print(item_available)
    if item_available:
        print("Checking out")
        checkout(driver, CART_URL, str(args.cvv))
    time.sleep(1000)
