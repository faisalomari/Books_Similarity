import requests
from bs4 import BeautifulSoup
import concurrent.futures

def extract_page_content(url, page_number):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # If the request fails (e.g., 404 error), return None
    if response.status_code != 200:
        print(f"Error or end page reached at page {page_number}.")
        return None
    
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the content (you can adjust this to match the page structure)
    content = soup.find('div', class_='nass margin-top-10')
    
    if content:
        print(f"Processing page {page_number}...")  # Optionally, process the content here
        # Return the content for further processing
        return content.get_text(strip=True)
    else:
        print(f"No content found on page {page_number}.")
        return None

def extract_book_pages(base_url, start_page=1, max_pages=100):
    processed_pages = 0  # Initialize the counter for processed pages
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit each page to be fetched in parallel
        future_to_page = {executor.submit(extract_page_content, f"{base_url}/{page}", page): page for page in range(start_page, start_page + max_pages)}

        # Process each page's content when it's fetched
        for future in concurrent.futures.as_completed(future_to_page):
            page_number = future_to_page[future]
            try:
                content = future.result()
                if content:
                    # If the page was processed successfully, increment the counter
                    processed_pages += 1
                    print(f"Page {page_number} processed.")
                else:
                    # If no content, stop the loop
                    print(f"Stopping processing at page {page_number} due to no content.")
                    break
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
                break  # Stop processing if there is an error

    print(f"Total pages processed: {processed_pages}")

# Example usage
base_url = 'https://shamela.ws/book/9472'  # Replace with the base URL of the book
extract_book_pages(base_url, start_page=1, max_pages=5000)
