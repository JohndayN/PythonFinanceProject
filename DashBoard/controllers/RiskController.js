const mongoose = require("mongoose");

exports.getAllTickers = async (req, res) => {
    const db = mongoose.connection.db;

    const data = await db.collection("hybrid_fraud_scores")
        .aggregate([
            { $sort: {time: -1}},
            {
                $group: {
                    _id: "$ticker",
                    latest_score: { $first: "$final_fraud_score" },
                    risk_level: { $first: "$risk_level" }
                }
            }
        ])
        .toArray();

    res.json(data);
};

exports.getTickerRisk = async (req, res) => {
    try {
        const db = mongoose.connection.db;

        const data = await db.collection("hybrid_fraud_scores")
            .find({ ticker: req.params.ticker })
            .sort({ time: 1 })
            .toArray();

        res.json(data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: "Database error" });
    }
};