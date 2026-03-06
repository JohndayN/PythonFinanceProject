const mongoose = require("mongoose");

exports.getAllTickers = async (req, res) => {
    const db = mongoose.connection.db;

    const data = await db.collection("hybrid_fraud_scores")
        .aggregate([
            {
                $group: {
                    _id: "$ticker",
                    latest_score: { $last: "$final_fraud_score" },
                    risk_level: { $last: "$risk_level" }
                }
            }
        ])
        .toArray();

    res.json(data);
};

exports.getTickerRisk = async (req, res) => {
    const db = mongoose.connection.db;

    const data = await db.collection("hybrid_fraud_scores")
        .find({ ticker: req.params.ticker })
        .sort({ time: 1 })
        .toArray();

    res.json(data);
};