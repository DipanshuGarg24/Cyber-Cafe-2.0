#  lets create the new app 

import glob
import streamlit as st
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from PIL import Image
from io import BytesIO
from google import  genai

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'input_aadhaar'
    st.session_state.driver = None
    st.session_state.client = None
    st.session_state.aadhaar_number = ''
    st.session_state.otp = ''

# Configure page
st.set_page_config(page_title="Cyber Cafe 2.0", page_icon="🖥️")
st.title("Cyber Cafe 2.0 - Aadhaar Download")

# Initialize Gemini and Selenium
@st.cache_resource
def init_services():
    try:
        # genai.configure(api_key="AIzaSyBvE1cAwhiT8zUW0U_p_Vqoeu-qNxsynwQ")
        # client = genai.GenerativeModel('gemini-1.5-flash')
        client = genai.Client(api_key="AIzaSyBvE1cAwhiT8zUW0U_p_Vqoeu-qNxsynwQ")
        options = Options()
        options.add_argument("--headless")
        # options.add_argument("--start-maximized")
        # options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        
        return client, driver
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        return None, None

def get_captcha_text(img_bytes):
    try:
        image = genai.types.Part.from_bytes(
            data=img_bytes, mime_type="image/png"
        )
        response = st.session_state.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["You are very advanced image recoginition person in the whole person who is able to solve any captcha , solve the given captcha , return only captha code ?", image],
        )

        print(response.text)
        return response.text
    except Exception as e:
        st.error(f"CAPTCHA solving failed: {str(e)}")
        return None

def setup_driver():
    try:
        st.session_state.driver.get("https://myaadhaar.uidai.gov.in/genricDownloadAadhaar")
        WebDriverWait(st.session_state.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[1]/div/div/div/input"))
        )
        # time.sleep(5)  # Wait for the page to load completely
        return True
    except Exception as e:
        st.error(f"Failed to load Aadhaar portal: {str(e)}")
        return False

# Main application flow
def main():
    if st.session_state.client is None or st.session_state.driver is None:
        st.session_state.client, st.session_state.driver = init_services()
        if st.session_state.client is None or st.session_state.driver is None:
            return

    if st.session_state.step == 'input_aadhaar':
        aadhaar_number = st.text_input("Enter 12-digit Aadhaar number:", max_chars=12, key="aadhaar_input")
        
        if st.button("Next"):
            if len(aadhaar_number) == 12 and aadhaar_number.isdigit():
                st.session_state.aadhaar_number = aadhaar_number
                st.session_state.step = 'process_aadhaar'
                st.rerun()
            else:
                st.error("Please enter a valid 12-digit Aadhaar number.")

    elif st.session_state.step == 'process_aadhaar':

        print("Setting up driver... starting the captcha process and then will start ahead :) ")
        if not setup_driver():
            return

        try:
            print("Driver setup complete, proceeding with Aadhaar download...")
            # Select Aadhaar option
            

            # Enter Aadhaar number
            aadhaar_input = WebDriverWait(st.session_state.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[1]/div/div/div/input"))
            )
            aadhaar_input.send_keys(st.session_state.aadhaar_number)

            # Capture CAPTCHA
            captcha_img = WebDriverWait(st.session_state.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[2]/div[2]/img"))
            )
            captcha_bytes = captcha_img.screenshot_as_png
            captcha_text = get_captcha_text(captcha_bytes)

            if captcha_text:
                # Enter CAPTCHA
                captcha_input = WebDriverWait(st.session_state.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[2]/div[1]/div/div/div/input"))
                )
                captcha_input.send_keys(captcha_text)

                # Send OTP
                btn = WebDriverWait(st.session_state.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[3]/div/button"))
                )
                btn.click()
                btn.click()  # Click twice to ensure OTP is sent

                st.session_state.step = 'input_otp'
                st.rerun()
            else:
                st.error("Failed to solve CAPTCHA. Please try again.")
                st.session_state.step = 'input_aadhaar'
                st.rerun()

        except Exception as e:
            st.error(f"Error processing Aadhaar: {str(e)}")
            st.session_state.step = 'input_aadhaar'
            st.rerun()

    elif st.session_state.step == 'input_otp':
        otp = st.text_input("Enter 6-digit OTP:", max_chars=6, key="otp_input")
        
        if st.button("Submit OTP"):
            if len(otp) == 6 and otp.isdigit():
                st.session_state.otp = otp
                try:
                    # Enter OTP
                    otp_input = WebDriverWait(st.session_state.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[5]/div[1]/div[1]/div/input"))
                    )
                    otp_input.send_keys(otp)

                    # Submit to download
                    WebDriverWait(st.session_state.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div/form/div[3]/div[6]/div/button"))
                    ).click()

                    # Wait for download success
                    try:
                        WebDriverWait(st.session_state.driver, 60).until(
                            EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[3]/div/div/span[2]"))
                        )
                        st.success("✅ Aadhaar download triggered successfully. Check your downloads folder.")
                        st.session_state.step = 'complete'
                    except:
                        st.error("⚠️ Timeout: Download success message not found.")
                        st.session_state.step = 'input_aadhaar'
                    st.rerun()

                except Exception as e:
                    st.error(f"Error during OTP submission: {str(e)}")
                    st.session_state.step = 'input_aadhaar'
                    st.rerun()
            else:
                st.error("Please enter a valid 6-digit OTP.")

    if st.session_state.step == 'complete':
        download_dir = os.path.join(os.getcwd(), "downloads")
        pdf_files = glob.glob(os.path.join(download_dir, "*.pdf"))
        if pdf_files:
            with open(pdf_files[0], "rb") as f:
                st.download_button(
                    label="Download Aadhaar Card",
                    data=f,
                    file_name="Aadhaar_Card.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("No PDF file found in downloads.")
        if st.button("Close"):
            # Clean up
            for file in pdf_files:
                os.remove(file)
            if st.session_state.driver:
                st.session_state.driver.quit()
                st.session_state.driver = None
            st.session_state.step = 'input_aadhaar'
            st.session_state.aadhaar_number = ''
            st.session_state.otp = ''
            st.success("✅ Session closed. Start a new download if needed.")
            st.rerun()

if __name__ == "__main__":
    main()
