from agents import function_tool
from dotenv import load_dotenv
load_dotenv()   
import googlemaps
import os
import time

# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'      # Purple
    BLUE = '\033[94m'        # Blue
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    ENDC = '\033[0m'         # Reset color
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline

API_KEY = os.getenv("GOOGLE_API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

@function_tool
def research_destination(destination:str) -> list[dict]:
    print(f"{Colors.YELLOW}[TOOL] research_destination called with destination='{destination}'{Colors.ENDC}")
    start_time = time.time()
    """
    Research top tourist attractions in the given destination using Google Places API.
    
    Args:
        destination (str): City or location name.
    Returns:
        list[dict]: List of places with name, address, rating, reviews, etc.
    """
    results = gmaps.places(query=f"Top Tourist Attractions in {destination}")
    results = results.get("results", [])
    duration = time.time() - start_time
    print(f"{Colors.GREEN}[TOOL] research_destination completed – {len(results)} results in {duration:.2f}s{Colors.ENDC}")
    # for result in results:
    #     print("Name: ", result["name"])
    #     print("Address: ", result["formatted_address"])
    #     print("Rating: ", result["rating"])
    #     print("Total Reviews: ", result["user_ratings_total"])

    return results





