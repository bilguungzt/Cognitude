#!/usr/bin/env python3
"""
Debug script to trace smart routing decisions
"""

import sys
sys.path.insert(0, '.')

from app.services.smart_router import SmartRouter, MODEL_CHARACTERISTICS
from app.services.tokens import count_tokens

# Test the classification and routing logic
test_messages = [{"role": "user", "content": "Classify: positive or negative? 'I love this product!'"}]

print("=== Smart Routing Debug ===\n")

# Step 1: Classify complexity
full_prompt = " ".join([msg.get("content", "") for msg in test_messages])
prompt_lower = full_prompt.lower()

try:
    token_count = count_tokens(full_prompt)
except:
    token_count = len(full_prompt.split())

print(f"Prompt: {full_prompt}")
print(f"Token count: {token_count}")

# Check keywords
simple_matches = sum(1 for kw in SmartRouter.SIMPLE_TASK_KEYWORDS if kw in prompt_lower)
complex_matches = sum(1 for kw in SmartRouter.COMPLEX_TASK_KEYWORDS if kw in prompt_lower)

print(f"Simple keywords found: {simple_matches}")
print(f"Complex keywords found: {complex_matches}")

# Classification logic
complexity = "medium"  # default
if token_count < 100 and simple_matches > 0:
    complexity = 'simple'
elif token_count < 50 and complex_matches == 0:
    complexity = 'simple'
elif token_count > 500 or complex_matches >= 2:
    complexity = 'complex'
elif simple_matches > complex_matches:
    complexity = 'simple'
elif complex_matches > simple_matches:
    complexity = 'complex'

print(f"Classified complexity: {complexity}\n")

# Step 2: Check which models are suitable
print("=== Model Suitability Check ===")
available_models = ["gemini-2.5-pro", "gemini-2.5-flash-lite", "gpt-3.5-turbo"]
available_providers = ["google"]

for model_name in available_models:
    if model_name in MODEL_CHARACTERISTICS:
        model = MODEL_CHARACTERISTICS[model_name]
        is_suitable = complexity in model.suitable_for_complexity
        provider_matches = model.provider in available_providers
        
        print(f"\nModel: {model_name}")
        print(f"  Provider: {model.provider}")
        print(f"  Suitable for: {model.suitable_for_complexity}")
        print(f"  Complexity match: {is_suitable}")
        print(f"  Provider match: {provider_matches}")
        print(f"  Overall suitable: {is_suitable and provider_matches}")
        
        if is_suitable and provider_matches:
            print(f"  ✓ This model SHOULD be selected!")
        else:
            print(f"  ✗ This model will be filtered out")
    else:
        print(f"\nModel: {model_name} - NOT FOUND in MODEL_CHARACTERISTICS!")

print(f"\n=== Routing Decision ===")
# Simulate the routing
routing_decision = SmartRouter.select_model(
    complexity=complexity,
    optimize_for="cost",
    available_models=available_models,
    available_providers=available_providers
)

print(f"Selected model: {routing_decision['selected_model']}")
print(f"Selected provider: {routing_decision['selected_provider']}")
print(f"Reason: {routing_decision['reason']}")

if routing_decision['reason'] == 'default_fallback':
    print("⚠️  FALLBACK USED - No suitable models found!")
    print("This means all models were filtered out during the selection process.")
else:
    print("✅ Model successfully selected!")