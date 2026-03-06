# Vietnam Finance Platform - React Frontend

A modern React-based web interface for the Vietnam Finance Platform, featuring fraud detection, anomaly detection, portfolio optimization, and market prediction modules.

## Features

- **Fraud Detection**: Upload and analyze financial data for fraudulent activity
- **Anomaly Detection**: Detect unusual patterns in Vietnamese stock market data
- **Portfolio Optimizer**: Optimize investment portfolios for better returns
- **Market Prediction**: Predict future stock prices using LSTM models
- **Real-time Dashboard**: Monitor system status and key metrics

## Setup

### Prerequisites
- Node.js 16+ and npm
- Python backend running on `http://localhost:8000`
- Node.js API gateway (optional) on `http://localhost:3000`

### Installation

```bash
npm install
```

### Configuration

The frontend uses environment variables defined in `.env`:
- `REACT_APP_API_URL`: Python FastAPI backend URL (default: http://localhost:8000)
- `REACT_APP_NODE_API_URL`: Node.js API gateway URL (default: http://localhost:3000)

### Running

```bash
npm start
```

The application will start on `http://localhost:3001` and automatically open in your browser.

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Project Structure

```
FrontEnd/
├── public/           # Static files
├── src/
│   ├── components/   # Reusable React components
│   ├── pages/        # Page components for each feature
│   ├── App.js        # Main app component
│   ├── index.js      # React entry point
│   └── index.css     # Global styles
├── package.json      # Dependencies and scripts
└── .env             # Environment configuration
```

## API Integration

The frontend communicates with the Python FastAPI backend through HTTP REST calls:

- `GET /api/health` - Health check
- `POST /api/fraud/detect` - Fraud detection analysis
- `GET /api/anomaly/detect` - Anomaly detection
- `GET /api/portfolio/optimize` - Portfolio optimization
- `GET /api/prediction/predict` - Market price prediction

See the backend documentation at `http://localhost:8000/docs` for full API details.

## Technologies Used

- **React 18**: Frontend framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls
- **Chart.js & react-chartjs-2**: Data visualization
- **Tailwind CSS**: Utility-first CSS framework
- **React Icons**: Icon library

## Troubleshooting

### Port 3001 already in use
```bash
kill -9 $(lsof -t -i :3001)
# or on Windows
netstat -ano | findstr :3001
taskkill /PID <PID> /F
```

### CORS errors
Make sure the backend has CORS enabled and the `REACT_APP_API_URL` is correctly set.

### Modules not installed
```bash
rm -rf node_modules package-lock.json
npm install
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License
