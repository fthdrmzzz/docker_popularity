import requests
import json
import csv
import os
from datetime import datetime, timedelta

BASE_URL = "https://hub.docker.com/v2/repositories/library/"
CUMULATIVE_DIR = "cumulative_pulls"
INTERVAL_DIR = "interval_pulls"

# Create directories if they don't exist
os.makedirs(CUMULATIVE_DIR, exist_ok=True)
os.makedirs(INTERVAL_DIR, exist_ok=True)

def get_repositories(page_size=100):
    repositories = []
    page = 1
    while True:
        url = f"{BASE_URL}"
        params = {"page_size": page_size, "page": page}
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            break

        data = response.json()

        if "results" not in data:
            print("Error: 'results' key not in response data")
            break

        repositories.extend(data["results"])

        if not data["next"]:
            break
        page += 1

    return repositories

def fetch_and_sort_images():
    repos = get_repositories()
    if not repos:
        print("No repositories fetched.")
        return []

    sorted_repos = sorted(repos, key=lambda x: x["pull_count"], reverse=True)
    for repo in sorted_repos:
        repo["official"] = True
    return sorted_repos

def save_data(data, folder, filename):
    filepath = os.path.join(folder, filename)
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {filepath}")

def save_current_data():
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    current_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    filename = f"docker_images_{timestamp_str}.json"
    data = fetch_and_sort_images()
    if data:
        save_data(data, CUMULATIVE_DIR, filename)
    return data, filename, current_timestamp


def load_last_cumulative_file():
    files = sorted(os.listdir(CUMULATIVE_DIR), reverse=True)
    if not files:
        print("No previous cumulative files found.")
        return None, None
    latest_file = files[0]
    with open(os.path.join(CUMULATIVE_DIR, latest_file), "r") as file:
        data = json.load(file)
    
    # Extract the full timestamp from the filename, e.g., "docker_images_2024-11-10_12-32-42.json"
    timestamp_str = latest_file.split("_", 2)[2].split(".")[0]
    last_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    return data, last_timestamp


def calculate_diff(new_data, old_data):
    old_data_dict = {repo["name"]: repo["pull_count"] for repo in old_data}
    diff_data = []

    for repo in new_data:
        name = repo["name"]
        new_count = repo["pull_count"]
        old_count = old_data_dict.get(name, 0)
        diff_count = new_count - old_count
        diff_data.append({
            "name": name,
            "namespace": repo["namespace"],
            "pull_count_diff": diff_count,
            "official": repo["official"]
        })

    return diff_data

def save_diff_data(diff_data, filename):
    save_data(diff_data, INTERVAL_DIR, filename)

if __name__ == "__main__":
    import sys

    compare_last = len(sys.argv) > 1 and sys.argv[1] == "--compare-last"


    if compare_last:
        last_data, last_timestamp = load_last_cumulative_file()
        current_data, current_filename, current_timestamp = save_current_data()
        if last_data and last_timestamp:
            interval_duration = current_timestamp - last_timestamp
            duration_str = str(interval_duration).replace(":", "-")
            diff_data = calculate_diff(current_data, last_data)
            diff_filename = f"docker_images_diff_{current_timestamp}_interval_{duration_str}.json"
            save_diff_data(diff_data, diff_filename)
