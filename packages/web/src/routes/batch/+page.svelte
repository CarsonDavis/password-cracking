<script lang="ts">
	import { api } from '$lib/api/client';
	import type { BatchResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import BatchUploader from '$lib/components/BatchUploader.svelte';
	import DistributionChart from '$lib/components/DistributionChart.svelte';
	import RatingBadge from '$lib/components/RatingBadge.svelte';

	let result: BatchResponse | null = $state(null);
	let error = $state('');
	let loading = $state(false);

	const RATING_LABELS: Record<number, string> = {
		0: 'Critical',
		1: 'Weak',
		2: 'Fair',
		3: 'Strong',
		4: 'Very Strong'
	};

	async function handleUpload(passwords: string[]) {
		loading = true;
		error = '';
		try {
			result = await api.batch(passwords, $algorithm, $hardwareTier);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed';
			result = null;
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto max-w-3xl space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">Batch Audit</h1>
		<p class="mt-1 text-sm text-gray-500">
			Evaluate many passwords at once and see the distribution of strength ratings.
		</p>
	</div>

	<BatchUploader onUpload={handleUpload} />

	{#if loading}
		<div class="text-center text-gray-500">Analyzing passwords...</div>
	{/if}

	{#if error}
		<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
	{/if}

	{#if result}
		<div class="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
			<div class="grid grid-cols-2 gap-4">
				<div>
					<p class="text-sm text-gray-500">Total passwords</p>
					<p class="text-2xl font-bold">{result.total_passwords}</p>
				</div>
				<div>
					<p class="text-sm text-gray-500">Median crack time</p>
					<p class="text-2xl font-bold">{result.summary.median_crack_time_seconds.toFixed(1)}s</p>
				</div>
			</div>

			<div>
				<h3 class="mb-2 text-sm font-medium text-gray-700">Rating Distribution</h3>
				<DistributionChart distribution={result.summary.rating_distribution} />
			</div>

			<div>
				<h3 class="mb-2 text-sm font-medium text-gray-700">All Passwords</h3>
				<div class="overflow-x-auto">
					<table class="min-w-full text-sm">
						<thead>
							<tr class="border-b border-gray-200 text-left text-gray-500">
								<th class="py-2 pr-4 font-medium">Password</th>
								<th class="py-2 pr-4 font-medium">Crack Time</th>
								<th class="py-2 pr-4 font-medium">Rating</th>
								<th class="py-2 pr-4 font-medium">Attack</th>
							</tr>
						</thead>
						<tbody>
							{#each result.passwords as pw}
								<tr class="border-b border-gray-100">
									<td class="py-2 pr-4 font-mono text-xs">{pw.password}</td>
									<td class="py-2 pr-4">{pw.crack_time_display}</td>
									<td class="py-2 pr-4"><RatingBadge rating={pw.rating} label={pw.rating_label} /></td>
									<td class="py-2 pr-4 text-xs text-gray-600">{pw.winning_attack}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	{/if}
</div>
