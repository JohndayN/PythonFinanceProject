const express = require("express");
const router = express.Router();
const { getTickerTrend } = require("../controllers/TrendController");

router.get("/:ticker", getTickerTrend);

module.exports = router;