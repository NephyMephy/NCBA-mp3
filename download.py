import os
import sys
import csv
import gdown
import re
import mimetypes
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def guess_extension(file_path):
    """Guess the file extension based on content if necessary."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mimetypes.guess_extension(mime_type) or '.mp3' if mime_type else '.mp3'

def download_file(url, output_path, session, max_attempts=2):
    """Download a file using requests with retry logic."""
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
            time.sleep(1)  # Reduced wait time

def download_batch(args):
    """Wrapper for downloading a single file with session."""
    url, output_path, session = args
    result = download_file(url, output_path, session)
    return result if result else f"Failed: {output_path}"

def download_files(judge_left, judge_right, csv_file="links_data.csv", max_workers=8):
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return
    
    # Create directories
    for judge in [judge_left, judge_right]:
        judge_dir = judge.replace(" ", "_")
        os.makedirs(judge_dir, exist_ok=True)
        print(f"Created directory: {judge_dir}")
    
    # Read CSV and prepare download tasks
    tasks = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            judge = row['Judge']
            if judge not in [judge_left, judge_right]:
                continue
            
            number = row['Number']
            equipment = row['Equipment']
            student = row['Student']
            classification = row['Classification']
            music_link = row['Music Link']
            
            student_clean = re.sub(r'[^\w\s-]', '', student).strip().replace(' ', '_')
            equipment_clean = re.sub(r'[^\w\s-]', '', equipment).strip().replace(' ', '_')
            classification_clean = re.sub(r'[^\w\s-]', '', classification).strip().replace(' ', '_')
            
            base_filename = f"{number}-{student_clean}-{equipment_clean}-{classification_clean}"
            judge_dir = judge.replace(" ", "_")
            output_path = os.path.join(judge_dir, base_filename)
            
            tasks.append((music_link, output_path))
    
    # Use a single session for all requests
    with requests.Session() as session:
        # Download in parallel
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

def main():
    if len(sys.argv) < 3:
        print("Usage: python download.py \"Judge Name 1\" \"Judge Name 2\"")
        return
    
    judge_left = sys.argv[1]
    judge_right = sys.argv[2]
    download_files(judge_left, judge_right)

if __name__ == "__main__":
    main()