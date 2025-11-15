import requests
from bs4 import BeautifulSoup

def scrape_rpi_degrees(url):
    """
    Scrapes degree information (Name, Type, HEGIS Code) from the RPI catalog page.

    Args:
        url (str): The URL of the RPI Degrees Offered page.

    Returns:
        list: A list of dictionaries, where each dictionary represents a degree 
              program and includes 'name', 'degree_type', and 'hegis_code'.
    """
    
    # 1. Fetch the HTML content
    try:
        response = requests.get(url)
        response.raise_for_status() 
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []

    # 2. Parse the HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    degree_list = []
    current_school = None
    
    # --- CHANGE 1: Find all tables directly ---
    tables = soup.find_all('table')
    
    # We will process tables that appear large enough to contain degrees
    for table in tables:
        rows = table.find_all('tr')
        
        # Filter tables that are too small (e.g., footers, menus)
        if len(rows) < 5:
            continue
            
        # 3. Process each row in the potential degree table
        for row in rows:
            cols = row.find_all('td')
            
            # Check for School Header: A row with one column.
            if len(cols) == 1:
                # Look for bold or large text, as headers often use H3/H2 or <b>
                header_text = cols[0].get_text(strip=True)
                # Ensure the header text isn't just an empty string or a separator
                if header_text and len(header_text) > 5: 
                    current_school = header_text
                continue
            
            # --- CHANGE 2: Check for valid data rows (must have 3 columns) ---
            if len(cols) == 3: 
                program_name = cols[0].get_text(strip=True)
                degree_types_str = cols[1].get_text(strip=True)
                hegis_code = cols[2].get_text(strip=True)
                
                # Skip rows that are empty or clearly headers
                if not program_name or not degree_types_str or hegis_code in ['HEGIS Code', 'Code']:
                    continue
                    
                # Split degree types (e.g., "B.S., M.S.")
                degree_types = [t.strip() for t in degree_types_str.split(',') if t.strip()]
                
                # 4. Create an entry for each unique degree offering
                for degree_type in degree_types:
                    degree_entry = {
                        'school': current_school, 
                        'name': program_name,
                        'degree_type': degree_type,
                        'hegis_code': hegis_code
                    }
                    degree_list.append(degree_entry)

    return degree_list

# --- Main Execution ---
url_to_scrape = 'https://catalog.rpi.edu/content.php?catoid=33&navoid=866'
degrees_data = scrape_rpi_degrees(url_to_scrape)

if degrees_data:
    print(f"Successfully scraped {len(degrees_data)} degree offerings.")
    print("\n--- Example Output (First 5 Entries) ---")
    
    # Print the first 5 entries for a preview
    for i, entry in enumerate(degrees_data[:5]):
        print(f"Entry {i+1}:")
        for key, value in entry.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("-" * 20)
    
    print("\n--- Full Data Structure Sample ---")
    print(degrees_data[:1]) 
else:
    print("Failed to scrape any degree data.")