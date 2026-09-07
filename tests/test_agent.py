from app.agent.agent import run_agent, clear_session


SESSION_ID = "khata_test"

clear_session(SESSION_ID)


print("\n========== ADD CREDIT ==========")

response = run_agent(
    "Put ₹500 on Ramesh's credit.",
    SESSION_ID
)

print(response)


print("\n========== CHECK BALANCE ==========")

response = run_agent(
    "What is Ramesh's balance?",
    SESSION_ID
)

print(response)


print("\n========== RECORD PAYMENT ==========")

response = run_agent(
    "Ramesh paid ₹300 by UPI.",
    SESSION_ID
)

print(response)


print("\n========== CHECK BALANCE AGAIN ==========")

response = run_agent(
    "What is Ramesh's balance now?",
    SESSION_ID
)

print(response)


print("\n========== SHOW LEDGER ==========")

response = run_agent(
    "Show me Ramesh's Khata ledger.",
    SESSION_ID
)

print(response)