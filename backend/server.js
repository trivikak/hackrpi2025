require('dotenv').config(); // MUST be the first line to load .env variables

const express = require('express');
// We no longer need to explicitly require 'body-parser' here!
const cors = require('cors'); 
const { getRequirements, generatePlan } = require('./plannerLogic'); 

const app = express();
const PORT = process.env.API_PORT || 3001; 

// --- Middleware Setup (FIXED: Using built-in Express parser) ---
app.use(cors()); 
// This is the modern, recommended replacement for bodyParser.json()
app.use(express.json()); 

// Basic Test Route
app.get('/', (req, res) => {
    res.send('Course Planning Backend is Operational and Ready to Serve!');
});

// --- CORE FEATURE ENDPOINT: Plan Generation ---
app.post('/api/plan/generate', async (req, res) => {
    // 1. Destructure and validate input
    const { major, minor, concentration, start_year, completed_courses = [] } = req.body;

    if (!major || !start_year) {
        return res.status(400).json({ error: 'Major and start_year are required parameters.' });
    }

    try {
        // --- STEP 1: Data Retrieval ---
        const { requirements, catalog } = await getRequirements(major, minor, concentration);
        
        // --- STEP 2: Run the Scheduling Algorithm ---
        const finalPlan = generatePlan(
            requirements, 
            catalog, 
            completed_courses, 
            parseInt(start_year, 10)
        );

        // --- STEP 3: Send the structured, generated plan back ---
        res.json(finalPlan); 
    
    } catch (error) {
        console.error('API Error during Plan Generation:', error.message);
        
        if (error.message.includes('No programs found')) {
             return res.status(400).json({ error: error.message });
        }
        res.status(500).json({ error: 'Failed to generate course plan due to a server error. Please check database connection or data integrity.' });
    }
});

// Start the server and listen on the defined port
app.listen(PORT, () => {
    console.log(`Server listening securely on port ${PORT}`);
});