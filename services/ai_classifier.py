import google.generativeai as genai
from PIL import Image
import os
import json

def classify_waste_significance(image_path: str, user_description: str):
    """
    Uses Gemini 1.5 Flash to determine if the report is a significant 
    environmental hazard or minor litter.
    """
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    img = Image.open(image_path)
    
    prompt = f"""
    Analyze this environmental waste report.
    User Description: {user_description}
    
    Tasks:
    1. Classify: Is this 'Significant Dumping', 'Infrastructure Blockage' (like a drain), or 'Minor Litter'?
    2. Volume: Estimate the scale (Small, Medium, Large).
    3. Score: Provide a significance score from 0 to 100.
    
    Return JSON only:
    {{
      "classification": "string",
      "scale": "string",
      "significance_score": int,
      "is_valid_waste": bool
    }}
    """

    response = model.generate_content([prompt, img])
    
    try:
        # Clean markdown formatting if present in response
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        # Return a neutral result if AI fails
        return {"is_valid_waste": True, "significance_score": 50, "classification": "unknown"}