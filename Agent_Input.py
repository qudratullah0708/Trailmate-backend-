from pydantic import BaseModel, ValidationError, field_validator
from datetime import datetime
from typing import Literal
import openai
import json
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)


# 🔷 Pydantic schema
class AccommodationRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    guests: int
    min_budget: float
    max_budget: float
    standard: Literal['economy', 'standard', 'luxury']

    @field_validator("check_in", "check_out")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD format")
        return v

    @field_validator("guests")
    @classmethod
    def validate_guests(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Guests must be at least 1")
        return v

    @field_validator("max_budget")
    @classmethod
    def validate_budget_range(cls, v: float, info) -> float:
      min_budget = info.data.get("min_budget")
      if min_budget is not None and min_budget > v:
        raise ValueError("min_budget cannot exceed max_budget")
      return v



# 🔷 System prompt
system_prompt = """
You are an assistant that extracts structured fields from a natural language accommodation request.
Return ONLY a JSON object in this format:

{
  "destination": str,
  "check_in": "YYYY-MM-DD",
  "check_out": "YYYY-MM-DD",
  "guests": int,
  "min_budget": float,
  "max_budget": float,
  "standard": "economy|standard|luxury"
}

## Convert dates to YYYY-MM-DD ISO format. Budgets should be numbers.
## If information is missing, make reasonable assumptions.
## Do not include any explanations, notes, or markdown formatting. Only output the JSON object.
"""



def extract_query_data(user_query: str) -> dict:
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,  # disable streaming for simplicity
        stop=None,
    )

    content = completion.choices[0].message.content.strip()
    # ✅ Remove wrapping backticks if present
    if content.startswith("```") and content.endswith("```"):
        content = content.strip("`").strip()
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON: {content}")


