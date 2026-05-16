import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from datetime import datetime
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

print("🔄 Fetching training data...")

db = SessionLocal()

# Get appointments with status
appointments = db.query(Appointment).filter(
    Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW])
).all()

print(f"✅ Found {len(appointments)} appointments")

data = []
for apt in appointments:
    patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
    if not patient:
        continue

    # Calculate past history
    past = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.id < apt.id,
        Appointment.status.in_([AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW])
    ).all()

    total_past = len(past)
    missed_past = sum(1 for a in past if a.status == AppointmentStatus.NO_SHOW)

    # Age group
    age_group = "unknown"
    if patient.date_of_birth:
        age = datetime.now().year - patient.date_of_birth.year
        if age < 35:
            age_group = "18-35"
        elif age <= 50:
            age_group = "35-50"
        else:
            age_group = "50+"

    # Time features
    apt_hour = apt.appointment_date.hour
    apt_day = apt.appointment_date.weekday()
    is_weekend = 1 if apt_day >= 5 else 0
    is_morning = 1 if apt_hour < 12 else 0

    # Target
    target = 1 if apt.status == AppointmentStatus.NO_SHOW else 0

    data.append({
        'age_group': age_group,
        'has_phone': 1 if patient.phone else 0,
        'total_past': total_past,
        'missed_past': missed_past,
        'miss_rate': missed_past / total_past if total_past > 0 else 0,
        'apt_hour': apt_hour,
        'apt_day': apt_day,
        'is_weekend': is_weekend,
        'is_morning': is_morning,
        'target': target
    })

db.close()

if len(data) < 50:
    print(f"⚠️ Not enough data: {len(data)} records")
    sys.exit(1)

df = pd.DataFrame(data)
print(f"📊 Data shape: {df.shape}")
print(f"   No-show rate: {df['target'].mean() * 100:.1f}%")

# Prepare features
feature_cols = ['age_group', 'has_phone', 'total_past', 'missed_past',
                'miss_rate', 'apt_hour', 'apt_day', 'is_weekend', 'is_morning']

X = df[feature_cols].copy()
y = df['target']

# Encode age_group
le = LabelEncoder()
X['age_group'] = le.fit_transform(X['age_group'])

# Train model
print("🔄 Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model
os.makedirs('app/ml/models', exist_ok=True)
with open('app/ml/models/no_show_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('app/ml/models/age_label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("✅ Model saved to app/ml/models/")
print(f"   Features used: {feature_cols}")

# Feature importance
print("\n📈 Feature Importance:")
for name, imp in zip(feature_cols, model.feature_importances_):
    print(f"   {name}: {imp * 100:.1f}%")