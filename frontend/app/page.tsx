import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-6xl font-bold text-primary-600 mb-4">
          Legend Hockey League
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Draft teams of NHL legends and simulate epic 20-25 year seasons
        </p>
        
        <div className="flex gap-4 justify-center mb-12">
          <Link href="/simulation/new" className="btn btn-primary text-lg px-8 py-3">
            Start New Simulation
          </Link>
          <Link href="/login" className="btn btn-secondary text-lg px-8 py-3">
            Login
          </Link>
        </div>
        
        <div className="card text-left max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold mb-4">How It Works</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>Create your simulation and choose league size (4-12 teams)</li>
            <li>Draft your dream team of hockey legends</li>
            <li>Configure your lines and strategy</li>
            <li>Simulate seasons and watch the stats unfold</li>
            <li>Compete for trophies and build a dynasty</li>
          </ol>
        </div>
      </div>
    </main>
  );
}
