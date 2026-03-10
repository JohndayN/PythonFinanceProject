const mongoose = require("mongoose");

exports.getTickerTrend = async (req, res) => {
    const db = mongoose.connection.db;

    const data = await db.collection("risk_trend_analysis")
        .find({ ticker: req.params.ticker })
        .sort({ time: 1 })
        .toArray();

    res.json(data);
};

exports.getTickerRisk = async (req, res) => {
    try {
        const db = mongoose.connection.db;

        const data = await db.collection("risk_trend_analysis")
            .find({ ticker: req.params.ticker })
            .sort({ time: 1 })
            .toArray();

        res.json(data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Database error" });
    }
};