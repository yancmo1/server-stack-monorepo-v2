import { Activity, Clock, MapPin, TrendingUp } from 'lucide-react';

export function Dashboard() {
  const stats = [
    { label: 'Total Runs', value: '24', icon: Activity, color: 'bg-blue-500' },
    { label: 'Best 5K Time', value: '22:45', icon: Clock, color: 'bg-green-500' },
    { label: 'This Month', value: '8', icon: TrendingUp, color: 'bg-purple-500' },
    { label: 'Favorite Location', value: 'Central Park', icon: MapPin, color: 'bg-orange-500' },
  ];

  const recentRaces = [
    { date: '2024-01-15', distance: '5K', time: '23:12', location: 'Central Park' },
    { date: '2024-01-10', distance: '10K', time: '48:30', location: 'Brooklyn Bridge' },
    { date: '2024-01-05', distance: '5K', time: '22:45', location: 'Prospect Park' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-300">Welcome back! Here's your running summary.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.label}</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Races */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Races</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {recentRaces.map((race, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400">{race.date}</div>
                  <div className="font-medium text-gray-900 dark:text-white">{race.distance}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{race.location}</div>
                </div>
                <div className="font-semibold text-blue-600 dark:text-blue-400">{race.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}