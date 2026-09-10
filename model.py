import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
data = pd.read_csv("Data/landslide_data.csv")


# Features used by the AI
features = [
    "rainfall",
    "soil_moisture",
    "slope",
    "elevation",
    "historical_landslides"
]

X = data[features]
y = data["risk"]


# Split data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)


# Create Random Forest model
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    random_state=42
)


# Train the AI
model.fit(X_train, y_train)


# Test the AI
predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)


# Display results
print("=" * 50)
print("      NER LANDSLIDE AI MODEL")
print("=" * 50)

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# Save trained model
joblib.dump(
    model,
    "landslide_model.pkl"
)


print("\n" + "=" * 50)
print("MODEL TRAINING COMPLETE")
print("=" * 50)
print("Saved as: landslide_model.pkl")