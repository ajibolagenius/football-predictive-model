require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const axios = require('axios');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Database Connection (Same Supabase DB)
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

// Python API URL (Local or Cloud)
const BRAIN_URL = process.env.BRAIN_URL || "http://localhost:8000";

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static('public'));

app.get('/', async (req, res) => {
    try {
        // Fetch matches directly from DB
        const result = await pool.query(`
            SELECT m.match_id, m.date, t1.name as home, t2.name as away 
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.team_id
            JOIN teams t2 ON m.away_team_id = t2.team_id
            WHERE m.date >= CURRENT_DATE
            ORDER BY m.date ASC LIMIT 10
        `);
        res.render('index', { matches: result.rows });
    } catch (err) {
        res.status(500).send("Database Error");
    }
});

// The Hybrid Bridge
app.get('/api/predict/:id', async (req, res) => {
    try {
        // Node asks Python for the math
        const response = await axios.post(`${BRAIN_URL}/predict`, { match_id: req.params.id });
        res.json(response.data);
    } catch (err) {
        res.status(500).json({ error: "Brain Offline" });
    }
});

app.listen(port, () => console.log(`🌍 Face running on port ${port}`));