import React, { useState } from 'react';

const ResultPanel = ({ result, loading, error }) => {
  const [expandedDays, setExpandedDays] = useState({});

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="error">{error}</p>;
  if (!result) return null;

  // Group logs by date
  const logsByDate = {};
  result.logs.forEach(log => {
    const dateStr = log.date.toString();
    if (!logsByDate[dateStr]) {
      logsByDate[dateStr] = [];
    }
    logsByDate[dateStr].push(log);
  });

  const toggleDay = (date) => {
    setExpandedDays(prev => ({
      ...prev,
      [date]: !prev[date]
    }));
  };

  // Determine HOS compliance status
  const hosCompliant = result.hos_compliant !== undefined ? result.hos_compliant : true;
  const hosStatusText = hosCompliant ? '✓ Compliant' : '✗ Non-compliant';
  const hosStatusClass = hosCompliant ? 'compliant' : 'non-compliant';

  return (
    <div className="result">
      <div className="summary-stats">
        <div className="stat-card">
          <h3>Total Distance</h3>
          <p className="stat-value">{result.total_distance ? result.total_distance.toFixed(1) : '0.0'} miles</p>
        </div>
        <div className="stat-card">
          <h3>Total Duration</h3>
          <p className="stat-value">{result.total_duration ? result.total_duration.toFixed(1) : '0.0'} hours</p>
        </div>
        <div className="stat-card">
          <h3>HOS Status</h3>
          <p className={`stat-value ${hosStatusClass}`}>
            {hosStatusText}
          </p>
        </div>
        <div className="stat-card">
          <h3>Days</h3>
          <p className="stat-value">{Object.keys(logsByDate).length}</p>
        </div>
      </div>

      {result.pdf_url && (
        <div className="pdf-download-section">
          <a href={`https://app-production-6389.up.railway.app/media/${result.pdf_url}`} target="_blank" rel="noopener noreferrer" className="pdf-download-button">
            📄 Download Complete PDF Log
          </a>
        </div>
      )}

      <div className="logs-section">
        <h2>Daily Logs Summary</h2>
        {Object.entries(logsByDate).map(([date, logs]) => {
          const totalEntry = logs.find(l => l.status === 'Total');
          const regularLogs = logs.filter(l => l.status !== 'Total');
          const isExpanded = expandedDays[date];

          return (
            <div key={date} className="day-log-card">
              <div className="day-header" onClick={() => toggleDay(date)}>
                <h3>{date}</h3>
                <div className="day-summary">
                  {totalEntry && <span className="total-info">{totalEntry.remarks}</span>}
                  <button className="expand-button">{isExpanded ? '▼ Hide' : '▶ Show'} Details ({regularLogs.length} entries)</button>
                </div>
              </div>
              
              {isExpanded && (
                <div className="day-details">
                  <ul className="log-entries">
                    {regularLogs.map((log, index) => (
                      <li key={index} className={`log-entry ${log.status.toLowerCase().replace(/\s+/g, '-')}`}>
                        <span className="log-time">{log.start_time} - {log.end_time}</span>
                        <span className="log-status">{log.status}</span>
                        <span className="log-remarks">{log.remarks}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="disclaimer">
        <small>⚠️ This is a simulation tool. Always verify with official FMCSA guidelines and consult professionals for real use.</small>
      </p>
    </div>
  );
};

export default ResultPanel;
