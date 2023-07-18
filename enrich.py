import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

#Get last contacts
def fetch_contacts_with_filters_and_sorting(api_key, filters, sort_by):
    url = 'https://api.overloop.com/public/v1/contacts'
    headers = {
        'Authorization': f'{api_key}',
        'Accept': 'application/vnd.api+json'
    }
    params = {
        'filter': ','.join(filters),
        'sort': sort_by
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception if response status is not 2xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

#Get a contact from ID
def get_contact_from_id(api_key, contact_id):
    url = f'https://api.overloop.com/public/v1/contacts/{contact_id}'
    headers = {
        'Authorization': f'{api_key}',
        'Accept': 'application/vnd.api+json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if response status is not 2xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

#Upate organization
def update_organization_website(api_key, organization_id, attributes):
    url = f'https://api.overloop.com/public/v1/organizations/{organization_id}'
    headers = {
        'Authorization': f'{api_key}',
        'Content-Type': 'application/vnd.api+json',
    }
    data = {
        'data': {
            'id': organization_id,
            'type': 'organization',
            'attributes': attributes
        }
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

#Extract website from email
def extract_website_from_email(email):
    try:
        _, domain = email.split('@')
        website = domain.split('.', 1)[-1]  # To handle subdomains like 'www.google.com'
        return domain
    except ValueError:
        return None

def get_linkedin_url(company_website):
    # Step 1: Scrape the company website for LinkedIn URL
    linkedin_url = scrape_linkedin_from_website(company_website)

    # Step 2 : find other ways (BING API?) to find LinkedIn url

    
    return linkedin_url

# Try to find if the LinkedIn URL is visible on the company page and return it
def scrape_linkedin_from_website(company_website):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        # Send a GET request to the company's website
        response = requests.get(company_website, headers=headers)
        response.raise_for_status()

        # Parse the HTML content of the website
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the LinkedIn URL in the HTML (assuming it is in the <a> tag with 'linkedin.com' in the href)
        linkedin_url = None
        for link in soup.find_all('a', href=True):
            if "linkedin.com" in link['href']:
                linkedin_url = link['href']
                break

        return linkedin_url

    except requests.exceptions.RequestException as e:
        print("Error: Unable to fetch the website.")
        return None
    except Exception as e:
        print("Error: Unable to parse the website's HTML.")
        return None

def scrape_linkedin_with_selenium(company_website):
    try:
        # Set up Chrome options to run in headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        # Initialize the Selenium Chrome driver
        driver = webdriver.Chrome(options=chrome_options)

        # Load the website
        driver.get(company_website)

        # Get the page source after rendering
        page_source = driver.page_source

        # Parse the HTML content of the website
        soup = BeautifulSoup(page_source, "html.parser")

        # Find the LinkedIn URL in the HTML (assuming it is in the <a> tag with 'linkedin.com' in the href)
        linkedin_url = None
        for link in soup.find_all('a', href=True):
            if "linkedin.com" in link['href']:
                linkedin_url = link['href']
                break

        driver.quit()  # Close the browser
        return linkedin_url

    except Exception as e:
        print("Error: Unable to fetch the website using Selenium.")
        return None

if __name__ == "__main__":

    #Demo account API Key:
    api_key = os.environ['OVERLOOP_API_KEY']

    #1 Extract Last Created Contacts that has not been updated
    filters = ["c_enriched:true"]
    sorting = "-created_at"

    
    while True:

        #1 Extract Last Created Contacts that has not been updated
        contacts = fetch_contacts_with_filters_and_sorting(api_key, filters, sorting)
    
        #2 For each contact, extract company website from email
        if contacts:
            for contact in contacts['data']:
                email = contact['attributes'].get('email', 'N/A')
                print(email)
                organization_id = contact['relationships']['organization']['data']['id']
                print(organization_id)
                company_website = "http://" + extract_website_from_email(email)
                print(company_website)
                
        #3 Extract Company LinkedIn's URL profil if possible (c_linkedin_url):
                c_linkedin_url = scrape_linkedin_with_selenium(company_website)
                if c_linkedin_url:
                    print(f"The LinkedIn URL for the company is: {c_linkedin_url}")
                else:
                    print("LinkedIn URL not found.")

        #4 Update Company Website and LinkedIn URL:
                attributes = {
                    'website': company_website,
                    'c_linkedin_url': c_linkedin_url
                }
                update_organization_website(api_key, organization_id, attributes)


        #WIP:
        # Update contact to mark is as 'Enriched'

        #Print Enriched contact
                first_name = contact['attributes'].get('first_name', 'N/A')
                last_name = contact['attributes'].get('last_name', 'N/A')
                print(f"First Name: {first_name}, Last Name: {last_name}")
        else:
            print("Failed to fetch contacts with filters and sorting.")
        
