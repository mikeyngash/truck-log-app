import React from 'react';

const LogGridSvg = ({ data }) => {
  if (!data || data.length === 0) return null;

  const width = 800;
  const height = 400;
  const leftMargin = 100;  // More space for labels
  const topMargin = 40;
  const rightMargin = 40;
  const bottomMargin = 40;
  const gridWidth = width - leftMargin - rightMargin;
  const gridHeight = height - topMargin - bottomMargin;
  const rowHeight = gridHeight / 4;

  const statusColors = {
    'Off-Duty': '#e74c3c',
    'Sleeper Berth': '#f39c12',
    'Driving': '#27ae60',
    'On-Duty': '#3498db'
  };

  const statusRows = {
    'Off-Duty': 0,
    'Sleeper Berth': 1,
    'Driving': 2,
    'On-Duty': 3
  };

  const logs = data.filter(log => log.status !== 'Total' && log.start_time && log.end_time);

  return (
    <div className="log-grid-svg">
      <h2>Driver Log Grid</h2>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Grid background */}
        <rect x={leftMargin} y={topMargin} width={gridWidth} height={gridHeight} fill="none" stroke="#000" strokeWidth="2" />

        {/* Horizontal lines */}
        {Array.from({ length: 4 }, (_, i) => (
          <line
            key={`h-${i}`}
            x1={leftMargin}
            y1={topMargin + (i + 1) * rowHeight}
            x2={leftMargin + gridWidth}
            y2={topMargin + (i + 1) * rowHeight}
            stroke="#000"
            strokeWidth="1"
          />
        ))}

        {/* Vertical lines (hours) */}
        {Array.from({ length: 25 }, (_, i) => (
          <line
            key={`v-${i}`}
            x1={leftMargin + (i * gridWidth) / 24}
            y1={topMargin}
            x2={leftMargin + (i * gridWidth) / 24}
            y2={topMargin + gridHeight}
            stroke="#000"
            strokeWidth="1"
          />
        ))}

        {/* Quarter hour ticks */}
        {Array.from({ length: 24 }, (_, h) =>
          Array.from({ length: 4 }, (_, q) => (
            <line
              key={`q-${h}-${q}`}
              x1={leftMargin + (h * gridWidth) / 24 + ((q + 1) * gridWidth) / 96}
              y1={topMargin}
              x2={leftMargin + (h * gridWidth) / 24 + ((q + 1) * gridWidth) / 96}
              y2={topMargin + gridHeight}
              stroke="#ccc"
              strokeWidth="0.5"
            />
          ))
        )}

        {/* Status labels */}
        {Object.entries(statusRows).map(([status, row]) => (
          <text
            key={`label-${status}`}
            x={leftMargin - 10}
            y={topMargin + row * rowHeight + rowHeight / 2}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize="12"
            fontWeight="bold"
          >
            {status}
          </text>
        ))}

        {/* Hour labels */}
        {Array.from({ length: 25 }, (_, i) => {
          const hour = i % 24;
          const label = hour === 0 ? 'Mid' : hour === 12 ? 'Noon' : hour > 12 ? `${hour - 12}` : `${hour}`;
          return (
            <text
              key={`hour-${i}`}
              x={leftMargin + (i * gridWidth) / 24}
              y={topMargin - 5}
              textAnchor="middle"
              fontSize="10"
            >
              {label}
            </text>
          );
        })}

        {/* Log entries */}
        {logs.map((log, index) => {
          const status = log.status;
          const row = statusRows[status];
          if (row === undefined || !log.start_time || !log.end_time) return null;

          // Parse time strings (e.g., "06:00:00")
          const parseTime = (timeStr) => {
            const [hours, minutes] = timeStr.split(':').map(Number);
            return { hours, minutes };
          };

          const start = parseTime(log.start_time);
          const end = parseTime(log.end_time);

          const startSlot = start.hours * 4 + Math.floor(start.minutes / 15);
          const endSlot = end.hours * 4 + Math.floor(end.minutes / 15);

          const x = leftMargin + (startSlot * gridWidth) / 96;
          const y = topMargin + row * rowHeight;
          const width = ((endSlot - startSlot) * gridWidth) / 96;
          const height = rowHeight;

          return (
            <rect
              key={`log-${index}`}
              x={x}
              y={y}
              width={width}
              height={height}
              fill={statusColors[status] || '#000'}
              opacity="0.7"
            />
          );
        })}
      </svg>
    </div>
  );
};

export default LogGridSvg;
