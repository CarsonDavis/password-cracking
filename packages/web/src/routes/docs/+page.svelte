<script lang="ts">
	const endpoints = [
		{
			method: 'POST',
			path: '/api/estimate',
			description: 'Evaluate a single password',
			body: '{ "password": "...", "algorithm": "bcrypt_cost12", "hardware_tier": "consumer" }'
		},
		{
			method: 'POST',
			path: '/api/batch',
			description: 'Evaluate multiple passwords at once',
			body: '{ "passwords": ["..."], "algorithm": "bcrypt_cost12", "hardware_tier": "consumer" }'
		},
		{
			method: 'POST',
			path: '/api/compare/passwords',
			description: 'Compare multiple passwords side by side',
			body: '{ "passwords": ["pw1", "pw2"], "algorithm": "bcrypt_cost12", "hardware_tier": "consumer" }'
		},
		{
			method: 'POST',
			path: '/api/compare/algorithms',
			description: 'Compare one password across different hash algorithms',
			body: '{ "password": "...", "algorithms": ["md5", "bcrypt_cost12"], "hardware_tier": "consumer" }'
		},
		{
			method: 'POST',
			path: '/api/compare/attackers',
			description: 'Compare one password across different hardware tiers',
			body: '{ "password": "...", "algorithm": "bcrypt_cost12", "hardware_tiers": ["consumer", "nation_state"] }'
		},
		{
			method: 'GET',
			path: '/api/metadata',
			description: 'Get available algorithms and hardware tiers',
			body: null
		},
		{
			method: 'POST',
			path: '/api/targeted',
			description: 'Evaluate with personal context for targeted attack simulation',
			body: '{ "password": "...", "algorithm": "bcrypt_cost12", "hardware_tier": "consumer", "context": ["name", "date"] }'
		}
	];
</script>

<div class="mx-auto max-w-3xl space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">API Reference</h1>
		<p class="mt-1 text-sm text-gray-500">
			The FastAPI server provides a REST API for password crack-time estimation.
			Full interactive docs are available at
			<a href="http://localhost:8000/docs" target="_blank" class="text-blue-600 hover:underline">
				localhost:8000/docs
			</a> (Swagger UI).
		</p>
	</div>

	<div class="space-y-4">
		{#each endpoints as ep}
			<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
				<div class="flex items-center gap-3">
					<span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">{ep.method}</span>
					<code class="text-sm font-medium">{ep.path}</code>
				</div>
				<p class="mt-2 text-sm text-gray-600">{ep.description}</p>
				{#if ep.body}
					<pre class="mt-2 overflow-x-auto rounded bg-gray-50 p-3 text-xs text-gray-700">{ep.body}</pre>
				{/if}
			</div>
		{/each}
	</div>
</div>
