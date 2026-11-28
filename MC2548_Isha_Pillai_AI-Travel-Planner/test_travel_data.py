from services.travel_data_service import get_destination_context


destination = "London"

context = get_destination_context(
    destination
)


print("\n================================")
print("TRAVEL CONTEXT")
print("================================")

print(context)