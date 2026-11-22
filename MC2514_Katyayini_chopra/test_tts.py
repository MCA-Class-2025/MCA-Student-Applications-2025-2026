from services.tts_service import text_to_speech


text = """
FixAI has analyzed your image.

The detected issue is damaged wall render.

The severity is high.

Possible causes include moisture ingress,
aging plaster, and poor adhesion.

We recommend contacting a wall repair professional.
"""


output = text_to_speech(
    text
)


print(
    "\n===== TEXT TO SPEECH ====="
)

print(
    "Audio generated:"
)

print(
    output
)