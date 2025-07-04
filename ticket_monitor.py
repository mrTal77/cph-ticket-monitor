import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Configuration
URL = "https://secure.onreg.com/onreg2/bibexchange/?eventid=6736&language=us"
TO_EMAIL = "tilt09673@gmail.com"
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'your_email@gmail.com')  # Replace with your email
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_app_password')  # Replace with app password


def setup_driver(headless=True):
    """Setup Chrome driver with options"""
    chrome_options = Options()

    if headless:
        chrome_options.add_argument('--headless')

    # Additional options for better compatibility
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    return webdriver.Chrome(options=chrome_options)


def take_bottom_screenshot(driver):
    """Navigate to page and capture bottom section"""
    try:
        # Load the page
        print(f"Loading {URL}...")
        driver.get(URL)

        # Wait for page to load (wait for the specific text to appear)
        wait = WebDriverWait(driver, 10)
        time.sleep(3)  # Additional wait for dynamic content

        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for scroll to complete

        # Try to find the ticket status element
        try:
            # Look for the main content area that contains the ticket info
            # This captures the relevant bottom section
            element = driver.find_element(By.XPATH, "//body")

            # Get the dimensions to capture bottom portion
            location = element.location
            size = element.size

            # Calculate bottom section (approximately bottom 40% of page)
            viewport_height = driver.execute_script("return window.innerHeight")
            scroll_height = driver.execute_script("return document.body.scrollHeight")

            # Scroll to show bottom section properly
            driver.execute_script(f"window.scrollTo(0, {scroll_height - viewport_height});")
            time.sleep(1)

            # Take screenshot
            screenshot_path = f"ticket_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)

            print(f"Screenshot saved: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            print(f"Error finding element, taking full page screenshot: {e}")
            screenshot_path = f"full_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            return screenshot_path

    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None


def send_email_with_screenshot(screenshot_path):
    """Send email with screenshot attachment"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL
        msg['Subject'] = f'CPH Ticket Status - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

        # Add text
        body = f"""
        CPH Half 2025 Ticket Status Check

        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        URL: {URL}

        Screenshot attached below.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Attach screenshot
        with open(screenshot_path, 'rb') as f:
            img = MIMEImage(f.read())
            img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
            msg.attach(img)

        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(FROM_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)

        print("Email sent successfully!")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def main():
    """Main function to take screenshot and send email"""
    print("CPH Ticket Screenshot Bot Starting...")
    print(f"Time: {datetime.now()}")
    print(f"Will send screenshot to: {TO_EMAIL}")

    # Initialize driver (set headless=False to see the browser)
    driver = setup_driver(headless=False)  # Set to True for invisible operation

    try:
        # Take screenshot
        screenshot_path = take_bottom_screenshot(driver)

        if screenshot_path and os.path.exists(screenshot_path):
            # Send email
            if send_email_with_screenshot(screenshot_path):
                print("Process completed successfully!")
            else:
                print("Screenshot saved but email failed to send")
                print(f"Screenshot location: {screenshot_path}")
        else:
            print("Failed to take screenshot")

    finally:
        # Clean up
        driver.quit()

        # Optionally delete screenshot after sending
        # if screenshot_path and os.path.exists(screenshot_path):
        #     os.remove(screenshot_path)


if __name__ == "__main__":
    # First, update these values:
    print("\n⚠️  IMPORTANT: Before running, update these in the script:")
    print("1. Replace 'your_email@gmail.com' with your Gmail address")
    print("2. Replace 'your_app_password' with your Gmail app password")
    print("\nOr set them as environment variables:")
    print("export FROM_EMAIL='your_email@gmail.com'")
    print("export EMAIL_PASSWORD='your_app_password'\n")

    main()
