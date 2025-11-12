import asyncio
from med_server_utils import mcp

async def main():
    # Upload a lead
    resp1 = await mcp.call_tool("process_csv", {
        "input_path": "data.csv",
        "output_path": "enriched_medical_leads_llm.csv",
    })
    print("Lead enriched:", resp1)

    # Enrich leads
    resp2 = await mcp.call_tool("assign_icp", {
        "input_path": "enriched_medical_leads_llm.csv",
        "output_path": "enriched_medical_leads_llm_icp.csv",
    })
    print("ICP Fit:", resp2)

asyncio.run(main())

