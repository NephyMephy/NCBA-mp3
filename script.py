from bs4 import BeautifulSoup
import re
import os
import csv
from urllib.parse import unquote
import sys
import time

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
                
            # Left schedule (first judge)
            if cells[0].text.strip():
                result = process_schedule(cells[:11], cells[9:11], judge_left)
                if isinstance(result, tuple) and len(result) == 6:  # Now 6 elements with classification
                    number, student, link, equipment, classification, judge = result
                    if link.startswith("http"):
                        if equipment not in left_links:
                            left_links[equipment] = []
                        left_links[equipment].append((student, link))
                        csv_data.append((judge, number, equipment, student, classification, link))
                    elif student.strip():  # Only add to no_submissions if student name is non-empty
                        no_submissions.append((judge, number, equipment, student, classification, link))
                    
            # Right schedule (second judge)
            if cells[12].text.strip():
                result = process_schedule(cells[12:23], cells[21:23], judge_right)
                if isinstance(result, tuple) and len(result) == 6:
                    number, student, link, equipment, classification, judge = result
                    if link.startswith("http"):
                        if equipment not in right_links:
                            right_links[equipment] = []
                        right_links[equipment].append((student, link))
                        csv_data.append((judge, number, equipment, student, classification, link))
                    elif student.strip():  # Only add to no_submissions if student name is non-empty
                        no_submissions.append((judge, number, equipment, student, classification, link))
                    
        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue
    
    # Write text file
    try:
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
    except Exception as e:
        print(f"Error writing text file: {str(e)}")
    
    # Sort CSV data by Judge then Number
    csv_data.sort(key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf')))
    
    # Write CSV file with new columns
    try:
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Judge', 'Number', 'Equipment', 'Student', 'Classification', 'Music Link'])
            for row in csv_data:
                writer.writerow(row)
        print(f"Generated CSV data saved to {csv_output}")
    except Exception as e:
        print(f"Error writing CSV file: {str(e)}")
    
    # Write no submissions file
    try:
        with open(no_sub_output, 'w', encoding='utf-8') as f:
            if no_submissions:
                f.write("Students with No Submissions:\n\n")
                for judge, number, equipment, student, classification, reason in sorted(no_submissions, key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf'))):
                    f.write(f"Judge: {judge}, Number: {number}, Equipment: {equipment}, Student: {student}, Classification: {classification}, Reason: {reason}\n")
            else:
                f.write("No students with missing submissions found.\n")
        print(f"Generated no submissions list saved to {no_sub_output}")
    except Exception as e:
        print(f"Error writing no submissions file: {str(e)}")
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    total_performers = len(csv_data) + len(no_submissions)
    judge_left_count = sum(1 for row in csv_data if row[0] == judge_left)
    judge_right_count = sum(1 for row in csv_data if row[0] == judge_right)
    no_sub_count = len(no_submissions)
    
    print(f"\nProcessing completed in {processing_time:.2f} seconds")
    print(f"Total performers: {total_performers}")
    print(f"Performers for {judge_left}: {judge_left_count}")
    print(f"Performers for {judge_right}: {judge_right_count}")
    print(f"Performers with no submissions: {no_sub_count}")
    
    return left_links, right_links, csv_data, no_submissions

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
        
    except Exception as e:
        return (number, student, f"Processing error: {str(e)}", equipment, classification, judge)

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
    if len(sys.argv) < 3:
        print("Error: Please provide two judge names as arguments")
        print("Usage: python script.py \"Judge Name 1\" \"Judge Name 2\"")
        print("Using default names 'Judge 1' and 'Judge 2'")
        judge_left = "Judge 1"
        judge_right = "Judge 2"
    else:
        judge_left = sys.argv[1]
        judge_right = sys.argv[2]
    
    try:
        with open('document.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Please save the HTML content as 'document.html' in the same directory")
        return
    except Exception as e:
        print(f"Error reading HTML file: {str(e)}")
        return
    
    left_links, right_links, csv_data, no_submissions = generate_links(html_content, judge_left, judge_right)

if __name__ == "__main__":
    main()