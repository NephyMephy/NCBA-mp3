import os
import sys
import csv
import re
import mimetypes
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from threading import Thread

# --- Link Generation Functions ---
def generate_links(csv_data, judge_left, judge_right, output_dir, 
                  txt_output="original_links.txt", csv_output="links_data.csv", 
                  no_sub_output="no_submissions.txt", console=None):
    start_time = time.time()
    
    txt_output = os.path.join(output_dir, txt_output)
    csv_output = os.path.join(output_dir, csv_output)
    no_sub_output = os.path.join(output_dir, no_sub_output)
    
    left_links = {}
    right_links = {}
    output_csv_data = []
    no_submissions = []
    
    for row in csv_data[4:]:
        if len(row) >= 12 and row[0].strip():
            result = process_schedule(row[:12], judge_left)
            if isinstance(result, tuple) and len(result) == 6:
                number, student, link, equipment, classification, judge = result
                if link.startswith("http"):
                    if equipment not in left_links:
                        left_links[equipment] = []
                    left_links[equipment].append((student, link))
                    output_csv_data.append((judge, number, equipment, student, classification, link))
                elif student.strip():
                    no_submissions.append((judge, number, equipment, student, classification, link))
        
        if len(row) >= 24 and row[13].strip():
            result = process_schedule(row[13:], judge_right)
            if isinstance(result, tuple) and len(result) == 6:
                number, student, link, equipment, classification, judge = result
                if link.startswith("http"):
                    if equipment not in right_links:
                        right_links[equipment] = []
                    right_links[equipment].append((student, link))
                    output_csv_data.append((judge, number, equipment, student, classification, link))
                elif student.strip():
                    no_submissions.append((judge, number, equipment, student, classification, link))
    
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
    if console: console.insert(tk.END, f"Generated original links saved to {txt_output}\n")
    
    output_csv_data.sort(key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf')))
    with open(csv_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Judge', 'Number', 'Equipment', 'Student', 'Classification', 'Music Link'])
        for row in output_csv_data:
            writer.writerow(row)
    if console: console.insert(tk.END, f"Generated CSV data saved to {csv_output}\n")
    
    with open(no_sub_output, 'w', encoding='utf-8') as f:
        if no_submissions:
            f.write("Students with No Submissions:\n\n")
            for judge, number, equipment, student, classification, reason in sorted(no_submissions, key=lambda x: (x[0], int(x[1]) if x[1].isdigit() else float('inf'))):
                f.write(f"Judge: {judge}, Number: {number}, Equipment: {equipment}, Student: {student}, Classification: {classification}, Reason: {reason}\n")
        else:
            f.write("No students with missing submissions found.\n")
    if console: console.insert(tk.END, f"Generated no submissions list saved to {no_sub_output}\n")
    
    end_time = time.time()
    if console: console.insert(tk.END, f"Link generation completed in {end_time - start_time:.2f} seconds\n")
    return output_csv_data

def process_schedule(row, judge):
    try:
        number = row[0].strip()
        equipment = row[1].strip()
        classification = row[2].strip()
        student = row[4].strip()
        link_text = row[11].strip()
        
        if not number or not student:
            return None
            
        if link_text.lower() == "not submitted":
            return (number, student, "No valid link found", equipment, classification, judge)
        
        if not link_text or 'drive.google.com' not in link_text:
            return (number, student, "No valid link found", equipment, classification, judge)
            
        original_url = extract_original_url(link_text)
        return (number, student, original_url, equipment, classification, judge)
    except Exception as e:
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

def download_file(url, output_path, session, max_attempts=2, console=None):
    file_id = re.search(r'/d/([\w-]+)/', url)
    if not file_id:
        if console: console.insert(tk.END, f"Error: Could not extract file ID from {url}\n")
        return None
    
    download_url = f"https://drive.google.com/uc?export=download&id={file_id.group(1)}"
    
    for attempt in range(max_attempts):
        try:
            if console: console.insert(tk.END, f"Attempt {attempt + 1}/{max_attempts} for {output_path}\n")
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
            if console: console.insert(tk.END, f"Attempt {attempt + 1} failed: {str(e)}\n")
            if attempt == max_attempts - 1:
                return None
            time.sleep(1)

def download_batch(args):
    url, output_path, session, console = args
    result = download_file(url, output_path, session, console=console)
    return result if result else f"Failed: {output_path}"

def download_files(csv_data, judge_left, judge_right, output_dir, console, max_workers=12):
    tasks = []
    for judge, number, equipment, student, classification, music_link in csv_data:
        if judge not in [judge_left, judge_right]:
            continue
        
        student_clean = re.sub(r'[^\w\s-]', '', student).strip().replace(' ', '_')
        equipment_clean = re.sub(r'[^\w\s-]', '', equipment).strip().replace(' ', '_')
        classification_clean = re.sub(r'[^\w\s-]', '', classification).strip().replace(' ', '_')
        
        base_filename = f"{number}-{student_clean}-{equipment_clean}-{classification_clean}"
        judge_dir = os.path.join(output_dir, judge.replace(" ", "_"))
        os.makedirs(judge_dir, exist_ok=True)
        output_path = os.path.join(judge_dir, base_filename)
        
        if music_link.startswith("http"):
            tasks.append((music_link, output_path))
    
    with requests.Session() as session:
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(download_batch, (url, path, session, console)): path for url, path in tasks}
            for future in as_completed(future_to_file):
                result = future.result()
                if result.startswith("Failed"):
                    console.insert(tk.END, f"{result}\n")
                else:
                    console.insert(tk.END, f"Success: Downloaded to {result}\n")
                console.see(tk.END)
        
        end_time = time.time()
        console.insert(tk.END, f"Download completed in {end_time - start_time:.2f} seconds\n")
        console.see(tk.END)

# --- UI and Main Execution ---
def select_output_dir(output_label, console):
    folder = filedialog.askdirectory(title="Select Output Directory")
    if folder:
        output_label.config(text=f"Output: {folder}")
        console.insert(tk.END, f"Output directory set to: {folder}\n")
    return folder

def start_processing(judge1_entry, judge2_entry, output_label, console):
    judge_left = judge1_entry.get().strip()
    judge_right = judge2_entry.get().strip()
    output_dir = output_label.cget("text").replace("Output: ", "")
    
    if not judge_left or not judge_right:
        console.insert(tk.END, "Please enter both judge names!\n")
        return
    if not output_dir or output_dir == "Output: Not selected":
        console.insert(tk.END, "Please select an output directory!\n")
        return
    
    console.insert(tk.END, f"Starting process for Judge 1: {judge_left}, Judge 2: {judge_right}\n")
    console.insert(tk.END, f"Output directory: {output_dir}\n")
    
    try:
        with open('schedule.csv', 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            csv_data = list(csv_reader)
    except FileNotFoundError:
        console.insert(tk.END, "Error: Please save the CSV content as 'schedule.csv' in the same directory\n")
        return
    
    csv_output_data = generate_links(csv_data, judge_left, judge_right, output_dir, console=console)
    
    if csv_output_data:
        console.insert(tk.END, "Starting file downloads...\n")
        download_files(csv_output_data, judge_left, judge_right, output_dir, console)

def create_ui():
    root = tk.Tk()
    root.title("Music Link Downloader")
    root.geometry("600x400")
    
    # Input frame
    input_frame = ttk.Frame(root, padding="10")
    input_frame.pack(fill="x")
    
    ttk.Label(input_frame, text="Judge 1:").grid(row=0, column=0, padx=5, pady=5)
    judge1_entry = ttk.Entry(input_frame, width=20)
    judge1_entry.grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(input_frame, text="Judge 2:").grid(row=1, column=0, padx=5, pady=5)
    judge2_entry = ttk.Entry(input_frame, width=20)
    judge2_entry.grid(row=1, column=1, padx=5, pady=5)
    
    ttk.Label(input_frame, text="Output Folder:").grid(row=2, column=0, padx=5, pady=5)
    output_label = ttk.Label(input_frame, text="Output: Not selected")
    output_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    ttk.Button(input_frame, text="Select", 
              command=lambda: select_output_dir(output_label, console)).grid(row=2, column=2, padx=5, pady=5)
    
    # Start button
    start_button = ttk.Button(input_frame, text="Start",
                            command=lambda: Thread(target=start_processing, 
                                                 args=(judge1_entry, judge2_entry, output_label, console)).start())
    start_button.grid(row=3, column=0, columnspan=3, pady=10)
    
    # Console output
    console = scrolledtext.ScrolledText(root, width=70, height=20)
    console.pack(padx=10, pady=10, fill="both", expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    create_ui()