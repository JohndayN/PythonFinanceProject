import torch
import torch.nn as nn


class Attention(nn.Module):

    def __init__(self, hidden_size):
        super().__init__()

        self.attn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, lstm_output):

        attn_weights = torch.softmax(self.attn(lstm_output), dim=1)

        context = torch.sum(attn_weights * lstm_output, dim=1)

        return context


class LSTMModel(nn.Module):

    def __init__(self, input_size=5, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )

        self.attention = Attention(hidden_size)

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):

        lstm_out, _ = self.lstm(x)

        context = self.attention(lstm_out)

        output = self.fc(context)

        return output