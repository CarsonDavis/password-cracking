<script lang="ts">
	import { api } from '$lib/api/client';
	import type { EstimateResponse } from '$lib/api/client';
	import { algorithm, hardwareTier } from '$lib/stores/settings';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import ComparisonTable from '$lib/components/ComparisonTable.svelte';
	import CrackTimeChart from '$lib/components/CrackTimeChart.svelte';

	let passwords = $state(['', '']);
	let results: EstimateResponse[] = $state([]);
	let error = $state('');
	let loading = $state(false);

	function addField() {
		passwords = [...passwords, ''];
	}

	function removeField(i: number) {
		passwords = passwords.filter((_, idx) => idx !== i);
	}

	function updatePassword(i: number, value: string) {
		passwords = passwords.map((p, idx) => (idx === i ? value : p));
	}

	async function compare() {
		const filled = passwords.filter(Boolean);
		if (filled.length < 2) {
			error = 'Enter at least 2 passwords to compare';
			return;
		}
		loading = true;
		error = '';
		try {
			results = await api.comparePasswords(filled, $algorithm, $hardwareTier);
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
		<h1 class="text-2xl font-bold tracking-tight text-heading">Compare Passwords</h1>
		<p class="mt-1 text-sm text-body">See how different passwords stack up side by side.</p>
	</div>

	<div class="space-y-3">
		{#each passwords as pw, i}
			<div class="flex gap-2">
				<div class="flex-1">
					<PasswordInput
						value={pw}
						placeholder="Password {i + 1}"
						oninput={(e: Event) => updatePassword(i, (e.target as HTMLInputElement).value)}
					/>
				</div>
				{#if passwords.length > 2}
					<button onclick={() => removeField(i)} class="text-red-400 transition-colors duration-150 hover:text-red-300">&times;</button>
				{/if}
			</div>
		{/each}
		<button onclick={addField} class="text-sm text-accent transition-colors duration-150 hover:text-accent-hover">+ Add password</button>
	</div>

	<button
		onclick={compare}
		disabled={loading}
		class="w-full rounded-lg border border-accent bg-accent/10 px-4 py-3 font-medium text-accent transition-colors duration-150 hover:bg-accent/20 disabled:opacity-50"
	>
		{loading ? 'Comparing...' : 'Compare'}
	</button>

	{#if error}
		<div class="rounded-lg bg-red-900/20 p-4 text-sm text-red-400">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="card space-y-6 rounded-lg border border-edge bg-panel p-6">
			<CrackTimeChart {results} labelKey="password" />
			<ComparisonTable {results} labelKey="password" />
		</div>
	{/if}
</div>
