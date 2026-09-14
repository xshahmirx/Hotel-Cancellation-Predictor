# 🏨 Hotel Booking Cancellation Predictor

An end-to-end machine learning project that predicts whether a hotel booking will be cancelled,
built for an *Introduction to AI* course. A Random Forest learns from ~70,000 real bookings and
serves predictions through an interactive Streamlit web app.

**Live demo:** _paste your Streamlit link here_

## Dataset
[Hotel Booking Demand](https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand) (Kaggle):
119,390 bookings × 32 columns from a city hotel and a resort hotel, originally published by
Antonio, Almeida & Nunes in *Data in Brief* (2019). After cleaning: 87,204 rows.

## Pipeline
1. Load dataset
2. Clean data (missing values, duplicates, zero-guest rows, answer-leaking columns removed)
3. Preprocessing (feature engineering, one-hot encoding → 245 features)
4. Exploratory data analysis
5. Train/test split (80/20, stratified): 69,763 seen rows, 17,441 unseen rows
6. Train model (Random Forest Classifier; Logistic Regression as baseline)
7. Predict on unseen data & evaluate (accuracy, precision, recall, F1, ROC-AUC)
8. Export a compact pipeline model for deployment

## Results (measured on the 17,441 unseen test bookings)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Random Forest | 0.841 | 0.765 | 0.610 | 0.679 | 0.896 |
| Random Forest (balanced) | 0.838 | 0.691 | 0.744 | 0.717 | 0.900 |
| **RF balanced + threshold 0.45** | **0.828** | **0.654** | **0.799** | **0.719** | **0.900** |
| Logistic Regression | 0.791 | 0.675 | 0.464 | 0.550 | 0.827 |

Random Forest beats Logistic Regression on every metric. Balancing the classes and tuning the
decision threshold on F1 raised recall from 0.61 to 0.80 while keeping accuracy at 83%.

The deployed app uses a lighter pipeline model (one-hot encoder + 120-tree Random Forest,
threshold 0.55): accuracy 80.5%, recall 0.76, ROC-AUC 0.88.

## Where is the AI?
The Random Forest algorithm learns decision rules from the training bookings during `model.fit()`
without any rules being hand-written. It then applies those rules to bookings it has never seen in
`model.predict_proba()`. Everything before that (loading, cleaning, EDA, splitting) is data preparation.

## The app
- **Predict**: enter 25 booking details, get a probability with an animated gauge, an adjustable
  decision threshold, and a what-if analysis that re-runs the model with one detail changed.
- **Batch predictions**: upload a CSV, score every row, see the risk distribution and download results.
- **Model performance**: metrics, feature importance, and a four-model comparison.
- **Data insights**: live charts computed from the dataset.
- **About**: the pipeline and where the AI lives.

## Project files
- `hotel_ai_assignment.ipynb` – full notebook (steps 1–8)
- `app.py` – Streamlit web app
- `model.joblib` – trained pipeline (preprocessing + Random Forest)
- `metrics.json` – evaluation metrics and app configuration
- `requirements.txt` – Python dependencies
- `.streamlit/config.toml` – app theme

## Run locally
```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Author
Muhammad Shahmir Khan
