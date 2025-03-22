import os
import sys
import csv
import re
import mimetypes
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time

# --- Link Generation Functions ---
def generate_links(html_content, judge_left="Judge 1", judge_right="Judge 2", 
                  txt_output="original_links.txt", csv_output="links_data.csv", 
                  no_sub_output="no_submissions.txt"):
    start_time = time.time()
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find('table', class_='waffle').find('tbody').find_all('tr')
    except AttributeError as e:
        print(f"Error parsing HTML: {str(e)}")
        return [], [], [], []

    data_rows = rows[4:]
    left_links = {}
    right_links = {}
    csv_data = []
    no_submissions = []
    
    for row in data_rows:
        try:
            cells = row.find_all('td')
            if len(cells) < 22:
                continue
                
            if cells[0].text.strip():
                result = process_schedule(cells[:11], cells[9:11], judge_left)
                if isinstance(result, tuple) and len(result) == 6:
                    number, student, link, equipment, classification, judge = result
                    if link.startswith("http"):
                        if equipment not in left_links:
                            left_links[equipment] = []
                        left_links[equipment].append((student, link))
                        csv_data.append((judge, number, equipment, student, classification, link))
                    elif student.strip():
                        no_submissions.append((judge, number, equipment, student, classification, link))
                    
            if cells[12].text.strip():
                result = process_schedule(cells[12:23], cells[21:23], judge_right)
                if isinstance(result, tuple) and len(result) == 6:
                    number, student, link, equipment, classification, judge = result
                    if link.startswith("http"):
                        if equipment not in right_links:
                            right_links[equipment] = []
                        right_links[equipment].append((student, link))
                        csv_data.append((judge, number, equipment, student, classification, link))
                    elif student.strip():
                        no_submissions.append((judge, number, equipment, student, classification, link))
                    
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue
    
    with open(txt_output, 'w', encoding='utf-8') as f:
        f.write(f"=== {judge_left} ===\n\n")
        for equip in sorted(left_links.keys()):
            if left_links[equip]:
                f.write(f"{equip}:\n")
                for student, link in left_links[equip]:
                    f.write(f"  {student}: {link}\n")
                f.write("\n")
            
        f.write(f"=== {judge_right} ===\n\n")
        for equip in sorted(right_links.keys()):
            if right_links[equip]:
                f.write(f"{equip}:\n")
                for student, link in right_links[equip]:
                    f.write(f"  {student}: {link}\n")
                f.write("\n")
    print(f"Generated original links saved to {txt_output}")
    
    csv_data.sort(key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf')))
    with open(csv_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Judge', 'Number', 'Equipment', 'Student', 'Classification', 'Music Link'])
        for row in csv_data:
            writer.writerow(row)
    print(f"Generated CSV data saved to {csv_output}")
    
    with open(no_sub_output, 'w', encoding='utf-8') as f:
        if no_submissions:
            f.write("Students with No Submissions:\n\n")
            for judge, number, equipment, student, classification, reason in sorted(no_submissions, key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf'))):
                f.write(f"Judge: {judge}, Number: {number}, Equipment: {equipment}, Student: {student}, Classification: {classification}, Reason: {reason}\n")
        else:
            f.write("No students with missing submissions found.\n")
    print(f"Generated no submissions list saved to {no_sub_output}")
    
    end_time = time.time()
    print(f"Link generation completed in {end_time - start_time:.2f} seconds")
    return csv_data

def process_schedule(cells, link_cells, judge):
    try:
        number = cells[0].text.strip()
        equipment = cells[1].text.strip()
        classification = cells[2].text.strip()
        student = cells[4].text.strip()
        
        audio_link_cell = link_cells[1]
        link_text = audio_link_cell.text.strip()
        
        if link_text.lower() == "not submitted":
            return (number, student, "No valid link found", equipment, classification, judge)
        
        audio_link = audio_link_cell.find('a')
        if not audio_link or 'drive.google.com' not in audio_link['href']:
            return (number, student, "No valid link found", equipment, classification, judge)
            
        original_url = extract_original_url(audio_link['href'])
        return (number, student, original_url, equipment, classification, judge)
    except Exception:
        return (number, student, "Processing error", equipment, classification, judge)

def extract_original_url(redirect_url):
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

# --- Download Functions ---
def guess_extension(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mimetypes.guess_extension(mime_type) or '.mp3' if mime_type else '.mp3'

def download_file(url, output_path, session, max_attempts=2):
    file_id = re.search(r'/d/([\w-]+)/', url)
    if not file_id:
        print(f"Error: Could not extract file ID from {url}")
        return None
    
    download_url = f"https://drive.google.com/uc?export=download&id={file_id.group(1)}"
    
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts} for {output_path}")
            response = session.get(download_url, stream=True, timeout=10)
            response.raise_for_status()
            
            temp_path = output_path + ".tmp"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            extension = guess_extension(temp_path)
            final_path = f"{output_path}{extension}"
            os.rename(temp_path, final_path)
            return final_path
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_attempts - 1:
                return None
            time.sleep(1)

def download_batch(args):
    url, output_path, session = args
    result = download_file(url, output_path, session)
    return result if result else f"Failed: {output_path}"

def download_files(csv_data, judge_left, judge_right, max_workers=12):
    tasks = []
    for judge, number, equipment, student, classification, music_link in csv_data:
        if judge not in [judge_left, judge_right]:
            continue
        
        student_clean = re.sub(r'[^\w\s-]', '', student).strip().replace(' ', '_')
        equipment_clean = re.sub(r'[^\w\s-]', '', equipment).strip().replace(' ', '_')
        classification_clean = re.sub(r'[^\w\s-]', '', classification).strip().replace(' ', '_')
        
        base_filename = f"{number}-{student_clean}-{equipment_clean}-{classification_clean}"
        judge_dir = judge.replace(" ", "_")
        os.makedirs(judge_dir, exist_ok=True)
        output_path = os.path.join(judge_dir, base_filename)
        
        if music_link.startswith("http"):
            tasks.append((music_link, output_path))
    
    with requests.Session() as session:
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(download_batch, (url, path, session)): path for url, path in tasks}
            for future in as_completed(future_to_file):
                result = future.result()
                if result.startswith("Failed"):
                    print(result)
                else:
                    print(f"Success: Downloaded to {result}")
        
        end_time = time.time()
        print(f"Download completed in {end_time - start_time:.2f} seconds")

# --- Main Execution ---
def main():
    if len(sys.argv) < 3:
        print("Usage: python combined_script.py \"Judge Name 1\" \"Judge Name 2\"")
        return
    
    judge_left = sys.argv[1]
    judge_right = sys.argv[2]
    
    try:
        with open('document.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Please save the HTML content as 'document.html' in the same directory")
        return
    
    # Step 1: Generate links and CSV data
    csv_data = generate_links(html_content, judge_left, judge_right)
    
    # Step 2: Download files using the generated data
    if csv_data:
        download_files(csv_data, judge_left, judge_right)

if __name__ == "__main__":
    main()