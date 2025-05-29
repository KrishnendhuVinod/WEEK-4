import json
import random
from difflib import SequenceMatcher

# Load ingredients database
with open("ingredients.json") as f:
    ingredients_db = json.load(f)

#Function to measure string similarity
def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

#Function to find matching ingredients
def find_matching_ingredients(user_input: str, ingredients: list, threshold: float = 0.6) -> list:
    keywords = user_input.lower().split()
    matched = []

    for keyword in keywords:
        for ingredient in ingredients:
            score = similar(keyword, ingredient['name'].lower())
            if score >= threshold and ingredient not in matched:
                matched.append(ingredient)
    return matched

#Function for generating recipe
def generate_recipe(preferences: str, servings: int, iteration: int, prev_recipe=None) -> dict:
    
    if iteration == 1:
        matched_ingredients = find_matching_ingredients(preferences, ingredients_db)
        if not matched_ingredients:
            matched_ingredients = ingredients_db[:3]

       
        ingredients_list = [{"name": ing["name"], "quantity": 100} for ing in matched_ingredients[:5]]
    else:
        
        ingredients_list = []
        
        if prev_recipe:
            
            for ing in prev_recipe["ingredients"]:
                change_pct = random.uniform(0.7, 1.3)
                new_qty = max(20, int(ing["quantity"] * change_pct))  # minimum 20g to avoid zero
                ingredients_list.append({"name": ing["name"], "quantity": new_qty})

            
            existing_names = {ing["name"] for ing in ingredients_list}
            available_to_add = [ing for ing in ingredients_db if ing["name"] not in existing_names]
            if available_to_add and random.random() < 0.5:  # 50% chance to add
                new_ing = random.choice(available_to_add)
                ingredients_list.append({"name": new_ing["name"], "quantity": 50})

            
            if len(ingredients_list) > 2 and random.random() < 0.3:  # 30% chance to remove one
                to_remove = random.choice(ingredients_list)
                ingredients_list.remove(to_remove)
        else:
            
            ingredients_list = [{"name": ing["name"], "quantity": 100} for ing in ingredients_db[:3]]

    return {
        "name": f"{preferences.title()} Recipe Attempt {iteration}",
        "servings": servings,
        "ingredients": ingredients_list
    }

#Function for checking the nutrients
def check_nutrition(recipe: dict) -> dict:
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for ingredient in recipe["ingredients"]:
        for item in ingredients_db:
            if item["name"] == ingredient["name"]:
                factor = ingredient["quantity"] / 100
                total["calories"] += item["calories"] * factor
                total["protein"] += item["protein"] * factor
                total["carbs"] += item["carbs"] * factor
                total["fat"] += item["fat"] * factor
                break
    per_serving = {k: round(v / recipe["servings"], 2) for k, v in total.items()}

    balanced = per_serving["protein"] >= 10 and per_serving["calories"] <= 600
    return {
        "per_serving": per_serving,
        "balanced": balanced
    }

#Round-robin agent  workflow controller
def run_chef(preferences: str, servings: int, max_attempts: int = 5):
    prev_recipe = None
    for iteration in range(1, max_attempts + 1):
        print(f"\n=== Iteration {iteration} ===")
        recipe_data = generate_recipe(preferences, servings, iteration, prev_recipe)
        nutrition_data = check_nutrition(recipe_data)

        if recipe_data and nutrition_data:
            print(f"\nRecipe: {recipe_data['name']} (Serves {recipe_data['servings']})")
            print("Ingredients:")
            for item in recipe_data["ingredients"]:
                print(f"- {item['quantity']}g {item['name']}")

            per = nutrition_data["per_serving"]
            print("\nNutrition Summary (Per Serving):")
            print(f"- Calories: {per['calories']}")
            print(f"- Protein: {per['protein']}")
            print(f"- Carbs: {per['carbs']}")
            print(f"- Fat: {per['fat']}")

            print(f"\nBalanced Meal: {'Yes' if nutrition_data['balanced'] else 'No'}")

            if nutrition_data['balanced']:
                print("\nThe recipe is balanced.")
                break
            else:
                print("\nRecipe is not balanced. Adjusting ingredients and retrying...")
                prev_recipe = recipe_data
        else:
            print("Failed to generate recipe or nutrition info.")
    else:
        print("\nCould not create a balanced recipe within iteration limit.")

#Main function
if __name__ == "__main__":
    print(" Personal Chef! Type 'exit' to quit.\n")
    while True:
        pref = input("Enter what you want to eat: ").strip()
        if pref.lower() == "exit":
            break
        try:
            servings = int(input("How many servings? "))
            run_chef(pref, servings)
        except ValueError:
            print("Please enter a valid number of servings.\n")
