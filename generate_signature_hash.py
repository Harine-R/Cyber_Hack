import hashlib

def generate_signature_hash(filepath):
    with open(filepath, "rb") as f:
        image_bytes = f.read()
    return hashlib.sha256(image_bytes).hexdigest()

# Run once with your HR signature image
hash_value = generate_signature_hash("data/signatures/hr_signature.jpeg")
print("HR Signature Hash:", hash_value)
