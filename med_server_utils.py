import pandas as pd
import json
import os
from groq import Groq
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("LeadEnrichmentServer")
llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
model = "qwen/qwen3-32b"


def enrich_with_llm(lead: dict) -> dict:
    """
    Use the LLM to enrich a lead with synthetic intelligence-derived fields.
    """
    prompt = f"""
    You are an expert sales assistant for a pharmaceutical company.

    Here is one lead record:
    {json.dumps(lead, indent=2)}

    Based on your reasoning and world knowledge, infer and output:
    1. company_size (small / medium / large)
    2. estimated_budget (in INR)
    3. potential_segment (Hospital / Clinic / Individual Doctor / Distributor)
    4. Tier of the city, like 1,2,3

    Respond in JSON format with keys:
    company_size, estimated_budget, potential_segment, tier
    """

    try:
        response = llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        result = response.choices[0].message.content
        result = result.split("{")[1]
        result = "{" + result
        output = json.loads(result)
    except Exception as e:
        print(f"[Warning] LLM enrichment failed for {lead.get('email')}: {e}")
        output = {
            "company_size": "unknown",
            "estimated_budget": "N/A",
            "potential_segment": "unknown",
            "tier" : 'N/A'
        }

    lead.update(output)
    return lead


@mcp.tool()
def process_csv(input_path: str, output_path: str):
    """
    Full end-to-end pipeline using only LLM enrichment.
    """
    leads = pd.read_csv(input_path)
    enriched = []

    print(f"🚀 Processing {len(leads)} leads using LLM enrichment...")
    for _, row in leads.iterrows():
        lead = row.to_dict()
        enriched_lead = enrich_with_llm(lead)
        enriched.append(enriched_lead)

    df_out = pd.DataFrame(enriched)
    df_out.to_csv(output_path, index=False)
    print(f"✅ Enriched leads saved to {output_path}")


def decide_action(row):
    budget = row.get("estimated_budget", 0)
    tier = row.get("tier", "")
    segment = str(row.get("potential_segment", "")).lower()

    try:
        budget = float(budget)
    except:
        budget = 0

    if str(tier) == "1" and budget > 5000000:
        return "Call"
    elif str(tier) == "2" and budget > 2000000 and "hospital" in segment:
        return "Email"
    else:
        return "Ignore"
    

@mcp.tool()
def assign_icp(input_path: str, output_path: str):
    leads = pd.read_csv(input_path)
    icp = []

    print(f"🚀 Assigning {len(leads)} leads using rule based approach...")
    for _, row in leads.iterrows():
        action = decide_action(row)
        row["action"] = action
        icp.append(row)
    df_out = pd.DataFrame(icp)
    df_out.to_csv(output_path, index=False)
    print(f"✅ ICP fits saved to {output_path}")