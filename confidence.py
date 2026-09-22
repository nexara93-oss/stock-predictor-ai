import numpy as np

def calculate_confidence(model, X_val, y_val, predictions, recent_errors=None):
    confidence = 50.0
    try:
        y_pred_val = model.predict(X_val)
        y_val = np.array(y_val)
        y_pred_val = np.array(y_pred_val)
        y_val_mean = np.mean(y_val)
        ss_res = np.sum((y_val - y_pred_val) ** 2)
        ss_tot = np.sum((y_val - y_val_mean) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        r2_conf = max(30, min(95, (r2 + 1) * 40 + 20))
        val_std = np.std(y_val)
        if val_std > 0:
            predictions_vs_actuals = np.abs(y_pred_val - y_val) / val_std
            pred_quality = np.mean(predictions_vs_actuals < 1) * 50
        else:
            pred_quality = 50
        direction_correct = np.mean((y_pred_val > 0) == (y_val > 0)) * 30
        model_size_conf = min(model.n_estimators / 500 * 10, 10)
        confidence = r2_conf * 0.3 + pred_quality * 0.3 + direction_correct * 0.3 + model_size_conf
    except:
        confidence = 50.0
    if recent_errors and len(recent_errors) > 0:
        recent_mape = np.mean([abs(e) for e in recent_errors])
        rec_conf = max(0, min(100, (1 - recent_mape) * 100))
        confidence = confidence * 0.7 + rec_conf * 0.3
    volatility = np.std(y_val) / abs(np.mean(y_val)) if np.mean(y_val) != 0 else 0
    if volatility > 0.02:
        confidence *= max(0.7, 1 - volatility * 2)
    return round(min(max(confidence, 15), 90), 1)

def get_prediction_signal(confidence, prediction_change):
    if confidence >= 65 and prediction_change > 2:
        return "شراء قوي", "strong_buy"
    if confidence >= 50 and prediction_change > 0.5:
        return "شراء", "buy"
    if confidence >= 65 and prediction_change < -2:
        return "بيع قوي", "strong_sell"
    if confidence >= 50 and prediction_change < -0.5:
        return "بيع", "sell"
    return "محايد", "neutral"
