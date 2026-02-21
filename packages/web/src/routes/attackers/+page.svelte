<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import type { EstimateResponse, MetadataResponse } from '$lib/api/client';
	import { algorithm } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import ComparisonTable from '$lib/components/ComparisonTable.svelte';
	import CrackTimeChart from '$lib/components/CrackTimeChart.svelte';

	let password = $state('');
	let selectedTiers = $state<string[]>([]);
	let metadata: MetadataResponse | null = $state(null);
	let results: EstimateResponse[] = $state([]);
	let error = $state('');
	let loading = $state(false);

	onMount(async () => {
		try {
			metadata = await api.metadata();
			selectedTiers = metadata.hardware_tiers.map((t) => t.name);
		} catch {
			// ignore
		}
	});

	function toggleTier(name: string) {
		if (selectedTiers.includes(name)) {
			selectedTiers = selectedTiers.filter((t) => t !== name);
		} else {
			selectedTiers = [...selectedTiers, name];
		}
	}

	async function compare() {
		if (!password || selectedTiers.length < 2) {
			error = 'Enter a password and select at least 2 tiers';
			return;
		}
		loading = true;
		error = '';
		try {
			results = await api.compareAttackers(password, $algorithm, selectedTiers);
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
		<h1 class="text-2xl font-bold tracking-tight text-heading">Attacker Profiles</h1>
		<p class="mt-1 text-sm text-body">
			Compare crack times across different attacker hardware capabilities.
		</p>
	</div>

	<PasswordInput bind:value={password} />

	{#if metadata}
		<div>
			<p class="mb-2 text-sm font-medium text-body">Select attacker profiles:</p>
			<div class="flex flex-wrap gap-2">
				{#each metadata.hardware_tiers as tier}
					<button
						onclick={() => toggleTier(tier.name)}
						class="rounded-full border px-3 py-1 text-xs transition-colors duration-150 {selectedTiers.includes(tier.name) ? 'border-accent bg-accent/10 text-accent' : 'border-edge text-body hover:border-accent hover:text-accent'}"
					>
						{tier.name} ({tier.description})
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<button
		onclick={compare}
		disabled={loading || !password}
		class="w-full rounded-lg border border-accent bg-accent/10 px-4 py-3 font-medium text-accent transition-colors duration-150 hover:bg-accent/20 disabled:opacity-50"
	>
		{loading ? 'Comparing...' : 'Compare Attackers'}
	</button>

	{#if error}
		<div class="rounded-lg bg-red-900/20 p-4 text-sm text-red-400">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="card space-y-6 rounded-lg border border-edge bg-panel p-6">
			<CrackTimeChart {results} labelKey="hardware_tier" />
			<ComparisonTable {results} labelKey="hardware_tier" />
		</div>
	{/if}
</div>
