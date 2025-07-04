import os
import time
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Configuration from environment variables (SAFE - no hardcoded secrets)
URL = "https://secure.onreg.com/onreg2/bibexchange/?eventid=6736&language=us"
TO_EMAIL = os.environ.get('TO_EMAIL')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
NO_TICKETS_TEXT = "There are currently no race numbers for sale. Try again later."

def validate_config():
    """Validate that all required environment variables are set"""
    if not all([TO_EMAIL, FROM_EMAIL, EMAIL_PASSWORD]):
        print("ERROR: Missing required environment variables!")
        print("Please set: TO_EMAIL, FROM_EMAIL, EMAIL_PASSWORD")
        sys.exit(1)
    print("✓ Configuration validated")

def setup_driver():
    """Setup Chrome driver for GitHub Actions/cloud environment"""
    chrome_options = Options()
    
    # Essential headless options for GitHub Actions
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Fix for session conflicts
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-data-dir=/tmp/chrome_user_data_' + str(os.getpid()))
    chrome_options.add_argument('--disable-dev-tools')
    
    # Use webdriver-manager to auto-download correct ChromeDriver
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def check_ticket_availability(driver):
    """Check if tickets are available"""
    try:
        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Check if the "no tickets" message is present
        if NO_TICKETS_TEXT not in page_text:
            # Look for indicators of available tickets
            if "buy" in page_text.lower() or "race number" in page_text.lower():
                return True, "🎟️ TICKETS AVAILABLE! Check the website immediately!"
            else:
                return True, "⚠️ Page content has changed - please check manually!"
        
        return False, "No tickets available yet"
        
    except Exception as e:
        print(f"Error checking availability: {e}")
        return None, f"Error: {str(e)}"

def take_screenshot(driver):
    """Navigate to page and capture screenshot with ticket status"""
    try:
        # Load the page
        print(f"Loading {URL}...")
        driver.get(URL)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Additional wait for dynamic content
        
        # Check ticket availability
        available, status_message = check_ticket_availability(driver)
        
        # Scroll to bottom for screenshot
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Take screenshot
        screenshot_path = f"/tmp/ticket_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)
        
        print(f"Screenshot saved: {screenshot_path}")
        print(f"Status: {status_message}")
        
        return screenshot_path, available, status_message
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None, None, f"Error: {str(e)}"

def send_notification(screenshot_path, tickets_available, status_message):
    """Send email notification"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL
        
        # Set subject based on ticket availability
        if tickets_available:
            msg['Subject'] = f'🚨 CPH TICKETS AVAILABLE! - {datetime.now().strftime("%H:%M:%S")}'
        else:
            msg['Subject'] = f'CPH Ticket Check - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Add body
        body = f"""
        CPH Half 2025 Ticket Status Check
        
        Status: {status_message}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        URL: {URL}
        
        {"🏃‍♂️ GO TO THE WEBSITE NOW! 🏃‍♀️" if tickets_available else "Still monitoring..."}
        
        Screenshot attached below.
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', 
                             filename=f'ticket_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
                msg.attach(img)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(FROM_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
            
        print("✓ Email notification sent!")
        return True
        
    except Exception as e:
        print(f"✗ Error sending email: {e}")
        return False

def main():
    """Main function to monitor tickets"""
    print("=" * 50)
    print("CPH Half 2025 Ticket Monitor - TEST MODE (All Emails)")
    print(f"Time: {datetime.now()}")
    print(f"Monitoring: {URL}")
    print(f"Notifications to: {TO_EMAIL}")
    print("=" * 50)
    
    # Validate configuration
    validate_config()
    
    # Initialize driver
    driver = setup_driver()
    
    try:
        # Take screenshot and check status
        screenshot_path, tickets_available, status_message = take_screenshot(driver)
        
        # TEST MODE: Always send email to monitor consistency
        print("📧 TEST MODE: Sending email for consistency check...")
        send_notification(screenshot_path, tickets_available, status_message)
            
        # Clean up screenshot file
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            print("✓ Cleaned up screenshot file")
            
    finally:
        # Clean up
        driver.quit()
        print("✓ Browser closed")
    
    print("=" * 50)
    print("Check complete!")

if __name__ == "__main__":
    main()
