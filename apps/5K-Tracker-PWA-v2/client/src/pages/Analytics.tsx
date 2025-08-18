import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const monthlyData = [
  { month: 'Jul', runs: 6, avgPace: 460 },
  { month: 'Aug', runs: 8, avgPace: 455 },
  { month: 'Sep', runs: 7, avgPace: 450 },
  { month: 'Oct', runs: 9, avgPace: 445 },
  { month: 'Nov', runs: 10, avgPace: 442 },
  { month: 'Dec', runs: 12, avgPace: 438 },
  { month: 'Jan', runs: 8, avgPace: 435 },
];

const distanceData = [
  { distance: '5K', count: 15, color: '#8884d8' },
  { distance: '10K', count: 6, color: '#82ca9d' },
  { distance: 'Half Marathon', count: 2, color: '#ffc658' },
  { distance: 'Marathon', count: 1, color: '#ff7300' },
];

const prData = [
  { distance: '5K', time: '22:45', date: '2024-01-05' },
  { distance: '10K', time: '48:30', date: '2024-01-10' },
  { distance: 'Half Marathon', time: '1:42:15', date: '2023-11-15' },
];

export function Analytics() {
  const formatPaceTooltip = (value: number) => {
    const minutes = Math.floor(value / 60);
    const seconds = value % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}/km`;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
        <p className="text-gray-600 dark:text-gray-300">Insights into your running performance</p>
      </div>

      {/* Monthly Runs Chart */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Monthly Runs Count</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="runs" fill="#3B82F6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pace Trend Chart */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Average Pace Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value: number) => [formatPaceTooltip(value), 'Average Pace']} />
            <Legend />
            <Line type="monotone" dataKey="avgPace" stroke="#10B981" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distance Distribution */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Distance Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distanceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ distance, count }) => `${distance}: ${count}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {distanceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Personal Records */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Personal Records</h2>
          <div className="space-y-4">
            {prData.map((pr, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">{pr.distance}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{pr.date}</div>
                </div>
                <div className="text-lg font-semibold text-green-600 dark:text-green-400">{pr.time}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Total PRs:</strong> {prData.length}
            </div>
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Most Recent:</strong> {prData[0].date}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}