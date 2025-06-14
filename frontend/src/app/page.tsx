'use client';
import React, { useState } from 'react';

export default function Home() {
  const [title, setTitle] = useState('');
  const [experience, setExperience] = useState('');
  const [location, setLocation] = useState('');
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(true);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setJobs([]);
    try {
      const res = await fetch('http://localhost:8000/scrape_and_save_jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          experience: experience ? parseInt(experience) : undefined,
          location,
          use_semantic_search: true,
        }),
      });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      setError('Failed to fetch jobs.');
    }
    setLoading(false);
  };

  return (
    <div className={
      `${darkMode ? 'dark' : ''} min-h-screen transition-colors duration-300 bg-gray-100 dark:bg-gray-900`
    }>
      <div className="max-w-2xl mx-auto pt-10 font-sans px-2">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Job Search</h1>
          <button
            onClick={() => setDarkMode((d) => !d)}
            className="rounded px-3 py-1 border border-gray-400 dark:border-gray-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition"
            aria-label="Toggle dark mode"
          >
            {darkMode ? '🌙' : '☀️'}
          </button>
        </div>
        <form onSubmit={handleSearch} className="mb-8 flex flex-wrap gap-2 bg-white dark:bg-gray-800 p-4 rounded shadow">
          <input
            type="text"
            placeholder="Job Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <input
            type="number"
            placeholder="Experience (years)"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            min={0}
            className="border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 rounded w-36 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <input
            type="text"
            placeholder="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-2 py-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700 disabled:opacity-60 transition"
          >
            {loading ? 'Searching...' : 'Search Jobs'}
          </button>
        </form>
        {error && <div className="text-red-600 mb-4">{error}</div>}
        <div>
          {jobs.length > 0 && <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">Results</h2>}
          {jobs.map((job, idx) => (
            <div
              key={idx}
              className="border border-gray-300 dark:border-gray-700 rounded p-4 mb-4 bg-white dark:bg-gray-800 shadow-sm transition-colors"
            >
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                {job.title}{' '}
                <span className="font-normal text-gray-600 dark:text-gray-300">@ {job.company}</span>
              </h3>
              <div className="text-gray-800 dark:text-gray-200">
                <b>Location:</b> {job.location || 'N/A'}
              </div>
              <div className="text-gray-800 dark:text-gray-200">
                <b>Skills:</b>{' '}
                {job.skills && job.skills.length ? job.skills.join(', ') : 'N/A'}
              </div>
              <div className="text-gray-800 dark:text-gray-200">
                <b>Description:</b>{' '}
                {job.description
                  ? job.description.slice(0, 200) +
                    (job.description.length > 200 ? '...' : '')
                  : 'N/A'}
              </div>
              <div>
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-700 dark:text-blue-400 underline"
                >
                  View Job
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}