const mongoose = require("mongoose");

const connectDB = async () => {
    try {
        await mongoose.connect("mongodb+srv://nguyengiap211004_db_user:lwLOPZcGUqymEKj8@doantotnghiep.ygcj75m.mongodb.net/financial_db");
        console.log("MongoDB Connected");
    } catch (error) {
        console.error(error);
        process.exit(1);
    }
};

module.exports = connectDB;