from app.agent.agent import run_agent, clear_session


SESSION_ID = "preferences_test"

clear_session(SESSION_ID)


print("\n========== SET PREFERENCE ==========")

response = run_agent(
    "Set my preferred payment mode to UPI.",
    SESSION_ID
)

print(response)


print("\n========== GET PREFERENCE ==========")

response = run_agent(
    "What is my preferred payment mode?",
    SESSION_ID
)

print(response)


print("\n========== UPDATE PREFERENCE ==========")

response = run_agent(
    "Change my preferred payment mode to CASH.",
    SESSION_ID
)

print(response)


print("\n========== GET UPDATED PREFERENCE ==========")

response = run_agent(
    "What is my preferred payment mode now?",
    SESSION_ID
)

print(response)


print("\n========== SHOW ALL PREFERENCES ==========")

response = run_agent(
    "Show all my saved preferences.",
    SESSION_ID
)

print(response)