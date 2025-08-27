import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SearchPage from './SearchPage';
import ResultsPage from './ResultsPage';
import LocationDetailPage from './LocationDetailPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* Navigation Bar */}
        <nav className="navbar">
          <div className="nav-left">
            <button className="hamburger-menu">
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
          <div className="nav-center">
            <h1 className="nav-title">🌲 MommyNature</h1>
          </div>
          <div className="nav-right">
            <button className="nav-button">EXPLORE</button>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/location/:locationName" element={<LocationDetailPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;