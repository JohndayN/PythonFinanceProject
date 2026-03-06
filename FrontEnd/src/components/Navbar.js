import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
	const [isOpen, setIsOpen] = useState(false);

	return (
		<nav className="navbar">
            <div className="nav-container">
            <Link to="/" className="nav-logo">Finance Webapp Project</Link>
            <button className="hamburger"onClick={() => setIsOpen(!isOpen)}>☰</button>
            <ul className={`nav-menu ${isOpen ? 'active' : ''}`}>
                <li><Link to="/" className="nav-link">Dashboard</Link></li>
                <li><Link to="/fraud-detection" className="nav-link">Fraud Detection</Link></li>
                <li><Link to="/anomaly-detection" className="nav-link">Anomaly Detection</Link></li>
                <li><Link to="/portfolio-optimizer" className="nav-link">Portfolio</Link></li>
                <li><Link to="/market-prediction" className="nav-link">Prediction</Link></li>
                <li><Link to="/market-scraper" className="nav-link">Market Data</Link></li>
            </ul>
            </div>
        </nav>
    );
}

export default Navbar;
