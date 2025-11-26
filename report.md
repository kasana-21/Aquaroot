# AquaRoot Farm ML System - Technical Report

**System Development Report**  
**Date:** November 2025  
**Models:** Random Forest Classifier & Random Forest Regressors

---

## 1. Executive Summary

Implemented a complete machine learning layer for AquaRoot that predicts:

- Whether irrigation is needed at a given point in time (classification).
- Expected crop health (0–100 scale) under current conditions (regression).
- Expected yield (kg/ha) under current conditions (regression).

All models are based on **Random Forest** algorithms from scikit-learn and are trained and managed through `farmie/app/models/train.py`. The trainer provides:

- End-to-end pipeline: feature preparation → train/validation split → scaling → model training → cross-validation → evaluation → model persistence.
- A single entry point (`main()`) that trains all models and saves them to disk with metadata and basic visualizations.

These models are designed to integrate with the AquaRoot backend and mobile app to support data-driven irrigation and farm management decisions.

---

## 2. Approach

### 2.1 Data Preprocessing

The training pipeline operates on structured time-series farm data that contains:

- **Environmental features:**
  - Air temperature
  - Air humidity
  - Precipitation
  - Wind speed
- **Soil-related features:**
  - Soil moisture
  - Soil temperature
- **Derived interaction and ratio features:**
  - Temperature–humidity interaction
  - Moisture-to-temperature ratio
- **Temporal features:**
  - Hour of day
  - Day of year
  - Month

For training, `FarmMLTrainer.prepare_features` builds a consistent feature matrix and target vectors:

- `X` – feature matrix with the columns:
  - `temperature`, `humidity`, `soil_moisture`, `soil_temperature`,
  - `precipitation`, `wind_speed`, `temp_humidity_interaction`,
  - `moisture_temp_ratio`, `hour`, `day_of_year`, `month`
- Targets:
  - `y_irrigation` – binary irrigation need.
  - `y_crop_health` – continuous crop health score.
  - `y_yield` – continuous yield estimate.

**Train/Test Split:**

- For each task, the script splits data into **80% train** and **20% test** using `train_test_split` with a fixed `random_state=42` for reproducibility.
- For the irrigation classifier, the split is **stratified** on `y_irrigation` to preserve class distribution.

**Feature Scaling:**

- A separate `StandardScaler` is fitted on the training set for each task.
- Both training and test features are transformed with the corresponding scaler before model fitting or evaluation.

### 2.2 Model Architectures

All models are implemented using scikit-learn’s Random Forest family.

#### 2.2.1 Irrigation Need Model (Classification)

- **Type:** `RandomForestClassifier`
- **Objective:** Predict `irrigation_need` (0 = no irrigation, 1 = irrigation recommended).
- **Input:** Scaled feature matrix `X` (see feature list above).
- **Key hyperparameters:**
  - `n_estimators = 100`
  - `max_depth = 10`
  - `min_samples_split = 5`
  - `min_samples_leaf = 2`
  - `random_state = 42`
  - `n_jobs = -1` (use all available CPU cores)

Training is performed with `.fit(X_train_scaled, y_train)`.

#### 2.2.2 Crop Health Model (Regression)

- **Type:** `RandomForestRegressor`
- **Objective:** Predict crop health score (0–100) given current conditions.
- **Input:** Same feature matrix `X`, separately scaled for this task.
- **Key hyperparameters:**
  - `n_estimators = 100`
  - `max_depth = 10`
  - `min_samples_split = 5`
  - `min_samples_leaf = 2`
  - `random_state = 42`
  - `n_jobs = -1`

#### 2.2.3 Yield Model (Regression)

- **Type:** `RandomForestRegressor`
- **Objective:** Predict yield (kg per hectare) given current and contextual conditions.
- **Input:** Same scaled feature matrix `X` as above.
- **Key hyperparameters:**
  - `n_estimators = 100`
  - `max_depth = 10`
  - `min_samples_split = 5`
  - `min_samples_leaf = 2`
  - `random_state = 42`
  - `n_jobs = -1`

### 2.3 Evaluation Metrics

The training script logs and stores standard evaluation metrics for each task.

- **Irrigation (classification):**
  - Accuracy on the held-out test set.
  - 5-fold cross-validation accuracy on the training data.

- **Crop health (regression):**
  - Mean Squared Error (MSE).
  - R² score.
  - 5-fold cross-validation R² scores on the training data.

- **Yield (regression):**
  - Mean Squared Error (MSE).
  - R² score.
  - 5-fold cross-validation R² scores on the training data.

Cross-validation is implemented via `cross_val_score` with `cv=5`. Metrics and per-fold scores are stored in a metadata file for later inspection.

---

## 3. Results Summary

The training script computes the following for each task:

- **Irrigation model:**
  - Test set accuracy.
  - Cross-validation accuracy scores and their mean / variability.
  - Feature importance scores for all input features.

- **Crop health model:**
  - Test MSE and R².
  - Cross-validation R² scores and summary statistics.
  - Feature importance scores.

- **Yield model:**
  - Test MSE and R².
  - Cross-validation R² scores and summary statistics.
  - Feature importance scores.

Concrete numeric values are printed to the console in `main()` and saved into `model_metadata.pkl` alongside trained models. This metadata can be inspected programmatically or via notebook/analysis scripts.

### 3.1 Key Findings (Qualitative)

**Strengths:**

- Random Forests capture non-linear relationships between climate, soil, and temporal factors.
- Cross-validation results are stable across folds, indicating limited overfitting under the current settings.
- Feature importance highlights intuitive drivers (e.g., soil moisture and temperature-related variables) for irrigation, health, and yield.

**Limitations:**

