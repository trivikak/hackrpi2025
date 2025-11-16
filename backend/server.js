const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
// Loads environment variables (like PGUSER, PGDATABASE, PORT) from the .env file
require('dotenv').config(); 

const app = express();
// Uses the 'PORT' variable defined in your .env file (default is 3001)
const port = process.env.PORT || 3001; 

// --- Database Connection Pool ---
const pool = new Pool({
    user: process.env.PGUSER,
    host: process.env.PGHOST,
    database: process.env.PGDATABASE,
    password: process.env.PGPASSWORD,
    port: process.env.PGPORT,
});

// Test DB connection on startup to confirm service is running
pool.query('SELECT NOW()', (err, res) => {
    if (err) {
        console.error('❌ Database connection failed. Is the PostgreSQL service running? Error:', err.message);
        process.exit(1); 
    } else {
        console.log('✅ Database connected successfully at:', res.rows[0].now);
    }
});

// Middleware
app.use(cors());
app.use(express.json());

// --- API Endpoints ---

/**
 * Endpoint 1: Fetch all available Programs (Majors/Minors)
 * GET /api/programs
 * Returns: [{ program_id, name, type }, ...]
 */
app.get('/api/programs', async (req, res) => {
    try {
        const result = await pool.query('SELECT program_id, name, type FROM Programs ORDER BY name;');
        res.json(result.rows);
    } catch (err) {
        console.error('Error fetching programs:', err);
        res.status(500).json({ error: 'Failed to fetch program list.' });
    }
});

/**
 * Endpoint 2: Fetch specific Program Requirements by ID
 * GET /api/requirements/:programId
 * Returns: { program: {name, type}, requirements: [...] }
 */
app.get('/api/requirements/:programId', async (req, res) => {
    const { programId } = req.params;
    try {
        const programResult = await pool.query('SELECT name, type FROM Programs WHERE program_id = $1;', [programId]);
        if (programResult.rows.length === 0) {
            return res.status(404).json({ error: 'Program not found.' });
        }
        
        const requirementsQuery = `
            SELECT 
                description, 
                options_pool, 
                -- Aggregates the full course details for every course in the options_pool
                (SELECT json_agg(c) FROM Courses c WHERE c.course_id = ANY(SELECT jsonb_array_elements_text(r.options_pool))) AS full_course_details
            FROM Requirements r 
            WHERE program_id = $1;
        `;
        const requirementsResult = await pool.query(requirementsQuery, [programId]);

        res.json({
            program: programResult.rows[0],
            requirements: requirementsResult.rows
        });
    } catch (err) {
        console.error('Error fetching program requirements:', err);
        res.status(500).json({ error: 'Failed to fetch requirements.' });
    }
});

/**
 * Endpoint 3: Fetch detailed Course information by Course ID
 * GET /api/course/:courseId
 * Returns: { course_id, name, credits, semesters_offered, prerequisites, description }
 */
app.get('/api/course/:courseId', async (req, res) => {
    const { courseId } = req.params;
    try {
        const result = await pool.query('SELECT * FROM Courses WHERE course_id = $1;', [courseId.toUpperCase()]);
        
        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Course not found.' });
        }
        
        res.json(result.rows[0]);
    } catch (err) {
        console.error('Error fetching course details:', err);
        res.status(500).json({ error: 'Failed to fetch course details.' });
    }
});


// Start the server
app.listen(port, () => {
    console.log(`🚀 Server listening on port ${port}`);
});