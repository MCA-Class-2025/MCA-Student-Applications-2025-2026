from src.moderator import analyze_comment

print("\n================================")
print("   HUGGING FACE API TEST")
print("================================\n")

comment = "You are such a stupid idiot."

print("Comment:")
print(comment)

print("\nSending to Hugging Face...\n")

result = analyze_comment(comment)

print("========== RESULT ==========\n")
print(result)