# core/models.py
import torch
import torch.nn as nn
import numpy as np

class VolatilityLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=32):
        super(VolatilityLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])

def get_nn_adjusted_volatility(historical_vol, returns_tensor):
    """
    Koryguje zmienność historyczną za pomocą sieci LSTM.
    Jeśli model zawiedzie, zwraca bezpiecznie zmienność historyczną.
    """
    try:
        model = VolatilityLSTM()
        # W prawdziwym projekcie tutaj ładowalibyśmy model: model.load_state_dict(...)
        
        with torch.no_grad():
            # Uproszczona korekta AI dla celów demonstracyjnych
            # (Sieć neuronowa analizuje wzorce i dodaje 'risk premium')
            ai_adjustment = model(returns_tensor).item()
            adjusted_vol = historical_vol * (1 + abs(ai_adjustment) * 0.1)
            return float(adjusted_vol)
    except Exception as e:
        print(f"[AI ERROR] Fallback to historical volatility: {e}")
        return float(historical_vol)