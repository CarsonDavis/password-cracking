<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import type { EstimateResponse, MetadataResponse } from '$lib/api/client';
	import { hardwareTier } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import ComparisonTable from '$lib/components/ComparisonTable.svelte';
	import CrackTimeChart from '$lib/components/CrackTimeChart.svelte';

	let password = $state('');
	let selectedAlgorithms = $state<string[]>([]);
	let metadata: MetadataResponse | null = $state(null);
	let results: EstimateResponse[] = $state([]);
	let error = $state('');
	let loading = $state(false);

	onMount(async () => {
		try {
			metadata = await api.metadata();
			selectedAlgorithms = metadata.algorithms.map((a) => a.name);
		} catch {
			// ignore
		}
	});

	function toggleAlgo(name: string) {
		if (selectedAlgorithms.includes(name)) {
			selectedAlgorithms = selectedAlgorithms.filter((a) => a !== name);
		} else {
			selectedAlgorithms = [...selectedAlgorithms, name];
		}
	}

	async function compare() {
		if (!password || selectedAlgorithms.length < 2) {
			error = 'Enter a password and select at least 2 algorithms';
			return;
		}
		loading = true;
		error = '';
		try {
			results = await api.compareAlgorithms(password, selectedAlgorithms, $hardwareTier);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Request failed';
			results = [];
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto max-w-3xl space-y-6">
	<div>
		<h1 class="text-2xl font-bold text-gray-900">Hash Algorithm Impact</h1>
		<p class="mt-1 text-sm text-gray-500">
			See how the choice of hash algorithm affects crack time for the same password.
		</p>
	</div>

	<PasswordInput bind:value={password} />

	{#if metadata}
		<div>
			<p class="mb-2 text-sm font-medium text-gray-700">Select algorithms:</p>
			<div class="flex flex-wrap gap-2">
				{#each metadata.algorithms as algo}
					<button
						onclick={() => toggleAlgo(algo.name)}
						class="rounded-full border px-3 py-1 text-xs {selectedAlgorithms.includes(algo.name) ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-500'}"
					>
						{algo.name}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<button
		onclick={compare}
		disabled={loading || !password}
		class="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
	>
		{loading ? 'Comparing...' : 'Compare Algorithms'}
	</button>

	{#if error}
		<div class="rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
			<CrackTimeChart {results} labelKey="hash_algorithm" />
			<ComparisonTable {results} labelKey="hash_algorithm" />
		</div>
	{/if}
</div>
