
from experiments.promptfoo_provider import call_api
import time

print("Testing call_api...")
start = time.time()
print(call_api("What is photosynthesis?", None, None))
print(f"Duration: {time.time() - start:.2f}s")
