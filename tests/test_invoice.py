from app.agent.agent import run_agent, clear_session


SESSION_ID = "invoice_test"

clear_session(SESSION_ID)

print("\n========== GENERATE GST INVOICE ==========")

response = run_agent(
    "Generate the GST invoice for bill ID 5.",
    SESSION_ID
)

print(response)