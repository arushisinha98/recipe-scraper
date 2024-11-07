import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import json
import random
from urllib.robotparser import RobotFileParser

class RecipeCrawler:
    def __init__(self, start_url, max_recipes=20):
        self.start_url = start_url
        self.max_recipes = max_recipes

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Start fresh by clearing visited URLs
        self.visited_urls = set()
        self.recipe_urls = set()
        self.unvisited_urls = set()
        self.base_domain = urlparse(start_url).netloc

        # load (un)visited URLs if any
        self.load_urls()
    
    def load_urls(self):
        """Load previously (un)visited URLs from JSON file"""
        try:
            self.visited_urls = self.unvisited_urls = set()
            with open(f'visited_urls.json', 'r') as f:
                self.visited_urls = set(json.load(f))
            with open(f'unvisited_urls.json', 'r') as f:
                self.unvisited_urls = set(json.load(f))
        except FileNotFoundError:
            print("Could not load previously (un)visited URLs.")

    def save_urls(self):
        """Save (un)visited URLs to JSON file"""
        with open('visited_urls.json', 'w') as f:
            json.dump(list(self.visited_urls), f)
        with open('unvisited_urls.json', 'w') as f:
            json.dump(list(self.unvisited_urls), f)

    def is_recipe_page(self, soup, url):
        """Check for specific div classes that indicate a recipe page"""
        if "#" not in url:
            required_classes = [
                'tasty-recipes-ingredients',
                'tasty-recipes-instructions',
            ]
            return all(soup.find('div', class_=class_name) for class_name in required_classes)
        return False

    def get_links(self, soup, current_url):
        """Extract all valid links from the page within the same domain"""
        links = set()

        try:
            # Find all <a> tags with href attribute
            all_links = soup.find_all('a', href=True)
            
            for a in all_links:
                href = a['href']
                
                # Skip tags, comments, response forms
                if any(s in href for s in ["tag", "respond", "comment"]):
                    continue

                # Handle relative URLs
                if not href.startswith('http'):
                    if href.startswith('/'):
                        full_url = f"https://{self.base_domain}{href}"
                    else:
                        full_url = urljoin(current_url, href)
                else:
                    full_url = href
                
                # Only include links from the same domain
                if urlparse(full_url).netloc == self.base_domain:
                    links.add(full_url)
        
        except Exception as e:
            print(f"Error getting links from {current_url}: {str(e)}")
        
        print(f"Total valid links found: {len(links)}")
        return links
    
    def crawl(self):
        """Start crawling from the start URL"""
        self.unvisited_urls = {self.start_url}
        print(f"\nStarting crawl from: {self.start_url}")
        
        try:
            while self.unvisited_urls and len(self.recipe_urls) < self.max_recipes:
                url = self.unvisited_urls.pop()
                print(f"\nProcessing: {url}")
                
                if url in self.visited_urls:
                    print("Already visited, skipping...")
                    continue
                
                try:
                    time.sleep(random.uniform(3, 7))  # Random delay between 3-7 seconds
                    
                    response = self.session.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Get new links before marking as visited
                    new_links = self.get_links(soup, url)
                    unvisited_links = new_links - self.visited_urls
                    self.unvisited_urls.update(unvisited_links)
                    print(f"Added {len(unvisited_links)} new URLs to visit")
                    
                    # Mark URL as visited
                    self.visited_urls.add(url)
                    
                    # Check if it's a recipe page
                    if self.is_recipe_page(soup, url):
                        self.recipe_urls.add(url)
                        print(f"Progress: {len(self.recipe_urls)}/{self.max_recipes}")
                    
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    continue
                
        finally:
            self.save_urls()
            self.save_recipes_to_markdown()
    
    def save_recipes_to_markdown(self):
        """Save the crawled URLs to a markdown file while preserving existing entries"""
        # First, load existing URLs from the markdown file if it exists
        existing_recipe_urls = set()
        
        try:
            with open('crawled_recipes.md', 'r', encoding='utf-8') as f:
                current_section = None
                for line in f:
                    # Remove whitespace and newlines from the line
                    line = line.strip()
                    
                    if "## Recipe Pages" in line:
                        current_section = "recipes"
                    # Check for URLs with more flexible matching
                    elif line.startswith("- "):
                        url = line[2:].strip()  # Remove "- " and any whitespace
                        if current_section == "recipes":
                            existing_recipe_urls.add(url)
        except FileNotFoundError:
            print("No existing markdown file found")
        except Exception as e:
            print(f"Error reading markdown file: {str(e)}")
        
        # Print debug information
        print(f"\nExisting recipe URLs: {len(existing_recipe_urls)}")
        print(f"New recipe URLs: {len(self.recipe_urls)}")
        
        # Combine existing and new URLs
        all_recipe_urls = existing_recipe_urls.union(self.recipe_urls)
        print(f"\nTotal recipe URLs after combining: {len(all_recipe_urls)}")
        
        # Write combined URLs to markdown file
        try:
            with open('crawled_recipes.md', 'w', encoding='utf-8') as f:
                f.write("# Crawled Recipe URLs\n\n")
                f.write("## Recipe Pages\n\n")
                for url in sorted(all_recipe_urls):
                    if url:  # Only write non-empty URLs
                        f.write(f"- {url}\n")
                
            print("\nSuccessfully wrote updated markdown file")
        except Exception as e:
            print(f"Error writing markdown file: {str(e)}")

def get_start_url(default_url = "https://www.gimmesomeoven.com/all-recipes"):
    """Get a random URL from unvisited_urls.json if it exists, else use default URL"""
    try:
        with open('unvisited_urls.json', 'r') as f:
            unvisited_urls = json.load(f)
            
            if unvisited_urls:  # If the list is not empty
                random_url = random.choice(unvisited_urls)
                print(f"Randomly selected URL from unvisited_urls.json: {random_url}")
                return random_url
            else:
                print("unvisited_urls.json is empty, using default URL")
                return default_url
                
    except FileNotFoundError:
        print("unvisited_urls.json not found, using default URL")
        return default_url
    except json.JSONDecodeError:
        print("Error reading unvisited_urls.json, using default URL")
        return default_url

# Usage
start_url = get_start_url()
crawler = RecipeCrawler(start_url, 2)
crawler.crawl()