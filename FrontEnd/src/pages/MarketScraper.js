import React, { useState, useEffect } from 'react';
import './Pages.css';
import './MarketScraper.css';

const MarketScraper = () => {
	const [ticker, setTicker] = useState('VCB');
	const [tickerInput, setTickerInput] = useState('VCB');
	const [filteredTickers, setFilteredTickers] = useState([]);
	const [showSuggestions, setShowSuggestions] = useState(false);
	const [startDate, setStartDate] = useState('2023-01-01');
	const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
	const [loading, setLoading] = useState(false);
	const [data, setData] = useState(null);
	const [error, setError] = useState(null);
	const [availableTickers, setAvailableTickers] = useState([]);
	const [hoseData, setHoseData] = useState(null);
	const [newsData, setNewsData] = useState(null);
	const [activeTab, setActiveTab] = useState('single');
	const [currentPage, setCurrentPage] = useState(1);
	const [scheduleInterval, setScheduleInterval] = useState('');
	const [scheduledTasks, setScheduledTasks] = useState([]);
	const itemsPerPage = 15;

	// helper to persist scheduled tasks to localStorage
	const saveScheduledTasks = (tasks) => {
		try {
			localStorage.setItem('scheduledTasks', JSON.stringify(tasks));
		} catch (e) {
			console.warn('Unable to save tasks to localStorage', e);
		}
	};

	const loadScheduledTasks = () => {
		try {
			const stored = localStorage.getItem('scheduledTasks');
			if (stored) {
				return JSON.parse(stored);
			}
		} catch (e) {
			console.warn('Unable to load tasks from localStorage', e);
		}
		return [];
	};

	// Fetch available tickers on mount
	useEffect(() => {
		fetchAvailableTickers();
		// restore any saved scheduled tasks
		const saved = loadScheduledTasks();
		if (saved && Array.isArray(saved)) {
			setScheduledTasks(saved);
		}
	}, []);

	const fetchAvailableTickers = async () => {
		try {
			const response = await fetch('http://localhost:8000/api/data/available-tickers');
			if (response.ok) {
				const result = await response.json();
				setAvailableTickers(result.tickers || ['VCB', 'GAS', 'HPG', 'MSN', 'MWG', 'VNM']);
			}
		} catch (err) {
			console.error('Error fetching tickers:', err);
			setAvailableTickers(['VCB', 'GAS', 'HPG', 'MSN', 'MWG', 'VNM']);
		}
	};

	const handleTickerInputChange = (value) => {
		const upperValue = value.toUpperCase();
		setTickerInput(upperValue);
		
		if (upperValue.length > 0) {
			const filtered = availableTickers.filter(t => 
				t.includes(upperValue)
			);
			setFilteredTickers(filtered);
			setShowSuggestions(true);
		} else {
			setFilteredTickers([]);
			setShowSuggestions(false);
		}
	};

	const handleTickerSelect = (selectedTicker) => {
		setTickerInput(selectedTicker);
		setTicker(selectedTicker);
		setShowSuggestions(false);
	};

	const fetchMarketData = async (e) => {
		e.preventDefault();
		setLoading(true);
		setError(null);
		setData(null);

		try {
			// Check if backend is available
			const healthCheck = await fetch('http://localhost:8000/api/health', {
				method: 'GET',
				headers: { 'Accept': 'application/json' }
			}).catch(() => null);

			if (!healthCheck) {
				setError('Backend server is not running. Please start the Python backend (run: python run.py)');
				setLoading(false);
				return;
			}

			const response = await fetch('http://localhost:8000/api/scraper/market-data', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Accept': 'application/json'
				},
				body: JSON.stringify({
					ticker: tickerInput.toUpperCase(),
					start_date: startDate,
					end_date: endDate,
				}),
			});

			if (!response.ok) {
				let errorData = {};
				try {
					errorData = await response.json();
				} catch (e) {
					console.log('Could not parse error response');
				}
				throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch market data`);
			}

			const result = await response.json();
			
			// Check if data is empty
			if (!result.data || (!result.data.dates || result.data.dates.length === 0)) {
				setError(`No data available for ${tickerInput} in the selected date range. Try a different date range or stock.`);
				return;
			}
			
			setData(result);
		} catch (err) {
			const errorMsg = err.message || 'Failed to fetch market data. Please check the backend connection.';
			setError(errorMsg);
			console.error('Market Data Fetch Error:', err);
		} finally {
			setLoading(false);
		}
	};

	const addScheduledTask = () => {
		if (!tickerInput || !scheduleInterval) {
			setError('Please select a ticker and schedule interval');
			return;
		}

		const newTask = {
			id: Date.now(),
			ticker: tickerInput,
			interval: scheduleInterval,
			addedAt: new Date().toLocaleString(),
		};

		const updatedTasks = [...scheduledTasks, newTask];
		setScheduledTasks(updatedTasks);
		saveScheduledTasks(updatedTasks);
		setScheduleInterval('');
		setError(null);
	};

	const removeScheduledTask = (taskId) => {
		const updatedTasks = scheduledTasks.filter(task => task.id !== taskId);
		setScheduledTasks(updatedTasks);
		saveScheduledTasks(updatedTasks);
	};

	const fetchCompanyNews = async () => {
		setLoading(true);
		setError(null);
		setNewsData(null);

		try {
			// Check if backend is available
			const healthCheck = await fetch('http://localhost:8000/api/health', {
				method: 'GET',
				headers: { 'Accept': 'application/json' }
			}).catch(() => null);

			if (!healthCheck) {
				setError('Backend server is not running. Please start the Python backend (run: python run.py)');
				setLoading(false);
				return;
			}

			// Fetch latest HOSE market news
			const response = await fetch('http://localhost:8000/api/scraper/company-news', {
				method: 'GET',
				headers: { 
					'Accept': 'application/json',
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				let errorData = {};
				try {
					errorData = await response.json();
				} catch (e) {
					console.log('Could not parse error response');
				}
				throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch news data`);
			}

			const result = await response.json();
			setNewsData(result.data || result);
		} catch (err) {
			const errorMsg = err.message || 'Failed to fetch company news. Please check the backend connection.';
			setError(errorMsg);
			console.error('News Data Fetch Error:', err);
		} finally {
			setLoading(false);
		}
	};

	const fetchHOSEData = async () => {
		setLoading(true);
		setError(null);
		setHoseData(null);
		setCurrentPage(1);

		try {
			// First check if backend is available
			const healthCheck = await fetch('http://localhost:8000/api/health', {
				method: 'GET',
				headers: { 'Accept': 'application/json' }
			}).catch(() => null);

			if (!healthCheck) {
				setError('Backend server is not running. Please start the Python backend (run: python run.py)');
				setLoading(false);
				return;
			}

			const response = await fetch('http://localhost:8000/api/scraper/hose-market', {
				method: 'GET',
				headers: { 
					'Accept': 'application/json',
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				let errorMessage = '';
				try {
					const errorData = await response.json();
					errorMessage = errorData.detail || `HTTP ${response.status}: Failed to fetch HOSE market data`;
				} catch {
					errorMessage = `HTTP ${response.status}: Failed to fetch HOSE market data`;
				}
				throw new Error(errorMessage);
			}

			const result = await response.json();
			
			// Filter and process the data
			if (result.data && result.data.length > 0) {
				const filtered = result.data.map(stock => {
					// Handle both API field names and the fields returned by GetHOSEMarketData
					const symbol = stock.symbol || stock.securitySymbol || 'N/A';
					const name = stock.name || stock.company || 'N/A';
					const price = parseFloat(stock.price || stock.close || 0);
					const change = parseFloat(stock.pct_change || stock.change || 0);
					const volume = parseFloat(stock.volume || 0);
					const open = stock.open && stock.open !== 'N/A' ? parseFloat(stock.open) : null;
					const high = stock.high && stock.high !== 'N/A' ? parseFloat(stock.high) : null;
					const low = stock.low && stock.low !== 'N/A' ? parseFloat(stock.low) : null;
					
					return {
						securitySymbol: symbol,
						name: name,
						price: price,
						change: change,
						volume: volume,
						open: open,
						high: high,
						low: low,
					};
				});
				
				setHoseData({
					...result,
					data: filtered
				});
			} else if (result.status === 'no_data' || result.count === 0) {
				setError(result.message || 'No HOSE market data available. The market API may be unavailable. Please try again later.');
			} else {
				setHoseData(result);
			}
		} catch (err) {
			const errorMsg = err.message || 'Failed to fetch HOSE data. Please check the backend connection.';
			setError(errorMsg);
			console.error('HOSE Data Fetch Error:', err);
		} finally {
			setLoading(false);
		}
	};

	const downloadCSV = () => {
		if (!data || !data.data) return;

		const headers = ['Date', 'Close', 'Volume'];
		const rows = [];

		if (data.data.dates && data.data.close && data.data.volume) {
			data.data.dates.forEach((date, index) => {
				rows.push([
					date,
					data.data.close[index]?.toFixed(2) || '',
					data.data.volume[index] || '',
				]);
			});
		}

		const csvContent = [
			headers.join(','),
			...rows.map(row => row.join(',')),
		].join('\n');

		const blob = new Blob([csvContent], { type: 'text/csv' });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${tickerInput}-${startDate}-${endDate}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	};

	// Pagination logic for HOSE data
	const getPaginatedData = () => {
		if (!hoseData || !hoseData.data) return { data: [], totalPages: 0 };
		
		const startIdx = (currentPage - 1) * itemsPerPage;
		const endIdx = startIdx + itemsPerPage;
		const paginatedData = hoseData.data.slice(startIdx, endIdx);
		const totalPages = Math.ceil(hoseData.data.length / itemsPerPage);
		
		return { data: paginatedData, totalPages };
	};

	return (
		<div className="page-container">
			<div className="scraper-tabs">
				<button
					className={`tab-button ${activeTab === 'single' ? 'active' : ''}`}
					onClick={() => setActiveTab('single')}
				>
					Single Stock
				</button>
				<button
					className={`tab-button ${activeTab === 'hose' ? 'active' : ''}`}
					onClick={() => setActiveTab('hose')}
				>
					HOSE Market
				</button>
			<button
				className={`tab-button ${activeTab === 'news' ? 'active' : ''}`}
				onClick={() => setActiveTab('news')}
			>
				Company News
			</button>
		</div>

		{activeTab === 'single' && (
			<div className="scraper-content">
				<div className="form-card">
					<h2>Fetch Stock Data</h2>
					<form onSubmit={fetchMarketData}>
						<div className="form-group">
							<label htmlFor="ticker">Stock Ticker</label>
							<div className="autocomplete-container">
								<input
									id="ticker"
									type="text"
									placeholder="Enter stock ticker (e.g., VCB, GAS, HPG)"
									value={tickerInput}
									onChange={(e) => handleTickerInputChange(e.target.value)}
									onFocus={() => tickerInput && setShowSuggestions(true)}
									className="form-input autocomplete-input"
								/>
								{showSuggestions && filteredTickers.length > 0 && (
									<ul className="autocomplete-suggestions">
										{filteredTickers.map((t) => (
											<li 
												key={t} 
												onClick={() => handleTickerSelect(t)}
												className="suggestion-item"
											>
												{t}
											</li>
										))}
									</ul>
								)}
							</div>
						</div>

						<div className="form-row">
							<div className="form-group">
								<label htmlFor="startDate">Start Date</label>
								<input
									id="startDate"
									type="date"
									value={startDate}
									onChange={(e) => setStartDate(e.target.value)}
									className="form-input"
								/>
							</div>

							<div className="form-group">
								<label htmlFor="endDate">End Date</label>
								<input
									id="endDate"
									type="date"
									value={endDate}
									onChange={(e) => setEndDate(e.target.value)}
									className="form-input"
								/>
							</div>
						</div>

						<button type="submit" disabled={loading} className="submit-button">
							{loading ? 'Fetching...' : 'Fetch Market Data'}
						</button>
					</form>

					<div className="schedule-section">
						<h3>Schedule Scraper</h3>
						<div className="schedule-form">
							<div className="form-group">
								<label htmlFor="scheduleInterval">Repeat Every</label>
								<select
									id="scheduleInterval"
									value={scheduleInterval}
									onChange={(e) => setScheduleInterval(e.target.value)}
									className="form-input"
								>
									<option value="">Select interval...</option>
									<option value="hourly">Hourly</option>
									<option value="daily">Daily</option>
									<option value="weekly">Weekly</option>
								</select>
							</div>
							<button 
								type="button" 
								onClick={addScheduledTask}
								className="schedule-button"
							>
								+ Schedule Task
							</button>
						</div>

						{scheduledTasks.length > 0 && (
							<div className="scheduled-tasks">
								<h4>Scheduled Tasks</h4>
								<ul className="task-list">
									{scheduledTasks.map(task => (
										<li key={task.id} className="task-item">
											<div className="task-info">
												<strong>{task.ticker}</strong>
												<span className="task-interval">{task.interval}</span>
												<span className="task-time">{task.addedAt}</span>
											</div>
											<button
												type="button"
												onClick={() => removeScheduledTask(task.id)}
												className="remove-button"
											>
												✕
											</button>
										</li>
									))}
								</ul>
							</div>
						)}
					</div>
				</div>

				{error && (
					<div className="error-card">
						<h3>Error</h3>
						<p>{error}</p>
					</div>
				)}

				{data && (
					<div className="results-card">
						<div className="results-header">
							<h2>{tickerInput} Market Data</h2>
							<button onClick={downloadCSV} className="download-button">
								Download CSV
							</button>
						</div>

						<div className="data-summary">
							<div className="summary-item">
								<span>Data Points</span>
								<strong>{data.data.dates?.length || 0}</strong>
							</div>
							<div className="summary-item">
								<span>Date Range</span>
								<strong>
									{data.data.dates?.[0]} to {data.data.dates?.[data.data.dates.length - 1]}
								</strong>
							</div>
							<div className="summary-item">
								<span>Latest Close</span>
								<strong>
									{data.data.close?.[data.data.close.length - 1]?.toFixed(2)}
								</strong>
							</div>
						</div>

						<div className="data-table-container">
							<table className="data-table">
								<thead>
									<tr>
										<th>Date</th>
										<th>Close Price</th>
										<th>Volume</th>
									</tr>
								</thead>
								<tbody>
									{data.data.dates?.map((date, index) => (
										<tr key={index}>
											<td>{date}</td>
											<td>{data.data.close?.[index]?.toFixed(2)}</td>
											<td>{data.data.volume?.[index]?.toLocaleString()}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</div>
				)}
			</div>
		)}

			{activeTab === 'hose' && (
				<div className="scraper-content">
					<div className="form-card">
						<h2>HOSE Market Overview</h2>
						<p>View current HOSE market data for all listed stocks</p>
						<button onClick={fetchHOSEData} disabled={loading} className="submit-button">
							{loading ? 'Fetching...' : 'Load HOSE Market Data'}
						</button>
					</div>

					{error && (
						<div className="error-card">
							<h3>Error</h3>
							<p>{error}</p>
						</div>
					)}

					{hoseData && (
						<div className="results-card">
							<div className="results-header">
								<h2>HOSE Market Data</h2>
								<span className="data-count">
									Showing {getPaginatedData().data.length} of {hoseData.data?.length || 0} stocks
								</span>
							</div>

							<div className="data-table-container">
								<table className="data-table">
									<thead>
										<tr>
											<th>Ticker</th>
											<th>Name</th>
											<th>Price</th>
											<th>Change %</th>
											<th>Volume</th>
											<th>Open</th>
											<th>High</th>
											<th>Low</th>
										</tr>
									</thead>
									<tbody>
										{getPaginatedData().data.map((stock, index) => (
											<tr key={index}>
												<td className="ticker-cell">
													<strong>{stock.securitySymbol}</strong>
												</td>
												<td>{stock.name}</td>
												<td>{typeof stock.price === 'number' ? stock.price.toFixed(2) : 'N/A'}</td>
												<td className={`change-cell ${stock.change >= 0 ? 'positive' : 'negative'}`}>
													{typeof stock.change === 'number' ? stock.change.toFixed(2) : '0.00'}%
												</td>
												<td>{(stock.volume || 0).toLocaleString()}</td>
												<td>{stock.open !== null && stock.open !== undefined ? stock.open.toFixed(2) : 'N/A'}</td>
												<td>{stock.high !== null && stock.high !== undefined ? stock.high.toFixed(2) : 'N/A'}</td>
												<td>{stock.low !== null && stock.low !== undefined ? stock.low.toFixed(2) : 'N/A'}</td>
											</tr>
										))}
									</tbody>
								</table>
							</div>

							{/* Pagination Controls */}
							{getPaginatedData().totalPages > 1 && (
								<div className="pagination">
									<button
										className="pagination-btn"
										onClick={() => setCurrentPage(1)}
										disabled={currentPage === 1}
									>
										First
									</button>
									<button
										className="pagination-btn"
										onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
										disabled={currentPage === 1}
									>
										Previous
									</button>
									<span className="pagination-info">
										Page {currentPage} of {getPaginatedData().totalPages}
									</span>
									<button
										className="pagination-btn"
										onClick={() => setCurrentPage(Math.min(getPaginatedData().totalPages, currentPage + 1))}
										disabled={currentPage === getPaginatedData().totalPages}
									>
										Next
									</button>
									<button
										className="pagination-btn"
										onClick={() => setCurrentPage(getPaginatedData().totalPages)}
										disabled={currentPage === getPaginatedData().totalPages}
									>
										Last
									</button>
								</div>
							)}
						</div>
					)}
				</div>
			)}

			{activeTab === 'news' && (
				<div className="scraper-content">
					<div className="form-card">
						<h2>Company News & Sentiment</h2>
						<p>Get latest HOSE market news and sentiment analysis</p>
						
						<button
							onClick={fetchCompanyNews}
							disabled={loading}
							className="submit-button"
						>
							{loading ? "Fetching..." : "Load Company News"}
						</button>

					{error && (
						<div className="error-card">
							<h3>Error</h3>
							<p>{error}</p>
						</div>
					)}

					{newsData && (
						<div className="results-card">
							<div className="results-header">
							<h2>HOSE Market News</h2>
						</div>

							{(newsData.fraud_pressure_score !== undefined || newsData.average_sentiment !== undefined) && (
								<div className="news-metrics-summary">
									<h3>Overall Market Sentiment</h3>
									<div className="metrics-container">
										{newsData.fraud_pressure_score !== undefined && (
											<div className="metric-box">
												<label>Fraud Pressure Score:</label>
												<span className={`metric-value ${newsData.fraud_pressure_score > 0.5 ? 'high-risk' : 'low-risk'}`}>
													{newsData.fraud_pressure_score.toFixed(2)}
												</span>
											</div>
										)}
										{newsData.average_sentiment !== undefined && (
											<div className="metric-box">
												<label>Average Sentiment:</label>
												<span className={`metric-value ${newsData.average_sentiment < 0 ? 'negative' : newsData.average_sentiment > 0 ? 'positive' : 'neutral'}`}>
													{newsData.average_sentiment.toFixed(2)}
												</span>
											</div>
										)}
										{newsData.average_risk_level && (
											<div className="metric-box">
												<label>Average Risk Level:</label>
												<span className="metric-value">{newsData.average_risk_level}</span>
											</div>
										)}
									</div>
								</div>
							)}

							{(newsData.news_articles && newsData.news_articles.length > 0) || (newsData.news && newsData.news.length > 0) ? (
								<div className="news-list">
									{(newsData.news_articles || newsData.news || []).map((article, index) => (
										<div key={index} className="news-item">
											<div className="news-header">
												<h3>{article.title || 'News Item'}</h3>
												{article.date && <span className="news-date">{article.date}</span>}
											</div>
											{article.content && <p className="news-content">{article.content}</p>}
											{article.risk_level && <p className="risk-level"><strong>Risk Level:</strong> {article.risk_level}</p>}
											{article.pressure_signals && article.pressure_signals.length > 0 && (
												<div className="news-keywords">
													<strong>Pressure Signals:</strong>
													{article.pressure_signals.map((signal, idx) => (
														<span key={idx} className="keyword-tag">{signal}</span>
													))}
												</div>
											)}
											{article.opportunity_signals && article.opportunity_signals.length > 0 && (
												<div className="news-keywords">
													<strong>Opportunity Signals:</strong>
													{article.opportunity_signals.map((signal, idx) => (
														<span key={idx} className="keyword-tag">{signal}</span>
													))}
												</div>
											)}
											{article.sentiment !== undefined && (
												<div className="news-sentiment">
													<span className="sentiment-label">Sentiment:</span>
													<span className={`sentiment-score ${article.sentiment < 0 ? 'sentiment-negative' : article.sentiment > 0 ? 'sentiment-positive' : 'sentiment-neutral'}`}>
														{article.sentiment?.toFixed(2)}
													</span>
												</div>
											)}
											{article.attachments && article.attachments.length > 0 && (
												<div className="news-attachments">
													<strong>Attachments:</strong>
													<div className="attachment-list">
														{article.attachments.map((attachment, attachIdx) => (
															<a
																key={attachIdx}
																href={attachment.url}
																download={attachment.name}
																target="_blank"
																rel="noopener noreferrer"
																className="attachment-link"
																title={`Download ${attachment.name}`}
															>
																{attachment.name}
															</a>
														))}
													</div>
												</div>
											)}
										</div>
									))}
								</div>
							) : (
								<p className="no-data">No news data available</p>
							)}

							{newsData.summary && (
								<div className="news-summary">
									<h3>Analysis Summary</h3>
									<p>{newsData.summary}</p>
								</div>
							)}
						</div>
					)}
				</div>
			)}
		</div>
	)}		
	</div>
);
};

export default MarketScraper;
