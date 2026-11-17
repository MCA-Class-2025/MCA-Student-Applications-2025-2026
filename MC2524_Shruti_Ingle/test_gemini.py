from src.gemini_api import export_gemini_dataset

result = export_gemini_dataset("sample_image.png")

print(result[:500])