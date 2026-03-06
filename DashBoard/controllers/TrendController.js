const mongoose = require("mongoose");

exports.getTickerTrend = async (req, res) => {
    const db = mongoose.connection.db;

    const data = await db.collection("risk_trend_analysis")
        .find({ ticker: req.params.ticker })
        .sort({ time: 1 })
        .toArray();

    res.json(data);
};