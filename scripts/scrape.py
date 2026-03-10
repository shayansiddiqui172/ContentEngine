import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os



load_dotenv()

# ---- CONFIG ----
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# The profiles you want to scrape
TARGET_PROFILES = [
    "https://www.linkedin.com/in/reidhoffman/",
    "https://www.linkedin.com/in/paulgraham/",
    "https://www.linkedin.com/in/naval/",
]

# ---- SETUP BROWSER ----
def get_driver():
    options = Options()
    # options.add_argument("--headless")  # comment this out during testing
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Make it look less like a bot
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# ---- LOGIN ----
def login(driver):
    print("Logging in...")
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(3)
    print("Logged in.")

# ---- SCRAPE PROFILE ----
def scrape_profile(driver, url):
    print(f"Scraping profile: {url}")
    driver.get(url)
    time.sleep(3)  # wait for page to load

    data = {}

    # Full name
    try:
        data["fullName"] = driver.find_element(
            By.CSS_SELECTOR, "h1.text-heading-xlarge"
        ).text.strip()
    except:
        data["fullName"] = None

    # Headline / bio
    try:
        data["bio"] = driver.find_element(
            By.CSS_SELECTOR, "div.text-body-medium"
        ).text.strip()
    except:
        data["bio"] = None

    # Follower count
    try:
        follower_text = driver.find_element(
            By.CSS_SELECTOR, "span.t-bold ~ span"
        ).text.strip()
        # e.g. "12,345 followers" → 12345
        data["followerCount"] = int(follower_text.replace(",", "").split()[0])
    except:
        data["followerCount"] = None

    # Location
    try:
        data["location"] = driver.find_element(
            By.CSS_SELECTOR, "span.text-body-small.inline"
        ).text.strip()
    except:
        data["location"] = None

    data["linkedinUrl"] = url
    data["posts"] = []  # posts scraped separately

    print(f"  Got: {data['fullName']} — {data['followerCount']} followers")
    return data

# ---- SCRAPE RECENT POSTS ----
def scrape_posts(driver, url, creator_id, num_posts=3):
    posts_url = url + "recent-activity/shares/"
    print(f"  Scraping posts from: {posts_url}")
    driver.get(posts_url)
    time.sleep(3)

    posts = []

    # Scroll to load posts
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    post_elements = driver.find_elements(
        By.CSS_SELECTOR, "div.feed-shared-update-v2"
    )[:num_posts]

    for i, post_el in enumerate(post_elements):
        post = {}

        # Post text
        try:
            post["keyInsight"] = post_el.find_element(
                By.CSS_SELECTOR, "div.feed-shared-text"
            ).text.strip()[:200]
        except:
            post["keyInsight"] = None

        # Reaction count
        try:
            reaction_text = post_el.find_element(
                By.CSS_SELECTOR, "span.social-details-social-counts__reactions-count"
            ).text.strip()
            post["reactions"] = int(reaction_text.replace(",", ""))
        except:
            post["reactions"] = 0

        # Comment count
        try:
            comment_text = post_el.find_element(
                By.CSS_SELECTOR, "li.social-details-social-counts__comments"
            ).text.strip()
            post["comments"] = int(comment_text.split()[0].replace(",", ""))
        except:
            post["comments"] = 0

        # Post URL
        try:
            post["postUrl"] = post_el.find_element(
                By.CSS_SELECTOR, "a.app-aware-link"
            ).get_attribute("href")
        except:
            post["postUrl"] = f"{url}post_{i}"

        post["creatorId"] = creator_id
        post["id"] = f"{creator_id}_post_{i}"
        post["format"] = "TEXT_ONLY"  # default, hard to detect automatically
        post["viralFlag"] = False
        post["secondaryTopics"] = []

        posts.append(post)
        print(f"    Post {i+1}: {post['reactions']} reactions")

    return posts

# ---- MAIN ----
def main():
    driver = get_driver()
    all_creators = []

    try:
        login(driver)

        for i, url in enumerate(TARGET_PROFILES):
            # Human-like delay between profiles
            time.sleep(4)

            creator_id = f"c{i+1}"
            creator = scrape_profile(driver, url)
            creator["id"] = creator_id

            # Scrape their posts
            posts = scrape_posts(driver, url, creator_id)
            creator["posts"] = posts

            all_creators.append(creator)

            # Random delay to avoid looking like a bot
            time.sleep(5)

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        driver.quit()

    # Save to JSON — same format as raw_creators.json
    with open("data/raw_creators.json", "w") as f:
        json.dump(all_creators, f, indent=2)

    print(f"\n✅ Scraped {len(all_creators)} creators. Saved to data/raw_creators.json")
    print("Now run: python3 scripts/ingest_data.py")

if __name__ == "__main__":
    main()