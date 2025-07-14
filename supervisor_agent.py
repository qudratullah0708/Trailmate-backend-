import asyncio
import openai
from agents import Agent, Runner, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel
from Agent_Input import extract_query_data, AccommodationRequest
from airbnb_scraper import scrape_airbnb
from Research_dest import research_destination
from pydantic import BaseModel, ValidationError
from groq import Groq
import os
import json
from dotenv import load_dotenv
import time
from datetime import datetime
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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

load_dotenv()


set_tracing_disabled(disabled=True)
# env variable
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
MODEL=os.getenv("MODEL")
print(MODEL)

# 🔷 User input
user_query = (
    "I want a luxury stay in Dubai from Aug 10 to Aug 15 for 2 guests, "
    "with an overall trip budget between 1000 and 3000 dollars."
)

# 🔷 Run extraction + validation
try:
    extracted_data = extract_query_data(user_query)
#     extracted_data = {
#     "destination": "Dubai",
#     "check_in": "2025-08-10",
#     "check_out": "2025-08-15",
#     "guests": 2,
#     "min_budget": 1000,
#     "max_budget": 3000,
#     "standard": "luxury"
# }
    print("\n📝 Extracted JSON")
    print(json.dumps(extracted_data, indent=2))

    validated = AccommodationRequest(**extracted_data)
    print("\n✅ Validated Data:")
    print(validated.model_dump())

except ValidationError as e:
    print("\n❌ Validation error:\n", e)

except Exception as e:
    print("\n❌ Error:\n", e)
print("Extracted Data:", extracted_data)

# Calculate trip duration and per-night budget from total budget
destination = extracted_data["destination"]
check_in_str = extracted_data['check_in']
check_out_str = extracted_data['check_out']

try:
    check_in_date = datetime.fromisoformat(check_in_str)
    check_out_date = datetime.fromisoformat(check_out_str)
    num_nights = (check_out_date - check_in_date).days
    if num_nights <= 0:
        raise ValueError("Check-out date must be after check-in date.")
except (ValueError, TypeError) as e:
    print(f"{Colors.RED}Error parsing dates: {e}{Colors.ENDC}")
    exit()

duration = f"{num_nights} nights ({check_in_str} to {check_out_str})"
preferences = extracted_data["standard"]
min_total_budget = extracted_data["min_budget"]
max_total_budget = extracted_data["max_budget"]
guests = extracted_data["guests"]

# Heuristic: Allocate 60% of the max total budget to accommodation to find a per-night price for the scraper.
# This is an assumption because the total budget must also cover activities, food, etc.
accommodation_budget_ratio = 0.6
max_accom_budget = max_total_budget * accommodation_budget_ratio
max_nightly_price = int(max_accom_budget / num_nights) if num_nights > 0 else max_accom_budget

print(f"{Colors.BLUE}Calculated trip duration: {num_nights} nights.{Colors.ENDC}")
print(f"{Colors.BLUE}Overall trip budget: ${min_total_budget}-${max_total_budget}.{Colors.ENDC}")
print(f"{Colors.BLUE}Derived max nightly accommodation price for search: ${max_nightly_price} (using {accommodation_budget_ratio*100:.0f}% of max total).{Colors.ENDC}")


# Define agents
experience_planner = Agent(
    name="Experience Planner Agent",
    instructions=(
        f"Use the `research_destination` tool to research and suggest engaging, "
        f"local, and culturally relevant activities and attractions in {destination}. "
        f"The tool only requires the destination name as input. "
        f"After getting the results, analyze and recommend activities suitable for {guests} guest(s) "
        f"for a {duration} trip. The total budget for the trip (accommodations and activities) is ${min_total_budget}-${max_total_budget}. "
        f"The user has a preference for '{preferences}' level experiences. "
        f"Include a variety of options for adventure, relaxation, and sightseeing with estimated costs per person."
    ),
    tools=[research_destination],
    model=LitellmModel(model=MODEL, api_key=GROQ_API_KEY),
)

