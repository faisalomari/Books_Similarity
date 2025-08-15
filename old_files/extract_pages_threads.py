import requests
from bs4 import BeautifulSoup
import concurrent.futures

def extract_text_from_shamela_page(url, page_num):
    # Send a GET request to the URL
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve the page {page_num}.")
        return None

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the content of the book from the specific HTML element
    content = soup.find('div', class_='nass margin-top-10')

    if not content:
        print(f"Failed to find content on page {page_num}.")
        return None
    
    # Extract the paragraphs and inline footnotes
    paragraphs = content.find_all('p')
    text_content = ""
    footnotes = []  # Store footnotes to be added later

    for p in paragraphs:
        # Check if the paragraph is a footnote (hamesh)
        if 'hamesh' in p.get('class', []):
            # If it's a footnote, extract the content and store it separately
            footnote_text = p.get_text(separator="\n", strip=True)  # Add new line between <br> elements
            footnotes.append(footnote_text)
            continue  # Skip this paragraph for the main content

        # Clean out unnecessary elements like references (e.g., <a> tags)
        for unwanted_tag in p.find_all(['a']):
            unwanted_tag.decompose()

        # Extract inline footnote numbers (e.g., <span class="c2">(١)</span>)
        footnote_numbers = p.find_all('span', class_='c2')

        # Add the paragraph content while keeping footnote numbers inline with the text
        paragraph_text = p.get_text(strip=True)
        for fn in footnote_numbers:
            footnote_number = fn.get_text(strip=True)
            # Keep the footnote number inline with the text
            paragraph_text = paragraph_text.replace(f"({footnote_number})", f" ({footnote_number})")
        
        text_content += paragraph_text + "\n\n"

    # If we found footnotes, add them at the end of the content as "حاشية"
    if footnotes:
        text_content += "\n\n(حاشية)\n"
        for footnote in footnotes:
            text_content += footnote + "\n"

    return text_content

def save_text_to_file(text, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

def extract_and_save_page(book_url, page_num):
    page_url = f"{book_url}/{page_num}#p{page_num}"
    print(f"Extracting page {page_num}...")
    text = extract_text_from_shamela_page(page_url, page_num)

    if text:
        # Save the extracted text to a file
        save_text_to_file(text, f"book/book_page_{page_num}.txt")
        print(f"Text saved to book/book_page_{page_num}.txt")
    else:
        print(f"Failed to extract text from page {page_num}")

def extract_and_save_multiple_pages(book_url, total_pages):
    # Use ThreadPoolExecutor to handle concurrent page fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        # Submit each page to be fetched in parallel
        future_to_page = {executor.submit(extract_and_save_page, book_url, page): page for page in range(1, total_pages + 1)}

        # Wait for the futures to complete and handle any exceptions
        for future in concurrent.futures.as_completed(future_to_page):
            page_number = future_to_page[future]
            try:
                future.result()  # Ensure we capture any exception raised
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")

if __name__ == "__main__":
    # The base URL for the book (table of contents)
    base_url = "https://shamela.ws/book/482"

    # Extract and save content from the first 1707 pages of the book
    extract_and_save_multiple_pages(base_url, 930)
