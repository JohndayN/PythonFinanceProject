import React, { useState } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import FraudDetection from './pages/FraudDetection';
import AnomalyDetection from './pages/AnomalyDetection';
import PortfolioOptimizer from './pages/PortfolioOptimizer';
import MarketPrediction from './pages/MarketPrediction';
import MarketScraper from './pages/MarketScraper';

function App() {
	return (
		<Router>
			<div className="App">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/fraud-detection" element={<FraudDetection />} />
            <Route path="/anomaly-detection" element={<AnomalyDetection />} />
            <Route path="/portfolio-optimizer" element={<PortfolioOptimizer />} />
            <Route path="/market-prediction" element={<MarketPrediction />} />
            <Route path="/market-scraper" element={<MarketScraper />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