accommodation_agent = Agent(
    name="Accommodation Agent",
    instructions=(
        f"Use the `scrape_airbnb` tool to find available accommodation options. "
        f"The tool requires these parameters: location='{destination}', guests={guests}, "
        f"max_price={max_nightly_price}, check_in='{extracted_data['check_in']}', check_out='{extracted_data['check_out']}'. "
        f"Call the tool with these exact parameters. The max_price of ${max_nightly_price} is a per-night budget derived from the total trip budget. "
        f"Analyze and rank results based on price, guest ratings, proximity to attractions, and overall value. "
        f"Return up to 5 of the best options with clear reasoning for {preferences} preferences."
    ),
    tools=[scrape_airbnb],
    model=LitellmModel(model=MODEL, api_key=GROQ_API_KEY),
)



budget_optimizer = Agent(
    name="Budget Optimizer Agent",
    instructions=(
        f"You will receive activity recommendations and accommodation options. "
        f"Optimize the trip plan for {guests} guest(s) in {destination} for {duration}. "
        f"The total budget for the entire trip is between ${min_total_budget} and ${max_total_budget}. "
        f"The user's preference is '{preferences}'. "
        f"Create a day-by-day itinerary with specific costs for activities and accommodation. "
        f"Provide a final summary of the total estimated cost and confirm it fits within the budget. "
        f"Suggest alternatives if the plan exceeds the budget."
    ),
    model=LitellmModel(model=MODEL, api_key=GROQ_API_KEY),
)

async def main():
    print(f"{Colors.HEADER}{Colors.BOLD}=== Supervisor Agent Started ==={Colors.ENDC}")
    print(f"{Colors.BLUE}Agents are running...{Colors.ENDC}\n")

    t0 = time.time()

    # Run planner & accommodation in parallel
    print(f"{Colors.BLUE}[SUPERVISOR] Launching Experience Planner and Accommodation agents in parallel...{Colors.ENDC}")
    planner_start = time.time()
    planner_task = Runner.run(experience_planner, destination)
    accom_start = time.time()
    accom_task = Runner.run(accommodation_agent, "Find accommodations for the specified parameters in the instructions")

    planner_result, accommodation_result = await asyncio.gather(planner_task, accom_task)
    print(f"{Colors.GREEN}[SUPERVISOR] Experience Planner completed in {time.time()-planner_start:.2f}s{Colors.ENDC}")
    print(f"{Colors.GREEN}[SUPERVISOR] Accommodation Agent completed in {time.time()-accom_start:.2f}s{Colors.ENDC}")

    print(f"\n{Colors.GREEN}✅ Planner Output (truncated):{Colors.ENDC}\n", str(planner_result.final_output)[:500], "...\n")
    print(f"\n{Colors.GREEN}✅ Accommodation Output (truncated):{Colors.ENDC}\n", str(accommodation_result.final_output)[:500], "...\n")

    # Combine results & pass to Budget Optimizer
    combined_input = (
        f"Trip Planning Data for {destination} ({duration}):\n"
        f"Guests: {guests} | Total Trip Budget: ${min_total_budget}-${max_total_budget} | Standard: {preferences}\n\n"
        f"ACTIVITIES RESEARCH:\n{planner_result.final_output}\n\n"
        f"ACCOMMODATION OPTIONS:\n{accommodation_result.final_output}\n\n"
        f"Please create an optimized itinerary that combines the best activities and accommodation "
        f"within the specified total budget constraints. Include a day-by-day cost breakdown and a final total."
    )

    print(f"{Colors.BLUE}[SUPERVISOR] Launching Budget Optimizer agent...{Colors.ENDC}")
    budget_start = time.time()
    budget_result = await Runner.run(budget_optimizer, combined_input)
    print(f"{Colors.GREEN}[SUPERVISOR] Budget Optimizer completed in {time.time()-budget_start:.2f}s{Colors.ENDC}")

    print(f"\n{Colors.GREEN}✅ Final Budget-Optimized Plan:{Colors.ENDC}\n", budget_result.final_output)
    print(f"{Colors.HEADER}{Colors.BOLD}=== Supervisor Agent Finished in {time.time()-t0:.2f}s ==={Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(main())