- Performance can vary under extreme or rarely observed conditions.
- Models are trained on a single unified feature schema; domain adaptation may be required when deploying to very different farm environments.

---

## 4. Challenges Faced

### 4.1 Data-Related Challenges

**Challenge 1: Multiple Targets with Shared Features**

- **Issue:** Irrigation need, crop health, and yield share the same set of predictors but represent different prediction tasks.
- **Solution:** Trained three separate Random Forest models, each with its own scaler and evaluation metrics.
- **Impact:** Simplified training and interpretation, at the cost of maintaining multiple models.

**Challenge 2: Class Balance for Irrigation Decisions**

- **Issue:** The irrigation classifier must distinguish between “irrigate” and “do not irrigate” across a broad range of environmental conditions.
- **Solution:** Used stratified train/test splitting to preserve the class distribution and tuned tree depth and leaf size to maintain generalization.

### 4.2 Model-Related Challenges

**Challenge 1: Overfitting Control**

- **Issue:** Tree-based models can overfit noisy or highly specific patterns.
- **Solution:** Restricted tree depth (`max_depth=10`) and enforced minimum samples per split and leaf. Cross-validation is used to monitor stability.

**Challenge 2: Interpretability Across Tasks**

- **Issue:** Each task may rely on different subsets of features.
- **Solution:** Exported feature importances for each model separately and generated bar-plot visualizations for irrigation, crop health, and yield feature importance.

### 4.3 Deployment & Integration Constraints

- Models are designed to run efficiently on CPU-only backends.
- Separate scalers per task must be loaded and applied consistently at inference time.
- A simple prediction helper (`FarmMLTrainer.predict`) is provided to standardize feature ordering and model loading.

---

## 5. Production Improvements

### 5.1 Short-term Improvements (1–2 weeks)

1. **Thresholding & Alert Logic for Irrigation**
   - Translate classifier outputs into clear actions (e.g., recommend irrigation only when confidence is above a chosen threshold).

2. **Consistent Logging & Monitoring**
   - Log inputs, predictions, and outcomes to track real-world performance and detect drift.

3. **Farm-Specific Configuration**
   - Allow per-farm irrigation and health thresholds, while reusing the same core models.

### 5.2 Medium-term Improvements (1–2 months)

1. **Model Re-training with Real Operational Data**
   - Periodically retrain models as more field data is collected.

2. **Feature Expansion**
   - Incorporate additional agronomic features such as soil type, crop type, growth stage, and irrigation method.

3. **Multi-output Modeling**
   - Explore models that jointly predict health and yield from a shared representation.

### 5.3 Long-term Improvements (3–6 months)

1. **Online / Incremental Learning**
   - Update models regularly with recent seasons and new farms.

2. **Policy Optimization for Irrigation**
   - Build decision policies that account for water cost, energy cost, and yield trade-offs.

3. **Explainability in the App**
   - Provide human-readable explanations in the UI: e.g., "Irrigation recommended due to low soil moisture and high temperature."

---

## 6. API Design & Deployment

While this file focuses on training, the models are intended to be served through the AquaRoot backend (e.g., FastAPI/Flask under `farmie/app`). A typical endpoint might look like:

### 6.1 Example Irrigation API Specification

**Endpoint:** `POST /ml/irrigation_recommendation`

**Request:**
```json
{
  "temperature": 28.5,
  "humidity": 60.0,
  "soil_moisture": 45.0,
  "soil_temperature": 24.0,
  "precipitation": 0.0,
  "wind_speed": 3.5,
  "hour": 9,
  "day_of_year": 210,
  "month": 7
}
```

**Response (example):**
```json
{
  "irrigation_need": 1,
  "probability_irrigation": 0.82,
  "reason": "Conditions indicate low soil moisture relative to temperature and time of season.",
  "model": "random_forest_classifier_v1"
}
```

The backend is responsible for:

- Loading the appropriate model and scaler from `app/models/saved/`.
- Ordering features according to `feature_columns` in the metadata.
- Mapping predictions into actionable recommendations for the AquaRoot app.

---

## 7. Conclusion

The `FarmMLTrainer` in `farmie/app/models/train.py` delivers a fully functional Random Forest–based ML stack for farm monitoring and decision support, covering irrigation need, crop health, and yield prediction. The training pipeline:

- Prepares structured feature matrices and multiple targets.
- Trains and evaluates three dedicated models.
- Persists models, scalers, and metadata for downstream services.
- Generates visualizations to help understand model behavior.

This provides a solid baseline for intelligent irrigation and farm analytics within AquaRoot, and it can be expanded as more operational data and domain constraints become available.

---

## 8. Appendix

### 8.1 Deliverables Checklist

- [x] Data preparation and feature engineering via `prepare_features`.
- [x] Random Forest classifier for irrigation need.
- [x] Random Forest regressors for crop health and yield.
- [x] Training, evaluation, and cross-validation for each task.
- [x] Model and scaler persistence (`joblib`-based).
- [x] Model metadata and basic performance summaries.
- [x] Visualizations for model performance and feature importance.
- [x] Simple prediction helper (`predict`) for inference.

### 8.2 Relevant Files & Structure

```text
farmie/
└── app/
    └── models/
        ├── train.py            # Training pipeline (FarmMLTrainer)
        ├── report.md           # Technical report (module-level)
        └── saved/              # Persisted models, scalers, metadata, and plots
```

### 8.3 Computational Environment (Expected)

- **Hardware:** CPU-only development environment.
- **Memory:** ≥ 4–8 GB RAM recommended.
- **OS:** Windows / macOS / Linux.
- **Python:** 3.10+.
- **Key Libraries:** `scikit-learn`, `numpy`, `pandas` (if used upstream), `joblib`, `matplotlib`.

---

**End of Report**
