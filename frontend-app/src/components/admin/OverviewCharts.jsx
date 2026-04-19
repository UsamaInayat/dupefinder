import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from 'recharts'

const gridStroke = 'rgba(45, 55, 72, 0.12)'
const axisColor = '#6b7280'
const tooltipStyle = {
  background: '#ffffff',
  border: '1px solid rgba(45, 55, 72, 0.12)',
  borderRadius: 10,
  boxShadow: '0 8px 24px rgba(15, 23, 42, 0.08)',
}
const tooltipLabel = { color: '#2d3748', fontWeight: 600 }

export default function OverviewCharts({ usageData, dailyData }) {
  return (
    <>
      <div className="section-card" style={{ marginBottom: 20 }}>
        <h3>Usage Breakdown</h3>
        <div style={{ width: '100%', minWidth: 0, height: 320 }}>
          <ResponsiveContainer width="100%" height={320} minWidth={0} debounce={50}>
            <BarChart data={usageData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="name" stroke={axisColor} tick={{ fill: axisColor, fontSize: 12 }} />
              <YAxis stroke={axisColor} tick={{ fill: axisColor, fontSize: 12 }} allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabel} />
              <Legend wrapperStyle={{ color: '#2d3748' }} />
              <Bar dataKey="value" name="Count" fill="#ff71a9" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="section-card">
        <h3>7-Day Community Activity</h3>
        <div style={{ width: '100%', minWidth: 0, height: 320 }}>
          <ResponsiveContainer width="100%" height={320} minWidth={0} debounce={50}>
            <LineChart data={dailyData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
              <XAxis dataKey="day" stroke={axisColor} tick={{ fill: axisColor, fontSize: 12 }} />
              <YAxis stroke={axisColor} tick={{ fill: axisColor, fontSize: 12 }} allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} labelStyle={tooltipLabel} />
              <Legend wrapperStyle={{ color: '#2d3748' }} />
              <Line type="monotone" dataKey="posts" name="Posts" stroke="#5b8def" strokeWidth={3} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="reports" name="Reports" stroke="#3bd6b6" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}
