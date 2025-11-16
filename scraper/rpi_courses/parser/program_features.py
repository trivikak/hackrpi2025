import re
from bs4 import BeautifulSoup, NavigableString, Tag
from rpi_courses.utils import safeInt, find_course_codes

def parse_program_content(catalog, soup):
    """
    Core parsing logic for a single program page (preview_program.php).
    Extracts program name, total credits, and structured list of requirements.
    This logic specifically targets the typical catalog layout shown in the user's snippet.
    """
    program_data = {}
    program_details = []
    
    # Extract Program Name
    program_name_tag = soup.find('h1', id='program_name') or soup.find('h1')
    
    if program_name_tag:
        full_name = program_name_tag.text.strip()
        
        # Clean up the name (e.g., remove ' - Catalog Year 202X-202Y')
        if " - " in full_name:
            full_name = full_name.split(' - ')[0].strip()
        
        program_data['name'] = full_name
        
        # Extract Total Credits
        total_credits = 0
        # Strategy A: Try to extract credits from the structured table cell next to "Total Credit Hours"
        credit_tag = soup.find('td', class_='width-25', string=lambda t: t and 'Total Credit Hours' in t)
        if credit_tag and credit_tag.find_next_sibling('td', class_='width-25'):
            credits_text = credit_tag.find_next_sibling('td', class_='width-25').text
            match = re.search(r'(\d+)\.?\d*', credits_text)
            total_credits = safeInt(match.group(1)) if match else 0
        else:
            # Strategy B: Fallback, search for a general credit match
            credit_hours_match = re.search(r'(\d+)\s+Total Credit Hours', soup.get_text())
            total_credits = safeInt(credit_hours_match.group(1)) if credit_hours_match else 0
            
        program_data['credit_hours'] = total_credits
            
    # Extract Requirement Blocks
    content_div = soup.find('div', id='program_descriptions')
    
    if content_div:
        # Target headers (h3, h4) and content containers (p, ul, ol, table)
        elements = content_div.find_all(['h3', 'h4', 'p', 'ul', 'ol', 'div', 'table'])
        
        current_header = "Program Overview"
        current_text_block = []
        
        for elem in elements:
            
            # Special handling for tables (often curriculum grids or minors)
            if elem.name == 'table':
                # Treat the whole table content as a single block
                table_text = elem.get_text(separator=' ', strip=True)
                if table_text and len(table_text) > 10:
                    program_details.append(extract_detail(current_header + " (Table Data)", table_text))
                    current_text_block = [] # Reset text block after processing table
                continue

            text = elem.get_text(separator=' ', strip=True)
            
            # Check for section headings (h3 or h4)
            if elem.name in ('h3', 'h4'):
                if current_text_block:
                    program_details.append(extract_detail(current_header, ' '.join(current_text_block)))
                    current_text_block = []
                current_header = text
                
            elif text:
                # Accumulate non-heading text, including text from lists (ul/ol/li)
                current_text_block.append(text)
                
        # Finalize the last section
        if current_text_block:
            program_details.append(extract_detail(current_header, ' '.join(current_text_block)))

    
    if not program_data.get('name'):
         program_data['name'] = soup.title.text.replace(' - Undergraduate Catalog', '').strip() if soup.title else "Unknown Program"
         
    # Add details to the final data structure
    program_data['details'] = [d for d in program_details if d]

    # Assign this program data to the catalog object using its name as the key
    catalog.programs[program_data['name']] = program_data
    

def extract_detail(header, text, elective_flag=False):
    """
    Helper function to process a single logical requirement block.
    """
    
    # Find courses and estimate credits from the text
    courses_data = find_course_data(text)
    
    # Check for elective status explicitly or via key phrases
    if not elective_flag and any(phrase in text.lower() for phrase in ['free elective', 'h&ss elective', 'humanities elective', 'technical elective', 'free elect.', 'h&ss elect.', 'h/ss elect.', 'restricted elective']):
        elective_flag = True
    
    # Estimate total credits for this block (improved logic)
    credits = 0
    # Look for a specific credit count in the text like '12 credits'
    credits_match = re.search(r'(\d+)\s+(?:credit|elect)', text)
    if credits_match:
        credits = safeInt(credits_match.group(1))
    elif courses_data:
        # Sum of individual course credits (using the heuristic if detail not found)
        credits = sum(c['credits'] for c in courses_data) 
    else:
        # Try to find common phrasing for credit blocks (e.g., "16 credit hours" at the start)
        credits_block_match = re.search(r'^(\d+)\s+(credit|hour)', text)
        credits = safeInt(credits_block_match.group(1)) if credits_block_match else 0
        

    return {
        "header": header,
        "text": text,
        "credits": credits,
        "courses": courses_data,
        "is_elective_section": elective_flag
    }

def find_course_data(text):
    """
    Helper function to extract course codes and attempt to infer credits.
    """
    # Uses the shared regex function from utils.py
    course_codes = find_course_codes(text)
    
    course_data = []
    
    for code in course_codes:
        # Try to find specific credit reference immediately following the code.
        # Pattern: CODE ... Credit Hours: N or CODE (N credits)
        # Regex explanation: Non-greedy match, then capture digits after common phrases/punctuation
        credit_match = re.search(rf'{re.escape(code)}.*?\s*(?:Credit\s*Hours:\s*|credits:\s*|:)\s*(\d+)', text, re.IGNORECASE | re.DOTALL)
        
        # Default to the most common credit value (4 for Rensselaer) if not found.
        # Use try/except on the group if the pattern failed entirely or captured None
        credits = safeInt(credit_match.group(1)) if credit_match and credit_match.group(1) else 4 
        
        course_data.append({"code": code, "credits": credits})
        
    # Remove duplicates from the list of dicts based on the 'code' key
    seen = set()
    unique_data = []
    for d in course_data:
        if d['code'] not in seen:
            seen.add(d['code'])
            unique_data.append(d)
            
    return unique_data
    
# Export the feature function
program_details_feature = parse_program_content