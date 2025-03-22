from bs4 import BeautifulSoup
import re
import os
import csv
from urllib.parse import unquote

def generate_links(html_content, txt_output="original_links.txt", csv_output="links_data.csv"):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find('table', class_='waffle').find('tbody').find_all('tr')
    except AttributeError as e:
        print(f"Error parsing HTML: {str(e)}")
        return [], [], []

    data_rows = rows[4:]
    
    santos_links = {'Mace': [], 'Military': []}
    gerolaga_links = {'Military': [], 'Conducting': []}
    csv_data = []
    problematic_performers = []
    
    for row in data_rows:
        try:
            cells = row.find_all('td')
            if len(cells) < 22:
                continue
                
            # Left schedule (Rod Santos)
            if cells[0].text.strip():
                result = process_schedule(cells[:11], cells[9:11], "Rod Santos")
                if isinstance(result, tuple) and len(result) == 5:  # (number, student, link, equipment, judge)
                    number, student, link, equipment, judge = result
                    if link.startswith("http"):
                        if equipment in santos_links:
                            santos_links[equipment].append((student, link))
                            csv_data.append((number, equipment, student, link, judge))
                        else:
                            problematic_performers.append((student, f"Unknown equipment type: {equipment}"))
                    else:
                        problematic_performers.append((student, link))
                    
            # Right schedule (Erik Gerolaga)
            if cells[12].text.strip():
                result = process_schedule(cells[12:23], cells[21:23], "Erik Gerolaga")
                if isinstance(result, tuple) and len(result) == 5:
                    number, student, link, equipment, judge = result
                    if link.startswith("http"):
                        if equipment in gerolaga_links:
                            gerolaga_links[equipment].append((student, link))
                            csv_data.append((number, equipment, student, link, judge))
                        else:
                            problematic_performers.append((student, f"Unknown equipment type: {equipment}"))
                    else:
                        problematic_performers.append((student, link))
                    
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue
    
    # Write text file
    try:
        with open(txt_output, 'w', encoding='utf-8') as f:
            f.write("=== Rod Santos (Stadium) ===\n\n")
            for equip in ['Mace', 'Military']:
                if santos_links[equip]:
                    f.write(f"{equip}:\n")
                    for student, link in santos_links[equip]:
                        f.write(f"  {student}: {link}\n")
                    f.write("\n")
            
            f.write("=== Erik Gerolaga (Stadium and Library) ===\n\n")
            for equip in ['Military', 'Conducting']:
                if gerolaga_links[equip]:
                    f.write(f"{equip}:\n")
                    for student, link in gerolaga_links[equip]:
                        f.write(f"  {student}: {link}\n")
                    f.write("\n")
        print(f"Generated original links saved to {txt_output}")
    except Exception as e:
        print(f"Error writing text file: {str(e)}")
    
    # Write CSV file
    try:
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Number', 'Equipment', 'Student', 'Music Link', 'Judge'])
            for row in csv_data:
                writer.writerow(row)
        print(f"Generated CSV data saved to {csv_output}")
    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
    
    if problematic_performers:
        print("\nPerformers with issues:")
        for performer, error in problematic_performers:
            print(f"- {performer}: {error}")
    
    return santos_links, gerolaga_links, csv_data

def process_schedule(cells, link_cells, judge):
    try:
        number = cells[0].text.strip()
        equipment = cells[1].text.strip()
        student = cells[4].text.strip()
        
        audio_link_cell = link_cells[1]
        audio_link = audio_link_cell.find('a')
        
        if not audio_link or 'drive.google.com' not in audio_link['href'] or 'Not Submitted' in audio_link_cell.text:
            return (student, "No valid link found")
            
        original_url = extract_original_url(audio_link['href'])
        return (number, student, original_url, equipment, judge)
        
    except Exception as e:
        return (student, f"Processing error: {str(e)}")

def extract_original_url(redirect_url):
    try:
        pattern = r'q=(https?://[^\s&]+)'
        match = re.search(pattern, redirect_url)
        if match:
            encoded_url = match.group(1)
            decoded_url = unquote(encoded_url)
        else:
            decoded_url = redirect_url
        
        pattern = r'id=([\w-]+)'
        match = re.search(pattern, decoded_url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/view"
        
        pattern = r'/d/([\w-]+)/'
        match = re.search(pattern, decoded_url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/view"
            
        return decoded_url
        
    except Exception as e:
        raise Exception(f"URL extraction error: {str(e)}")

def main():
    try:
        with open('document.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Please save the HTML content as 'document.html' in the same directory")
        return
    except Exception as e:
        print(f"Error reading HTML file: {str(e)}")
        return
    
    santos_links, gerolaga_links, csv_data = generate_links(html_content)
    
    print("\n=== Rod Santos (Stadium) ===")
    for equip in ['Mace', 'Military']:
        if santos_links[equip]:
            print(f"\n{equip}:")
            for student, link in santos_links[equip]:
                print(f"  {student}: {link}")
                
    print("\n=== Erik Gerolaga (Stadium and Library) ===")
    for equip in ['Military', 'Conducting']:
        if gerolaga_links[equip]:
            print(f"\n{equip}:")
            for student, link in gerolaga_links[equip]:
                print(f"  {student}: {link}")

if __name__ == "__main__":
    main()