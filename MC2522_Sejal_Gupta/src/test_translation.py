from api.translation_api import translate_text


print("\n========== MYMEMORY TRANSLATION TEST ==========\n")


text = "तुम पागल हो"

print("Original:")
print(text)


translated = translate_text(
    text,
    source_language="hi",
    target_language="en"
)


print("\nTranslated:")
print(translated)