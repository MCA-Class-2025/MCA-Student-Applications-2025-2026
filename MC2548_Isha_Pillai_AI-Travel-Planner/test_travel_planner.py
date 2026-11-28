from services.travel_planner import create_travel_plan


result = create_travel_plan(
    destination="London",
    days=3,
    budget=80000
)


print("\n================================")
print("AI TRAVEL PLAN")
print("================================")

print(result)