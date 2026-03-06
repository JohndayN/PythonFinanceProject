const express = require("express");
const router = express.Router();
const { getTickerRisk, getAllTickers } = require("../controllers/RiskController");

router.get("/", getAllTickers);
router.get("/:ticker", getTickerRisk);

module.exports = router;